#קובץ עבודה מול הסוכנים . שליחת פרומפטים , הפעלת מודלים 

import pandas as pd
import anthropic
import os
import pickle
import gzip
import json
import chromadb
from langfuse import Langfuse, observe
from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor
from dotenv import dotenv_values


chroma_client = chromadb.Client()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
collection = chroma_client.get_or_create_collection("powerlifting_clusters")



config = dotenv_values(os.path.join(BASE_DIR, '.env'))

#פונקציית עזר . מחפשת קודם בקובץ .env (מקומי) , ואם לא נמצא - במשתני הסביבה האמיתיים (Railway)
def get_env(key):
    return config.get(key) or os.environ.get(key)


langfuse = Langfuse(
    public_key=get_env("LANGFUSE_PUBLIC_KEY"),
    secret_key=get_env("LANGFUSE_SECRET_KEY"),
    host="https://cloud.langfuse.com",
)
AnthropicInstrumentor().instrument()

client = anthropic.Anthropic(api_key=get_env("ANTHROPIC_API_KEY"))


#טעינת מודלי הקלאסטרינג (בלי טבלאות הנתונים הגולמיות)
with open(os.path.join(BASE_DIR, 'cluster_model', 'cluster_model_slim.pkl'), 'rb') as f:
 all_cluster_models = pickle.load(f)

#טעינת מודלי הקלאסיפיקציה (דחוסים)
with gzip.open(os.path.join(BASE_DIR, 'classification_model', 'classification_model_gz.pkl.gz'), 'rb') as f:
    all_classification_models = pickle.load(f)


#טעינת מסמכי הקבוצות שחושבו מראש מתוך הטבלאות
with open(os.path.join(BASE_DIR, 'cluster_model', 'cluster_documents.json'), 'r', encoding='utf-8') as f:
    cluster_documents_data = json.load(f)

documents = cluster_documents_data['documents']
ids = cluster_documents_data['ids']


if collection.count() == 0:
    collection.add(
        documents=documents,
        ids=ids
    )


##פונקציות הקלאסיפיקציה לפי קצב התקדמות ##



#פונקציה שמייצרת טקסט הכי רלוונטי ביחס למה שהמשתמש שאל 
def get_context(query, n_results=10):
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results['documents'][0]



#פונקציה שמוצאת מפתח CLASS 
def find_key_class_predict(lift_column, sex):
    lift_map = {
        'Best3SquatKg': 'squat',
        'Best3BenchKg': 'bench', 
        'Best3DeadliftKg': 'deadlift',
        'TotalKg': 'total'
    }
    sex_map = {'M': 'm', 'F': 'f'}
    return f"{lift_map[lift_column]}_{sex_map[sex]}"
    

#פונקציה שמחזירה מודל לפי המפתח של הCLASS
def class_user_predict(lift_column, sex, Age, BodyweightKg, lift_value):
    key_model = find_key_class_predict(lift_column, sex)
    model = all_classification_models[key_model]

    # טבלה עם שמות עמודות - כך sklearn מאמת את הסדר ולא נסמכים על מיקום
    user_df = pd.DataFrame(
        [[Age, BodyweightKg, lift_value]],
        columns=['Age', 'BodyweightKg', lift_column]
    )
    class_predict = model.predict(user_df[model.feature_names_in_])[0]
    return class_predict, key_model



#פונקציית שאלת הסוכן classification
@observe()
def ask_agent_classifiation(lift_column, sex, Age, BodyweightKg, lift_value):
 if Age is None:
     return "כדי לבצע ניתוח מדויק צריך את הגיל שלך - מה גילך?"
 the_class, key_model = class_user_predict(lift_column, sex, Age, BodyweightKg, lift_value)

 # בניית הפרומפט
 progress_map = {0: 'איטי', 1: 'בינוני', 2: 'מהיר'}

 prompt = f"""אתה מנתח אימוני פאוורליפטינג.

 נתוני המשתמש:
 - מגדר: {'גבר' if sex == 'M' else 'אישה'}
 - גיל: {Age}
 - משקל גוף: {BodyweightKg} קג
 - ביצוע ב-{lift_column}: {lift_value} קג

 המודל חזה שקצב ההתקדמות הצפוי שלך הוא: {progress_map[the_class]}

 הסבר בעברית מה המשמעות של קצב זה.

 חשוב: הנתונים שלמעלה הם היחידים שעליהם מבוסס הניתוח - אל תשתמש
 בערכים אחרים מההקשר. אל תספק אחוזים, טווחי משקל או טווחי זמן
 קונקרטיים - המודל החזיר תווית בלבד (איטי/בינוני/מהיר), לא תחזית
 מספרית."""

 # שלב שליחה לקלוד
 message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
 return message.content[0].text




## פונקציות הקלסאטרינג##


#פונקציה שמוצאת את המפתח הנכון לפי משתנים שהוזנו
def find_key_cluster(lift_column, sex):
    for key, value in all_cluster_models.items():
        if (value['lift_column'] == lift_column and
            value['sex'] == sex):
            return key
    return None



#פונקציה שמוצאת קלאסטר של משתמש . (מספר)
def cluster_user(lift_column, sex, Age, BodyweightKg, lift_value):
    key_model = find_key_cluster(lift_column, sex)
    if key_model is None:
        raise ValueError(f"לא נמצא מודל עבור {lift_column} / {sex}")

    entry  = all_cluster_models[key_model]
    model  = entry['model']
    scaler = entry['scaler']

    # טבלה עם שמות עמודות - כך sklearn מאמת את הסדר ולא נסמכים על מיקום
    user_df = pd.DataFrame(
        [[Age, BodyweightKg, lift_value]],
        columns=['Age', 'BodyweightKg', lift_column]
    )

    # כל שלב מסודר לפי הסדר שעליו אומן אותו רכיב
    scaled = pd.DataFrame(
        scaler.transform(user_df[scaler.feature_names_in_]),
        columns=scaler.feature_names_in_
    )
    cluster = model.predict(scaled[model.feature_names_in_])[0]

    return int(cluster), key_model




