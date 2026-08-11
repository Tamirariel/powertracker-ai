import pandas as pd
from sklearn.metrics import silhouette_score
import pickle
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
path = os.path.join(BASE_DIR, 'AGENT_data')


df = pd.read_csv(path + r'\cleaned_openpowerlifting.csv', low_memory=False)



def analayze_classafication_model(data,lift_column,sex):
 if lift_column == 'TotalKg':
    data = data[data['Event'] == 'SBD']
 df_new = data[data[lift_column].notna()]
 
 #בדיקה של רק מי שיש לו גיל
 df_new = df_new[df_new['Age'].notna()]


 #יצירת טבלה ממספרת כמה פעמים מופיע מתחרה 
 competitions_per_athlete = df_new['Name'].value_counts()

 #טבלה רק מע ל5
 athletes_5plus = competitions_per_athlete[competitions_per_athlete > 4]

 #מחיקת אנשים שלא מעל ל5 בטהלה 
 df_new= df_new[df_new['Name'].isin(athletes_5plus.index)]

 #המרת המחרוזת לתאריף
 df_new['Date']=pd.to_datetime(df_new['Date'])


  #חישוב תאריך ראשון לכל מתאמן 
 first_competition_date = df_new.groupby('Name')['Date'].transform('min')

 #צירוף טבלאות
 df_new['first_date']=first_competition_date

 #הוספת עמודה חדשה - כמה זמן עבר  בחודשים מתאריך ראשון עד התאריך של השורה 

 df_new['months_since_first'] = (df_new['Date'] - df_new['first_date']).dt.days / 30.44

 #מציאת שיפוע(קצב התקדמות )של מתאמן 
 def analayze_linearRegression(table_group):
     y = table_group[lift_column]
     x = table_group['months_since_first']
     x= x.values.reshape(-1, 1)
     model = LinearRegression()
     model.fit(x, y)
     return model.coef_[0]


 #הרצת המודל על הטבלה
 df_new_linear = df_new.groupby('Name').apply(analayze_linearRegression)


 #סינון הטבלה שיהיה לי רק מתאמנים ותאריך התחלה 
 df_new=df_new[df_new['first_date']==df_new['Date']]




 #מערך הישפועים להעביר לטבלה
 df_new_linear = df_new_linear.reset_index()
 df_new_linear.columns = ['Name', 'slope']

 #מיזוג הטבלאות
 df_new = df_new.merge(df_new_linear, on='Name')

 #מחיקת שורות תמשקל נאל
 df_new = df_new[df_new['BodyweightKg'].notna()]

 #פיצול עמודת המין למספר עמודות בינאריות לכל מין
 is_sex = df_new['Sex'].str.get_dummies()
 df_new = pd.concat([df_new, is_sex], axis=1)
 df_new.drop(columns=['Sex'], inplace=True)


 #מחיקת עמודות המגדר וסינון רק למגדר הנבחר 
 df_new = df_new[df_new[sex]==1]
 


 #חלוקת המתאמנים לשלוש לפי קצב תקדמות
 df_new['slope_category'] = pd.qcut(df_new['slope'], q=3, labels=[0, 1, 2])

 #השמת משתנים 
 x = df_new[['Age', 'BodyweightKg', lift_column]]
 y = df_new['slope_category']


 #הרצת מודל על המשתנים 
 X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

 # max_depth=12 - נבחר לפי ניסוי דיוק מול גודל (ראה max_depth_results/)
 # 15 ומעלה: 232MB+ לפני דחיסה, חורג מיעד הריפו.
 # 8: חוסך פי 5 בנפח אך עולה 3.5 נק' דיוק - כרבע מהסיגנל מעל בייסליין 33%.
 # 12: 24MB אחרי gzip, שומר על רוב הדיוק.
 model = RandomForestClassifier(max_depth=12, random_state=42)
 model.fit(X_train, y_train)

 
 y_pred = model.predict(X_test)
 report=(classification_report(y_test, y_pred, target_names=['איטי', 'בינוני', 'מהיר']))
 return model,report,df_new 



configurations = [
    #     
    {'key': 'squat_m',   'lift_column': 'Best3SquatKg',    'sex': 'M'},
    {'key': 'squat_f',   'lift_column': 'Best3SquatKg',    'sex': 'F'},
 
    #     
    {'key': 'bench_m',   'lift_column': 'Best3BenchKg',    'sex': 'M'},
    {'key': 'bench_f',   'lift_column': 'Best3BenchKg',    'sex': 'F'},
 
    #     
    {'key': 'deadlift_m',   'lift_column': 'Best3DeadliftKg',    'sex': 'M'},
    {'key': 'deadlift_f',   'lift_column': 'Best3DeadliftKg',    'sex': 'F'},
 
    #     
    {'key': 'total_m',   'lift_column': 'TotalKg',    'sex': 'M'},
    {'key': 'total_f',   'lift_column': 'TotalKg',    'sex': 'F'},
]
all_models = {}
 
for config in configurations:
    print(f"בונה מודל: {config['key']}")
    model, report, table = analayze_classafication_model(
        df,
        config['lift_column'],
        config['sex']
        
    )
    all_models[config['key']]= {
        'model': model,
        'report': report,
        'table': table,
        'lift_column': config['lift_column'],
        'sex': config['sex']
        
    }
print("\nכל 8 המודלים נבנו בהצלחה!")
print("מפתחות זמינים ב-all_models:")
for key in all_models:
    print(f"\n--- {key} ---")
    print(all_models[key]['report'])



models_only = {key: all_models[key]['model'] for key in all_models}


#יצירת קובץ עם רשימת המודלים
with open(os.path.join(SCRIPT_DIR, 'classification_model_list.pkl'), 'wb') as f:
    pickle.dump(models_only, f)
 

 
