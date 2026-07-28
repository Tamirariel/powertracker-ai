"""
build_artifacts.py - ייצור הארטיפקטים שהאפליקציה טוענת בזמן ריצה.

סקריפטי האימון מייצרים קובצי pickle שמכילים גם את המודלים וגם את טבלאות
הדאטה הגולמיות (כ-1.4 מיליון שורות, ~209MB). האפליקציה לא צריכה את הטבלאות:
היא משתמשת בהן פעם אחת בלבד, כדי לחשב תיאורי טקסט של הקבוצות עבור ה-RAG.

הסקריפט הזה מפריד בין השניים. הוא מקבל את תוצרי האימון ומייצר שלושה קבצים
מצומצמים (~30MB סה"כ) שהם היחידים שנטענים בזמן ריצה.

    קלט (תוצרי האימון, לא נשמרים בריפו):
      cluster_model/cluster_model_list.pkl
      classification_model/classification_model_list.pkl

    פלט (נשמר בריפו):
      cluster_model/cluster_documents.json          תיאורי הקבוצות ל-RAG
      cluster_model/cluster_model_slim.pkl          KMeans + scalers, בלי טבלאות
      classification_model/classification_model_gz.pkl.gz   Random Forest דחוס

הרצה:  python BACK/build_artifacts.py
"""

import os
import json
import gzip
import pickle
import warnings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLUSTER_DIR = os.path.join(BASE_DIR, 'cluster_model')
CLASSIFICATION_DIR = os.path.join(BASE_DIR, 'classification_model')

# תרגום שמות הליפטים לעברית, לשימוש בתיאורי הקבוצות
LIFT_HEB = {
    'Best3SquatKg': 'סקוואט',
    'Best3BenchKg': 'בנץ',
    'Best3DeadliftKg': 'דדליפט',
    'TotalKg': 'טוטאל',
}


