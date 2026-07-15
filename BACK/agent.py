#קובץ עבודה מול הסוכנים . שליחת פרומפטים , הפעלת מודלים 


import anthropic
import os
import pickle
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

documents = []
ids = []

with open(os.path.join(BASE_DIR, 'cluster_model', 'cluster_model_list.pkl'), 'rb') as f:
 all_cluster_models = pickle.load(f)

with open(os.path.join(BASE_DIR,'classification_model','classification_model_list.pkl'), 'rb') as f:
    all_classification_models = pickle.load(f)



#בדיקת המסמכים לכל הקבוצות לפי קלאסטרים 
for i in all_cluster_models:
 #השמת משתנים  מתוך המילון
 table = all_cluster_models[i]['table']
 sex = all_cluster_models[i]['sex']
 lift_column = all_cluster_models[i]['lift_column']
 
 #בדיקת מין
 sex_heb = 'גברים' if sex == 'M' else 'נשים'

 
 #ממוצעי הקבוצה 
 cols = ['Age_real', 'BodyweightKg_real', f'{lift_column}_real'] 
 stats = table.groupby('cluster')[cols].mean()
 #נתונים נוספים . טיית תקן ,מספר מאמנים , טווח , מינימום ומקסימום
 for cluster_id, row in stats.iterrows():
    
      #. כמה הקבוצה מפוזרת .חישוב סטיית תקן
     cluster_data = table[table['cluster'] == cluster_id]
     std_lift = cluster_data[f'{lift_column}_real'].std()
     min_lift = cluster_data[f'{lift_column}_real'].min()
     max_lift = cluster_data[f'{lift_column}_real'].max()
     n = len(cluster_data)
    
     age_str = f"גיל ממוצע {row['Age_real']:.1f} "
     #המרה לעברית 
     lift_heb = {
      'Best3SquatKg': 'סקוואט',
      'Best3BenchKg': 'בנץ',
      'Best3DeadliftKg': 'דדליפט',
      'TotalKg': 'טוטאל'
      }
     doc = f"קבוצה {cluster_id} של {sex_heb} ב-{lift_heb[lift_column]}: " \
          f"{age_str}" \
          f"משקל {row['BodyweightKg_real']:.1f} קג, " \
          f"{lift_heb[lift_column]} ממוצע {row[f'{lift_column}_real']:.1f} קג, " \
          f"טווח {min_lift:.0f}-{max_lift:.0f} קג, " \
          f"סטיית תקן {std_lift:.1f} קג, " \
          f"מספר מתאמנים {n}"
     
     #הוספה לרשימות 
     documents.append(doc)
     ids.append(f"{i}_cluster_{cluster_id}")

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
def class_user_predict(lift_column,sex,Age,BodyweightKg,lift_value):
 #מציאת מודל מתאים לפי פרטים שהוזנו
 key_model = find_key_class_predict(lift_column, sex)
 model = all_classification_models[key_model]

 # נרמול נתוני המשתמש
 user_data = [[Age, BodyweightKg, lift_value]]
 
 class_predict = model.predict(user_data)[0]
 return class_predict , key_model   



#פונקציית שאלת הסוכן classification
@observe()
def ask_agent_classifiation(lift_column,sex,Age,BodyweightKg,lift_value):
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
 - ביצוע: {lift_value} קג

 המודל חזה שקצב ההתקדמות הצפוי שלך הוא: {progress_map[the_class]}

 הסבר בעברית מה המשמעות של קצב זה, ומה המשתמש יכול לצפות לו."""


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
def cluster_user(lift_column,sex,Age,BodyweightKg,lift_value):
 #מציאת מודל מתאים לפי פרטים שהוזנו
 key_model = find_key_cluster(lift_column, sex)
 model = all_cluster_models[key_model]['model']
 scaler = all_cluster_models[key_model]['scaler']

 # נרמול נתוני המשתמש
 user_data = [[Age, BodyweightKg, lift_value]]
 

 user_scaled = scaler.transform(user_data)
 cluster = model.predict(user_scaled)[0]
 return cluster , key_model




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
 
