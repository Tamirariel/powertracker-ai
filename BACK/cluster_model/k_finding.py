#קובץ מציאת K הכי רלוונטי לכל קבוצה 


import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import os

#התיקייה שבה הסקריפט הזה יושב (cluster_model)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

#טיפוס רמה אחת למעלה אל myapp ומשם אל הדאטה
BASE_DIR = os.path.dirname(SCRIPT_DIR)
path = os.path.join(BASE_DIR, 'AGENT_data')

#הפלט נשמר באותה תיקייה כמו הסקריפט
output_path = SCRIPT_DIR


df = pd.read_csv(path + r'\cleaned_openpowerlifting.csv', low_memory=False)


#המרה לעברית לכותרות
lift_heb = {
 'Best3SquatKg': 'סקוואט',
 'Best3BenchKg': 'בנץ',
 'Best3DeadliftKg': 'דדליפט',
 'TotalKg': 'טוטאל'
 }


def check_k_for_model(df,lift_column,sex,include_age):
 scaler = StandardScaler()
 if lift_column == 'TotalKg':
    df = df[df['Event'] == 'SBD']

 #סינון טבלה רק לפי עמודות הרלוונטיות עם גיל, משקל גוף ומין
 df_new = df[['Age', 'BodyweightKg', lift_column, 'Sex']]


 #בדיקת כולל גיל או לא
 if(include_age==1):
      df_new = df_new[df_new['Age'].notna()]

      df_new= df_new[df_new[lift_column].notna()]
 else:
     df_new.drop('Age', axis=1, inplace=True)
     df_new = df_new[df_new[lift_column].notna()]

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
 if(include_age==1):
     df_new[['Age', 'BodyweightKg', lift_column]] = scaler.fit_transform(df_new[['Age', 'BodyweightKg', lift_column]])
 else:
     df_new[[ 'BodyweightKg', lift_column]] = scaler.fit_transform(df_new[[ 'BodyweightKg', lift_column]])


 #בדיקת ציון בדיקת סילואט לכל מספר קבוצות . בדיוק כמו הבדיקה המקורית - מדגם של 15000
 silhouette_scores = []
 inertia_scores = []
 for k in range(2,7):
     kmeans = KMeans(n_clusters=k, random_state=42)
     kmeans.fit(df_new)
     silhouette_scores.append(silhouette_score(df_new, kmeans.labels_, sample_size=15000, random_state=42))
     inertia_scores.append(kmeans.inertia_)

 return silhouette_scores,inertia_scores,len(df_new)



configurations = [
    # סקוואט
    {'key': 'squat_m_age',     'lift_column': 'Best3SquatKg',    'sex': 'M', 'include_age': 1},
    {'key': 'squat_f_age',     'lift_column': 'Best3SquatKg',    'sex': 'F', 'include_age': 1},
    {'key': 'squat_m_no_age',  'lift_column': 'Best3SquatKg',    'sex': 'M', 'include_age': 0},
    {'key': 'squat_f_no_age',  'lift_column': 'Best3SquatKg',    'sex': 'F', 'include_age': 0},

    # בנץ
    {'key': 'bench_m_age',     'lift_column': 'Best3BenchKg',    'sex': 'M', 'include_age': 1},
    {'key': 'bench_f_age',     'lift_column': 'Best3BenchKg',    'sex': 'F', 'include_age': 1},
    {'key': 'bench_m_no_age',  'lift_column': 'Best3BenchKg',    'sex': 'M', 'include_age': 0},
    {'key': 'bench_f_no_age',  'lift_column': 'Best3BenchKg',    'sex': 'F', 'include_age': 0},

    # דדליפט
    {'key': 'deadlift_m_age',    'lift_column': 'Best3DeadliftKg', 'sex': 'M', 'include_age': 1},
    {'key': 'deadlift_f_age',    'lift_column': 'Best3DeadliftKg', 'sex': 'F', 'include_age': 1},
    {'key': 'deadlift_m_no_age', 'lift_column': 'Best3DeadliftKg', 'sex': 'M', 'include_age': 0},
    {'key': 'deadlift_f_no_age', 'lift_column': 'Best3DeadliftKg', 'sex': 'F', 'include_age': 0},

    # TotalKg
    {'key': 'total_m_age',    'lift_column': 'TotalKg', 'sex': 'M', 'include_age': 1},
    {'key': 'total_f_age',    'lift_column': 'TotalKg', 'sex': 'F', 'include_age': 1},
    {'key': 'total_m_no_age', 'lift_column': 'TotalKg', 'sex': 'M', 'include_age': 0},
    {'key': 'total_f_no_age', 'lift_column': 'TotalKg', 'sex': 'F', 'include_age': 0},
]


