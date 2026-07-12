import pandas as pd
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(BASE_DIR, 'AGENT_data')

df = pd.read_csv(path + r'\openpowerlifting.csv', low_memory=False)

#בודק רק אם מתחרים עם ציוד בסיסי
df = df[df['Equipment'].isin(['Raw', 'Wraps'])]

#החלפת ערכים שליליים ב-NaN
df.loc[df['Best3SquatKg'] < 0, 'Best3SquatKg'] = np.nan
df.loc[df['Best3BenchKg'] < 0, 'Best3BenchKg'] = np.nan
df.loc[df['Best3DeadliftKg'] < 0, 'Best3DeadliftKg'] = np.nan

#בדיקת NaN לפני טיפול ב-IQR
print("NaN לפני IQR:")
print(df[['Best3SquatKg', 'Best3BenchKg', 'Best3DeadliftKg']].isnull().sum())


#טיפול ב-IQR לכל עמודה בנפרד, תוך התחשבות במין ובמשקל   
for col in ['Best3SquatKg', 'Best3BenchKg', 'Best3DeadliftKg']:
    Q1 = df.groupby(['Sex', 'WeightClassKg'])[col].transform(lambda x: x.quantile(0.25))
    Q3 = df.groupby(['Sex', 'WeightClassKg'])[col].transform(lambda x: x.quantile(0.75))
    IQR = Q3 - Q1
    upper_bound = Q3 + 1.5 * IQR
    lower_bound = Q1 - 1.5 * IQR
    df.loc[df[col] < lower_bound, col] = np.nan
    df.loc[df[col] > upper_bound, col] = np.nan

print("NaN אחרי IQR:")
print(df[['Best3SquatKg', 'Best3BenchKg', 'Best3DeadliftKg']].isnull().sum())


#סטטיסטיקות על מספר התחרויות של המתאמנים
only_once = sum(df['Name'].value_counts() == 1)
print(f"מספר מתחרים שהשתתפו רק פעם אחת: {only_once}")
how_many = df['Name'].value_counts()
print(f"מספר מתחרים שהשתתפו יותר מפעם אחת: {sum(how_many > 1)}")
print(how_many.describe())
competitions_per_athlete = df['Name'].value_counts()
athletes_5plus = sum(competitions_per_athlete >= 5)
print(f"מתאמנים עם 5 תחרויות ומעלה: {athletes_5plus}")
print(f"אחוז מסך המתאמנים: {athletes_5plus / len(competitions_per_athlete) * 100:.1f}%")


df.to_csv(path + r'\cleaned_openpowerlifting.csv', index=False)






