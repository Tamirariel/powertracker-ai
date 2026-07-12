import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import pickle
import os

#התיקייה שבה הסקריפט הזה יושב (cluster_model)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

#טיפוס רמה אחת למעלה אל myapp ומשם אל הדאטה
BASE_DIR = os.path.dirname(SCRIPT_DIR)
path = os.path.join(BASE_DIR, 'AGENT_data')


df = pd.read_csv(path + r'\cleaned_openpowerlifting.csv', low_memory=False)



def analayze_clustering_model(df,lift_column,sex,k):
 scaler = StandardScaler()
 #סינון טבלה רק לפי עמודות הרלוונטיות לסקוואט עם גיל, משקל גוף ומין
 df_new = df[['Age', lift_column, 'BodyweightKg', 'Sex']]


 df_new = df_new[df_new['Age'].notna()]
  
 df_new= df_new[df_new[lift_column].notna()]
 
 
 #הסרת שורות מתאמנים בלי משקל גוף
 df_new=df_new[df_new['BodyweightKg'].notna()]


 #פיצול עמודת מגדר
 is_sex=df_new['Sex'].str.get_dummies()
 df_new = pd.concat([df_new, is_sex], axis=1)
 df_new.drop(columns=['Sex'], inplace=True)
 

 #מחיקת עמודות המגדר 
 df_new = df_new[df_new[sex]==1]
 df_new.drop('M', axis=1, inplace=True)
 df_new.drop('F',axis =1 , inplace=True)



  #סטנדרזציה של העמודות
 df_new[['Age', 'BodyweightKg', lift_column]] = scaler.fit_transform(df_new[['Age', 'BodyweightKg', lift_column]])
 
 
 model = KMeans(n_clusters=k, random_state=42)
 df_new['cluster'] = model.fit_predict(df_new)

 

 original_values = scaler.inverse_transform(df_new[['Age', 'BodyweightKg', lift_column]])
 df_new[['Age_real', 'BodyweightKg_real',f'{lift_column}_real' ]] = original_values
 
 return model,scaler,df_new 



configurations = [
    # סקוואט k=3
    {'key': 'squat_m_age',     'lift_column': 'Best3SquatKg',    'sex': 'M', 'k': 3},
    {'key': 'squat_f_age',     'lift_column': 'Best3SquatKg',    'sex': 'F', 'k': 3},
   
 
    # בנץ  k=3
    {'key': 'bench_m_age',     'lift_column': 'Best3BenchKg',    'sex': 'M', 'k': 3},
    {'key': 'bench_f_age',     'lift_column': 'Best3BenchKg',    'sex': 'F', 'k': 3},
   
 
    # דדליפט  k=3
    {'key': 'deadlift_m_age',    'lift_column': 'Best3DeadliftKg', 'sex': 'M', 'k': 3},
    {'key': 'deadlift_f_age',    'lift_column': 'Best3DeadliftKg', 'sex': 'F', 'k': 3},
  
 
    # TotalKg - ה-k שונה בכל קומבינציה 
    {'key': 'total_m_age',    'lift_column': 'TotalKg', 'sex': 'M', 'k': 6},
    {'key': 'total_f_age',    'lift_column': 'TotalKg', 'sex': 'F', 'k': 4},
 ]
 
all_models = {}
 
for config in configurations:
    print(f"בונה מודל: {config['key']} (k={config['k']})")
    model, scaler, table = analayze_clustering_model(
        df,
        config['lift_column'],
        config['sex'],
        config['k']
    )
    all_models[config['key']] = {
        'model': model,
        'scaler': scaler,
        'table': table,
        'lift_column': config['lift_column'],
        'sex': config['sex'],
        'k': config['k'],
    }
 


print("\nכל 8 המודלים נבנו בהצלחה!")
print("מפתחות זמינים ב-all_models:")
for key in all_models:
    print(f"  - {key}")



with open(os.path.join(SCRIPT_DIR, 'cluster_model_list.pkl'), 'wb') as f:
    pickle.dump(all_models, f)
 