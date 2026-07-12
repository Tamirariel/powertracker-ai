import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

path = r'C:\Users\yuval\OneDrive - Shoham Schools\שולחן העבודה\AI\myapp\AGENT_data'

df = pd.read_csv(path + r'\cleaned_openpowerlifting.csv', low_memory=False)



print("בדיקות גברים בנץ+סקווט+דדליפט עם גיל")

#וידוא מחיקת מתאמנים בלי גיל
df_with_age = df[df['Age'].notna()]



#וידוא מחיקת מתאמנים בלי משקלל כולל
SBD_table_age = df_with_age[df_with_age['TotalKg'].notna()]



#סינון טבלה רק לפי עמודות הרלוונטיות לסקוואט עם גיל, משקל גוף ומין
SBD_table_age = SBD_table_age[['Age', 'TotalKg','BodyweightKg', 'Sex']]

#הסרת שורות מתאמנים בלי משקל גוף
SBD_table_age=SBD_table_age[SBD_table_age['BodyweightKg'].notna()]



#פיצול עמודת המין למספר עמודות בינאריות לכל מין
is_sex=SBD_table_age['Sex'].str.get_dummies()
SBD_table_age = pd.concat([SBD_table_age, is_sex], axis=1)
SBD_table_age.drop(columns=['Sex'], inplace=True)

#מחיקת עמודות המגדר 
SBD_table_age_m = SBD_table_age[SBD_table_age['M']==1]
SBD_table_age_m.drop('M', axis=1, inplace=True)
SBD_table_age_m.drop('F',axis =1 , inplace=True)


#סטרדינג של העמודות הרלוונטיות
scaler = StandardScaler()
SBD_table_age_m[['Age', 'BodyweightKg', 'TotalKg']] = scaler.fit_transform(SBD_table_age_m[['Age', 'BodyweightKg','TotalKg']])


#בדיקת ציון בדיקת סילואט לכל מספר קבוצות . אני משארי את הבדיקה הזו כאן לצורך השוואה אבל היא הייתה בכל אחד משאר החלקים 
silhouette_scores = []
for k in range(2,7):
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(SBD_table_age_m)
    silhouette_scores.append(silhouette_score(SBD_table_age_m, kmeans.labels_, sample_size=15000, random_state=42))
for k, score in zip(range(2,7), silhouette_scores):
    print(f"k={k}: silhouette={score:.4f}")


#הרצת המודל עם מספר הקבוצות לפי הבדיקות שהרצנו (6)
model = KMeans(n_clusters=6, random_state=42)
SBD_table_age_m['cluster'] = model.fit_predict(SBD_table_age_m)



#ייצוג של הערכים לפני הסטנדרזציה 
original_values = scaler.inverse_transform(SBD_table_age_m[['Age', 'BodyweightKg', 'TotalKg']])
SBD_table_age_m[['Age_real', 'BodyweightKg_real', 'TotalKg_real']] = original_values
print(SBD_table_age_m.groupby('cluster')[['Age_real', 'BodyweightKg_real', 'TotalKg_real']].mean())



print("בדיקות נשים בנץ+סקווט+דדליפט עם גיל")



#מחיקת עמודות המגדר 
SBD_table_age_f = SBD_table_age[SBD_table_age['F']==1]
SBD_table_age_f.drop('M', axis=1, inplace=True)
SBD_table_age_f.drop('F',axis =1 , inplace=True)


#סטרדינג של העמודות הרלוונטיות
scaler = StandardScaler()
SBD_table_age_f[['Age', 'BodyweightKg', 'TotalKg']] = scaler.fit_transform(SBD_table_age_f[['Age', 'BodyweightKg','TotalKg']])


#בדיקת ציון בדיקת סילואט לכל מספר קבוצות . אני משארי את הבדיקה הזו כאן לצורך השוואה אבל היא הייתה בכל אחד משאר החלקים 
silhouette_scores = []
for k in range(2,7):
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(SBD_table_age_f)
    silhouette_scores.append(silhouette_score(SBD_table_age_f, kmeans.labels_, sample_size=15000, random_state=42))
for k, score in zip(range(2,7), silhouette_scores):
    print(f"k={k}: silhouette={score:.4f}")


#הרצת המודל עם מספר הקבוצות לפי הבדיקות שהרצנו (4)
model = KMeans(n_clusters=4, random_state=42)
SBD_table_age_f['cluster'] = model.fit_predict(SBD_table_age_f)



#ייצוג של הערכים לפני הסטנדרזציה 
original_values = scaler.inverse_transform(SBD_table_age_f[['Age', 'BodyweightKg', 'TotalKg']])
SBD_table_age_f[['Age_real', 'BodyweightKg_real', 'TotalKg_real']] = original_values
print(SBD_table_age_f.groupby('cluster')[['Age_real', 'BodyweightKg_real', 'TotalKg_real']].mean())