#פונקציית שאלת הסוכן cluster
@observe()
def ask_agent_cluster(user_query,lift_column,sex,Age,BodyweightKg,lift_value):
 if Age is None:
     return "כדי לבצע ניתוח מדויק צריך את הגיל שלך - מה גילך?"
 the_cluster, key_model = cluster_user(lift_column, sex, Age, BodyweightKg, lift_value)
 

 # שלב 1: שליפת context מChromaDB
 result = collection.get(ids=[f"{key_model}_cluster_{the_cluster}"])
 context_text = result['documents'][0]
    

    # בניית הפרומפט 
 prompt = f"""אתה מנתח אימוני פאוורליפטינג. 

    נתוני המשתמש:
   - מגדר: {'גבר' if sex == 'M' else 'אישה'}
   - גיל: {Age}
   - משקל גוף: {BodyweightKg} קג
   - ביצוע ב-{lift_column}: {lift_value} קג
   - קבוצה שסווג אליה: {the_cluster}

   מידע על הקבוצה שלו:
  {context_text}

  שאלת המשתמש: {user_query}

  ענה בעברית, השווה את המשתמש לקבוצה שלו, והסבר איפה הוא עומד ביחס לאחרים."""

 # שלב שליחה לקלוד 
 message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
 return message.content[0].text

  

#כלי טקסט שיהיה זמין לסוכן וידע איזו פונקציה להפעיל 
tools = [
    {
        "name": "analyze_cluster",
        "description": "מנתח את רמת הכוח של המתאמן ומשווה אותו לקבוצות דומות. השתמש בכלי זה כשהמשתמש שואל איפה הוא עומד, כמה הוא חזק ביחס לאחרים, או רוצה השוואה.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lift_column": {"type": "string", "description": "עמודת הליפט. סקוואט=Best3SquatKg, בנץ/לחיצת חזה=Best3BenchKg, דדליפט=Best3DeadliftKg, טוטאל/סה\"כ=TotalKg"},
                "sex": {"type": "string", "description": "מגדר: M או F"},
                "Age": {"type": "number", "description": "גיל המתאמן בשנים"},
                "BodyweightKg": {"type": "number", "description": "משקל גוף בקילוגרמים"},
                "lift_value": {"type": "number", "description": "ערך הליפט בקילוגרמים"}
            },
            "required": ["lift_column", "sex", "BodyweightKg", "lift_value","Age"]
        }
    },


    
    {
        "name": "predict_progress",
        "description": "מנבא את קצב ההתקדמות הצפוי של המתאמן (איטי/בינוני/מהיר). השתמש בכלי זה כשהמשתמש שואל על קצב התקדמות, פוטנציאל, או האם הוא מתקדם מהר.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lift_column": {"type": "string", "description": "עמודת הליפט. סקוואט=Best3SquatKg, בנץ/לחיצת חזה=Best3BenchKg, דדליפט=Best3DeadliftKg, טוטאל/סה\"כ=TotalKg"},
                "sex": {"type": "string", "description": "מגדר: M או F"},
                "Age": {"type": "number", "description": "גיל המתאמן"},
                "BodyweightKg": {"type": "number", "description": "משקל גוף בקילוגרמים"},
                "lift_value": {"type": "number", "description": "ערך הליפט בקילוגרמים"}
            },
            "required": ["lift_column", "sex", "Age", "BodyweightKg", "lift_value"]
        }
    }
]



##פונקציה שמאחדת את שתי הסוכנים ##
@observe()
def ask_full_agent(user_query): 
 #בניית פרומפט
 prompt = f"""אתה מנתח אימוני פאוורליפטינג. 

 שאלת המשתמש: {user_query}
 תנתח את נתוני המשתמש כמו :משקל גוף , גיל , סוג האימון , משקל הרמה לתרגיל הספציפי , מגדר .

 השתמש בכלים רק אם השאלה דורשת ניתוח נתונים ספציפי. 
 אם זו שאלה כללית — ענה ישירות בעברית."""
   # שלב שליחה לקלוד 
 message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": prompt}]
 )

 #אם קלוד הבין שצריך להשתמש בכלי מtools
 if message.stop_reason == "tool_use":
    # Claude בחר כלי — צריך להריץ אותו
    tool_call = next(block for block in message.content if block.type == "tool_use")
    tool_name = tool_call.name
    tool_input = tool_call.input
 else:
    # Claude ענה ישירות בטקסט
    return message.content[0].text
 


 #אם הבין שצריך את כלי ניתוח
 
 if tool_name == "analyze_cluster":
    result = ask_agent_cluster(
        user_query,
        tool_input['lift_column'],
        tool_input['sex'],
        tool_input['Age'],
        tool_input['BodyweightKg'],
        tool_input['lift_value']
    )
  # אם הבין שצריך לחזות קצב התקדמות
 elif tool_name == "predict_progress":
    result = ask_agent_classifiation(
        tool_input['lift_column'],
        tool_input['sex'],
        tool_input['Age'],
        tool_input['BodyweightKg'],
        tool_input['lift_value']
    )

 return result