#רשימת שורות שיכתבו לקובץ הטקסט בסוף
report_lines = []
report_lines.append("דוח בחירת k למודלי הקלאסטרינג")
report_lines.append("silhouette חושב על מדגם של 15000 עם random_state=42 - בדיוק כמו הבדיקה המקורית")
report_lines.append("="*60)

#רשימה לטבלת סיכום בסוף
summary = []

for config in configurations:
    print(f"בודק מודל: {config['key']}")

    silhouette_scores, inertia_scores, n = check_k_for_model(
        df,
        config['lift_column'],
        config['sex'],
        config['include_age']
    )

    #בדיקת מין וגיל לכותרת בעברית
    sex_heb = 'גברים' if config['sex'] == 'M' else 'נשים'
    age_heb = 'עם גיל' if config['include_age'] == 1 else 'ללא גיל'

    #מציאת הk עם הציון הכי גבוה
    best_k = range(2,7)[silhouette_scores.index(max(silhouette_scores))]

    #הדפסת התוצאות למסך
    for k, score in zip(range(2,7), silhouette_scores):
        print(f"k={k}: silhouette={score:.4f}")
    print(f"k הכי טוב: {best_k}")

    #כתיבת התוצאות לדוח
    report_lines.append("")
    report_lines.append(f"מודל: {config['key']} ({lift_heb[config['lift_column']]} | {sex_heb} | {age_heb})")
    report_lines.append(f"מספר שורות: {n}")
    for k, score in zip(range(2,7), silhouette_scores):
        if k == best_k:
            report_lines.append(f"k={k}: silhouette={score:.4f}  <-- הכי טוב")
        else:
            report_lines.append(f"k={k}: silhouette={score:.4f}")

    #שמירה לטבלת הסיכום
    summary.append({'key': config['key'], 'best_k': best_k, 'score': max(silhouette_scores)})

    #יצירת גרף - מרפק וסילואט אחד ליד השני
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    #גרף מרפק
    axes[0].plot(range(2,7), inertia_scores, marker='o')
    axes[0].set_xlabel('k')
    axes[0].set_ylabel('Inertia')
    axes[0].set_title(f"Elbow - {config['key']}")
    axes[0].grid(True)

    #גרף סילואט עם סימון של הk הכי טוב
    axes[1].plot(range(2,7), silhouette_scores, marker='o', color='green')
    axes[1].axvline(best_k, color='red', linestyle='--', label=f'best k={best_k}')
    axes[1].set_xlabel('k')
    axes[1].set_ylabel('Silhouette Score')
    axes[1].set_title(f"Silhouette - {config['key']}")
    axes[1].legend()
    axes[1].grid(True)

    fig.tight_layout()
    fig.savefig(output_path + f"\\{config['key']}.png")
    plt.close(fig)


#טבלת סיכום בסוף הדוח
report_lines.append("")
report_lines.append("="*60)
report_lines.append("סיכום - k מומלץ לכל מודל:")
for row in summary:
    report_lines.append(f"{row['key']}: k={row['best_k']} (silhouette={row['score']:.4f})")


#כתיבת הדוח לקובץ טקסט
with open(output_path + r'\k_selection_results.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(report_lines))

print("\nכל 16 הבדיקות הסתיימו בהצלחה!")
print(f"הדוח נשמר בתיקייה: {output_path}")