def load_pickle(path):
    """טעינת קובץ pickle עם הודעת שגיאה ברורה אם הוא חסר."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"\nהקובץ לא נמצא: {path}\n"
            "הקובץ הזה הוא תוצר של סקריפטי האימון ואינו נשמר בריפו.\n"
            "הריצו קודם את שלבי האימון - ראו את סעיף Retrain the Models ב-README."
        )
    with open(path, 'rb') as f:
        return pickle.load(f)


def build_cluster_documents(all_cluster_models):
    """
    חישוב תיאורי הקבוצות עבור ChromaDB.

    לכל שילוב של ליפט ומגדר, ולכל קלאסטר בתוכו, נוצר משפט אחד בעברית
    שמסכם את הקבוצה: גיל ממוצע, משקל גוף, ביצוע ממוצע, טווח, סטיית תקן
    ומספר המתאמנים.

    שימו לב: פורמט המזהים (ids) חייב להישאר `{key}_cluster_{n}` -
    זה בדיוק מה ש-ask_agent_cluster ב-agent.py שולף לפיו.
    """
    documents = []
    ids = []

    for key in all_cluster_models:
        table = all_cluster_models[key]['table']
        sex = all_cluster_models[key]['sex']
        lift_column = all_cluster_models[key]['lift_column']

        sex_heb = 'גברים' if sex == 'M' else 'נשים'

        # ממוצעי הקבוצה
        cols = ['Age_real', 'BodyweightKg_real', f'{lift_column}_real']
        stats = table.groupby('cluster')[cols].mean()

        for cluster_id, row in stats.iterrows():
            # נתונים נוספים: סטיית תקן, טווח, ומספר מתאמנים
            cluster_data = table[table['cluster'] == cluster_id]
            std_lift = cluster_data[f'{lift_column}_real'].std()
            min_lift = cluster_data[f'{lift_column}_real'].min()
            max_lift = cluster_data[f'{lift_column}_real'].max()
            n = len(cluster_data)

            age_str = f"גיל ממוצע {row['Age_real']:.1f} "

            doc = f"קבוצה {cluster_id} של {sex_heb} ב-{LIFT_HEB[lift_column]}: " \
                  f"{age_str}" \
                  f"משקל {row['BodyweightKg_real']:.1f} קג, " \
                  f"{LIFT_HEB[lift_column]} ממוצע {row[f'{lift_column}_real']:.1f} קג, " \
                  f"טווח {min_lift:.0f}-{max_lift:.0f} קג, " \
                  f"סטיית תקן {std_lift:.1f} קג, " \
                  f"מספר מתאמנים {n}"

            documents.append(doc)
            ids.append(f"{key}_cluster_{cluster_id}")

    return documents, ids


def build_slim_cluster_models(all_cluster_models):
    """
    העתקת מודלי הקלאסטרינג בלי טבלאות הדאטה.

    נשמרים: model (KMeans), scaler, lift_column, sex, k.
    יורד: table - כ-94% מנפח הקובץ.
    """
    slim = {}
    for key in all_cluster_models:
        entry = dict(all_cluster_models[key])
        entry.pop('table', None)
        slim[key] = entry
    return slim


def verify_classification_models(original, restored):
    """
    אימות שהדחיסה לא שינתה ולו תחזית אחת.

    נבדקות שלוש דגימות מייצגות מול כל אחד משמונת המודלים.
    """
    samples = [[25, 70, 100], [40, 90, 180], [55, 110, 250]]

    with warnings.catch_warnings():
        # sklearn מעיר שהמודל אומן עם שמות עמודות ואנחנו בודקים עם רשימה.
        # לא רלוונטי כאן - אנחנו רק משווים תחזיות של אותו מודל לעצמו.
        warnings.simplefilter("ignore")

        for key in original:
            before = list(original[key].predict(samples))
            after = list(restored[key].predict(samples))
            if before != after:
                raise ValueError(
                    f"אימות נכשל עבור {key}: התחזיות אחרי הדחיסה שונות מהמקור.\n"
                    f"  מקור: {before}\n  דחוס: {after}"
                )
    return True


def mb(path):
    """גודל קובץ במגה-בייט."""
    return os.path.getsize(path) / 1_000_000


def main():
    src_cluster = os.path.join(CLUSTER_DIR, 'cluster_model_list.pkl')
    src_classification = os.path.join(CLASSIFICATION_DIR, 'classification_model_list.pkl')

    out_documents = os.path.join(CLUSTER_DIR, 'cluster_documents.json')
    out_slim = os.path.join(CLUSTER_DIR, 'cluster_model_slim.pkl')
    out_gz = os.path.join(CLASSIFICATION_DIR, 'classification_model_gz.pkl.gz')

    # ---- קלאסטרינג ----
    print("טוען את מודלי הקלאסטרינג...")
    all_cluster_models = load_pickle(src_cluster)

    print("מחשב את תיאורי הקבוצות...")
    documents, ids = build_cluster_documents(all_cluster_models)
    with open(out_documents, 'w', encoding='utf-8') as f:
        json.dump({'documents': documents, 'ids': ids}, f, ensure_ascii=False, indent=1)
    print(f"  נוצרו {len(documents)} תיאורים")
    print(f"  דוגמה: {documents[0]}")

    print("שומר את המודלים בלי הטבלאות...")
    slim = build_slim_cluster_models(all_cluster_models)
    with open(out_slim, 'wb') as f:
        pickle.dump(slim, f)

    # ---- קלאסיפיקציה ----
    print("\nטוען את מודלי הקלאסיפיקציה...")
    all_classification_models = load_pickle(src_classification)

    print("דוחס...")
    with open(out_gz, 'wb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', compresslevel=6, mtime=0) as f:
            pickle.dump(all_classification_models, f)

    print("מאמת שהתחזיות זהות...")
    with gzip.open(out_gz, 'rb') as f:
        restored = pickle.load(f)
    verify_classification_models(all_classification_models, restored)
    print(f"  עבר - כל {len(all_classification_models)} המודלים מחזירים תחזיות זהות")

    # ---- דוח ----
    print("\n" + "=" * 58)
    print("סיכום")
    print("=" * 58)

    before_total = mb(src_cluster) + mb(src_classification)
    after_total = mb(out_documents) + mb(out_slim) + mb(out_gz)

    print("\nקלט (תוצרי אימון):")
    for p in [src_cluster, src_classification]:
        print(f"  {os.path.basename(p):40s} {mb(p):8.2f} MB")

    print("\nפלט (ארטיפקטים):")
    for p in [out_documents, out_slim, out_gz]:
        print(f"  {os.path.basename(p):40s} {mb(p):8.2f} MB")

    saved = 100 * (1 - after_total / before_total)
    print(f"\n  {before_total:.1f} MB -> {after_total:.1f} MB  (חיסכון של {saved:.0f}%)")


if __name__ == '__main__':
    main()