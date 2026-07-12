import pandas as pd
import matplotlib.pyplot as plt
import pickle
import os

#התיקייה שבה הסקריפט הזה יושב (cluster_model)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

#תיקייה לשמירת הגרפים
output_path = os.path.join(SCRIPT_DIR, 'cluster_plots')
os.makedirs(output_path, exist_ok=True)


#טעינת המודלים והטבלאות ששמרנו באימון
with open(os.path.join(SCRIPT_DIR, 'cluster_model_list.pkl'), 'rb') as f:
    all_cluster_models = pickle.load(f)


#המרה לעברית לכותרות
lift_heb = {
 'Best3SquatKg': 'Squat',
 'Best3BenchKg': 'Bench',
 'Best3DeadliftKg': 'Deadlift',
 'TotalKg': 'Total'
 }


#כמה נקודות לצייר בכל גרף . ציור של מאות אלפי נקודות כבד ומיותר
PLOT_SAMPLE = 20000


for key in all_cluster_models:
    print(f"מצייר גרף: {key}")

    #השמת משתנים מתוך המילון
    table = all_cluster_models[key]['table']
    lift_column = all_cluster_models[key]['lift_column']
    sex = all_cluster_models[key]['sex']
    include_age = all_cluster_models[key]['include_age']
    k = all_cluster_models[key]['k']

    #דגימה אקראית לציור בלבד . אם הטבלה קטנה מהמדגם לוקחים הכל
    if len(table) > PLOT_SAMPLE:
        plot_table = table.sample(PLOT_SAMPLE, random_state=42)
    else:
        plot_table = table

    #כותרת בעברית
    sex_heb = 'Men' if sex == 'M' else 'Women'
    age_heb = 'with age' if include_age == 1 else 'no age'

    #גרף פיזור - משקל גוף מול הליפט , צבוע לפי קבוצה
    fig, ax = plt.subplots(figsize=(9, 6))
    scatter = ax.scatter(
        plot_table['BodyweightKg_real'],
        plot_table[f'{lift_column}_real'],
        c=plot_table['cluster'],
        cmap='viridis',
        s=4,
        alpha=0.4
    )

    ax.set_xlabel('Bodyweight (kg)')
    ax.set_ylabel(f'{lift_heb[lift_column]} (kg)')
    ax.set_title(f'{key} | {lift_heb[lift_column]} | {sex_heb} | {age_heb} | k={k}')
    ax.grid(True, alpha=0.3)

    #מקרא של הקבוצות
    legend = ax.legend(*scatter.legend_elements(), title='Cluster')
    ax.add_artist(legend)

    fig.tight_layout()
    fig.savefig(os.path.join(output_path, f'{key}.png'), dpi=120)
    plt.close(fig)


print("\nכל הגרפים נוצרו בהצלחה!")
print(f"הגרפים נשמרו בתיקייה: {output_path}")