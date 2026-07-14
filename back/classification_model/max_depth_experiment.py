import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import pickle
import os

#התיקייה שבה הסקריפט הזה יושב (classification_model)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

#טיפוס רמה אחת למעלה אל BACK ומשם אל הדאטה
BASE_DIR = os.path.dirname(SCRIPT_DIR)
path = os.path.join(BASE_DIR, 'AGENT_data')

#תיקייה לשמירת התוצאות והגרפים
output_path = os.path.join(SCRIPT_DIR, 'max_depth_results')
os.makedirs(output_path, exist_ok=True)


df = pd.read_csv(os.path.join(path, 'cleaned_openpowerlifting.csv'), low_memory=False)


#ערכי max_depth שנבדוק . None = בלי הגבלה בכלל (המצב המקורי)
DEPTH_VALUES = [3, 5, 8, 12, 15, None]

#ה-baseline של ניחוש הקטגוריה השכיחה . qcut לשלושה שווים = 33.3%
BASELINE = 1 / 3


#הכנת הדאטה לתרגיל מסוים . זהה לפונקציה המקורית ב-classification_model.py
def prepare_data(data, lift_column, sex):
 df_new = data[data[lift_column].notna()]
 df_new = df_new[df_new['Age'].notna()]

 #רק מתאמנים עם 5 תחרויות ומעלה
 competitions_per_athlete = df_new['Name'].value_counts()
 athletes_5plus = competitions_per_athlete[competitions_per_athlete > 4]
 df_new = df_new[df_new['Name'].isin(athletes_5plus.index)]

 #חישוב חודשים מהתחרות הראשונה
 df_new['Date'] = pd.to_datetime(df_new['Date'])
 first_competition_date = df_new.groupby('Name')['Date'].transform('min')
 df_new['first_date'] = first_competition_date
 df_new['months_since_first'] = (df_new['Date'] - df_new['first_date']).dt.days / 30.44

 #שיפוע התקדמות לכל מתאמן
 def analayze_linearRegression(table_group):
     from sklearn.linear_model import LinearRegression
     y = table_group[lift_column]
     x = table_group['months_since_first']
     x = x.values.reshape(-1, 1)
     model = LinearRegression()
     model.fit(x, y)
     return model.coef_[0]

 df_new_linear = df_new.groupby('Name').apply(analayze_linearRegression)

 #סינון לשורת התחרות הראשונה בלבד
 df_new = df_new[df_new['first_date'] == df_new['Date']]

 df_new_linear = df_new_linear.reset_index()
 df_new_linear.columns = ['Name', 'slope']
 df_new = df_new.merge(df_new_linear, on='Name')

 df_new = df_new[df_new['BodyweightKg'].notna()]

 is_sex = df_new['Sex'].str.get_dummies()
 df_new = pd.concat([df_new, is_sex], axis=1)
 df_new.drop(columns=['Sex'], inplace=True)
 df_new = df_new[df_new[sex] == 1]

 #חלוקה לשלוש קטגוריות קצב
 df_new['slope_category'] = pd.qcut(df_new['slope'], q=3, labels=[0, 1, 2])

 x = df_new[['Age', 'BodyweightKg', lift_column]]
 y = df_new['slope_category']

 X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
 return X_train, X_test, y_train, y_test


#הרצת הניסוי לצירוף אחד . מאמן מודל לכל max_depth ומודד דיוק וגודל קובץ
def run_experiment_for_lift(X_train, X_test, y_train, y_test):
 results = []
 for depth in DEPTH_VALUES:
     model = RandomForestClassifier(max_depth=depth, random_state=42)
     model.fit(X_train, y_train)

     y_pred = model.predict(X_test)
     acc = accuracy_score(y_test, y_pred)

     #גודל המודל בזיכרון כשהוא ארוז . זה בדיוק מה ששוקל בתוך קובץ הpkl
     size_bytes = len(pickle.dumps(model))
     size_kb = size_bytes / 1024

     results.append({'depth': depth, 'accuracy': acc, 'size_kb': size_kb})

 return results


configurations = [
    {'key': 'squat_m', 'lift_column': 'Best3SquatKg', 'sex': 'M'},
    {'key': 'squat_f', 'lift_column': 'Best3SquatKg', 'sex': 'F'},
    {'key': 'bench_m', 'lift_column': 'Best3BenchKg', 'sex': 'M'},
    {'key': 'bench_f', 'lift_column': 'Best3BenchKg', 'sex': 'F'},
    {'key': 'deadlift_m', 'lift_column': 'Best3DeadliftKg', 'sex': 'M'},
    {'key': 'deadlift_f', 'lift_column': 'Best3DeadliftKg', 'sex': 'F'},
    {'key': 'total_m', 'lift_column': 'TotalKg', 'sex': 'M'},
    {'key': 'total_f', 'lift_column': 'TotalKg', 'sex': 'F'},
]