print("בדיקות גברים בנץ+סקווט+דדליפט בלי גיל")



#וידוא מחיקת מתאמנים בלי משקל כולל
SBD_table_no_age = df[df['TotalKg'].notna()]



#סינון טבלה רק לפי עמודות הרלוונטיות לסקוואט עם גיל, משקל גוף ומין
SBD_table_no_age = SBD_table_no_age[[ 'TotalKg','BodyweightKg', 'Sex']]


#הסרת שורות מתאמנים בלי משקל גוף
SBD_table_no_age=SBD_table_no_age[SBD_table_no_age['BodyweightKg'].notna()]



#פיצול עמודת המין למספר עמודות בינאריות לכל מין
is_sex=SBD_table_no_age['Sex'].str.get_dummies()
SBD_table_no_age = pd.concat([SBD_table_no_age, is_sex], axis=1)
SBD_table_no_age.drop(columns=['Sex'], inplace=True)

#מחיקת עמודות המגדר 
SBD_table_no_age_m = SBD_table_no_age[SBD_table_no_age['M']==1]
SBD_table_no_age_m.drop('M', axis=1, inplace=True)
SBD_table_no_age_m.drop('F',axis =1 , inplace=True)


#סטרדינג של העמודות הרלוונטיות
scaler = StandardScaler()
SBD_table_no_age_m[[ 'BodyweightKg', 'TotalKg']] = scaler.fit_transform(SBD_table_no_age_m[[ 'BodyweightKg','TotalKg']])


#בדיקת ציון בדיקת סילואט לכל מספר קבוצות . אני משארי את הבדיקה הזו כאן לצורך השוואה אבל היא הייתה בכל אחד משאר החלקים 
silhouette_scores = []
for k in range(2,7):
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(SBD_table_no_age_m)
    silhouette_scores.append(silhouette_score(SBD_table_no_age_m, kmeans.labels_, sample_size=15000, random_state=42))
for k, score in zip(range(2,7), silhouette_scores):
    print(f"k={k}: silhouette={score:.4f}")


#הרצת המודל עם מספר הקבוצות לפי הבדיקות שהרצנו (4)
model = KMeans(n_clusters=4, random_state=42)
SBD_table_no_age_m['cluster'] = model.fit_predict(SBD_table_no_age_m)



#ייצוג של הערכים לפני הסטנדרזציה 
original_values = scaler.inverse_transform(SBD_table_no_age_m[['BodyweightKg', 'TotalKg']])
SBD_table_no_age_m[[ 'BodyweightKg_real', 'TotalKg_real']] = original_values
print(SBD_table_no_age_m.groupby('cluster')[[ 'BodyweightKg_real', 'TotalKg_real']].mean())



print("בדיקות נשים בנץ+סקווט+דדליפט בלי גיל")



#מחיקת עמודות המגדר 
SBD_table_no_age_f = SBD_table_no_age[SBD_table_no_age['F']==1]
SBD_table_no_age_f.drop('M', axis=1, inplace=True)
SBD_table_no_age_f.drop('F',axis =1 , inplace=True)


#סטרדינג של העמודות הרלוונטיות
scaler = StandardScaler()
SBD_table_no_age_f[[ 'BodyweightKg', 'TotalKg']] = scaler.fit_transform(SBD_table_no_age_f[[ 'BodyweightKg','TotalKg']])


#בדיקת ציון בדיקת סילואט לכל מספר קבוצות . אני משארי את הבדיקה הזו כאן לצורך השוואה אבל היא הייתה בכל אחד משאר החלקים 
silhouette_scores = []
for k in range(2,7):
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(SBD_table_no_age_f)
    silhouette_scores.append(silhouette_score(SBD_table_no_age_f, kmeans.labels_, sample_size=15000, random_state=42))
for k, score in zip(range(2,7), silhouette_scores):
    print(f"k={k}: silhouette={score:.4f}")


#הרצת המודל עם מספר הקבוצות לפי הבדיקות שהרצנו (3)
model = KMeans(n_clusters=3, random_state=42)
SBD_table_no_age_f['cluster'] = model.fit_predict(SBD_table_no_age_f)



#ייצוג של הערכים לפני הסטנדרזציה 
original_values = scaler.inverse_transform(SBD_table_no_age_f[['BodyweightKg', 'TotalKg']])
SBD_table_no_age_f[[ 'BodyweightKg_real', 'TotalKg_real']] = original_values
print(SBD_table_no_age_f.groupby('cluster')[[ 'BodyweightKg_real', 'TotalKg_real']].mean())