#תוצאות כל המודלים . מבנה : all_results['squat_m'] = [{'depth':.., 'accuracy':.., 'size_kb':..}, ...]
all_results = {}

for config in configurations:
    print(f"בודק מודל: {config['key']}")

    X_train, X_test, y_train, y_test = prepare_data(df, config['lift_column'], config['sex'])
    results = run_experiment_for_lift(X_train, X_test, y_train, y_test)
    all_results[config['key']] = results

    for r in results:
        depth_label = r['depth'] if r['depth'] is not None else 'ללא הגבלה'
        print(f"  depth={depth_label}: accuracy={r['accuracy']*100:.1f}% | גודל={r['size_kb']:.0f}KB")


#כתיבת דוח טקסט מסודר לכל המודלים
report_lines = []
report_lines.append("דוח ניסוי כיווץ מודלים - max_depth")
report_lines.append(f"baseline (ניחוש הקטגוריה השכיחה) = {BASELINE*100:.1f}%")
report_lines.append("=" * 60)

for key, results in all_results.items():
    report_lines.append("")
    report_lines.append(f"מודל: {key}")
    report_lines.append(f"{'max_depth':<12}{'accuracy':<12}{'גודל (KB)':<12}")
    report_lines.append("-" * 36)
    for r in results:
        depth_label = str(r['depth']) if r['depth'] is not None else 'ללא הגבלה'
        report_lines.append(f"{depth_label:<12}{r['accuracy']*100:.1f}%{'':<7}{r['size_kb']:.0f}")

#סיכום כולל . סכום הגדלים לכל ערך max_depth על פני כל 8 המודלים , וממוצע הדיוק
report_lines.append("")
report_lines.append("=" * 60)
report_lines.append("סיכום כולל על פני כל 8 המודלים:")
report_lines.append(f"{'max_depth':<12}{'ממוצע דיוק':<14}{'סכום גודל (KB)':<16}")
report_lines.append("-" * 42)

summary_by_depth = {}
for depth in DEPTH_VALUES:
    accs = [all_results[key][i]['accuracy'] for key in all_results for i, r in enumerate(all_results[key]) if r['depth'] == depth]
    sizes = [all_results[key][i]['size_kb'] for key in all_results for i, r in enumerate(all_results[key]) if r['depth'] == depth]
    avg_acc = sum(accs) / len(accs)
    total_size = sum(sizes)
    summary_by_depth[depth] = {'avg_acc': avg_acc, 'total_size': total_size}
    depth_label = str(depth) if depth is not None else 'ללא הגבלה'
    report_lines.append(f"{depth_label:<12}{avg_acc*100:.1f}%{'':<9}{total_size:.0f}")

with open(os.path.join(output_path, 'max_depth_results.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(report_lines))


#גרף המסחר-בין : דיוק ממוצע מול גודל קובץ כולל , לכל ערך max_depth
depth_labels_for_plot = [str(d) if d is not None else 'none' for d in DEPTH_VALUES]
avg_accuracies = [summary_by_depth[d]['avg_acc'] * 100 for d in DEPTH_VALUES]
total_sizes = [summary_by_depth[d]['total_size'] / 1024 for d in DEPTH_VALUES]  # ב-MB

fig, ax1 = plt.subplots(figsize=(9, 5))

color1 = 'tab:blue'
ax1.set_xlabel('max_depth')
ax1.set_ylabel('Average accuracy (%)', color=color1)
ax1.plot(depth_labels_for_plot, avg_accuracies, marker='o', color=color1, label='Accuracy')
ax1.axhline(BASELINE * 100, color='gray', linestyle='--', alpha=0.5, label='Baseline (33.3%)')
ax1.tick_params(axis='y', labelcolor=color1)

ax2 = ax1.twinx()
color2 = 'tab:red'
ax2.set_ylabel('Total size - all 8 models (MB)', color=color2)
ax2.plot(depth_labels_for_plot, total_sizes, marker='s', color=color2, label='Total size')
ax2.tick_params(axis='y', labelcolor=color2)

fig.suptitle('Accuracy vs model size tradeoff')
fig.tight_layout()
fig.savefig(os.path.join(output_path, 'accuracy_vs_size.png'), dpi=120)
plt.close(fig)


print("\nכל 8 המודלים נבדקו על פני כל ערכי max_depth!")
print(f"הדוח נשמר: {os.path.join(output_path, 'max_depth_results.txt')}")
print(f"הגרף נשמר: {os.path.join(output_path, 'accuracy_vs_size.png')}")