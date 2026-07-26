#חישובי פאוורליפטינג . 1RM משוער , התקדמות לפי תאריך , וקצב אישי
from datetime import date as _date
import database

POWER_LIFTS = ['סקוואט', 'בנץ', 'דדליפט']


#הערכת 1RM לפי נוסחת Epley . מתרגם סט עבודה לשווה ערך של הרמה מקסימלית אחת
def epley_1rm(weight, reps):
    if reps == 1:
        return weight
    return weight * (1 + reps / 30)


#שיפוע רגרסיה לינארית . נוסחה סגורה - זהה מתמטית ל-LinearRegression עם משתנה אחד
def linear_slope(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    denom = sum((x - mean_x) ** 2 for x in xs)
    if denom == 0:
        return None
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    return num / denom



#התקדמות בתרגיל אחד . לכל תאריך נלקח הסט עם ה-1RM המשוער הגבוה ביותר
def lift_progress(lift_name):
    history = database.get_exercise_history(lift_name)

    best_by_date = {}
    for row in history:
        est = epley_1rm(row['weight'], row['reps'])
        d = row['date']
        if d not in best_by_date or est > best_by_date[d]:
            best_by_date[d] = est

    points = [
        {"date": d, "est_1rm": round(v, 1)}
        for d, v in sorted(best_by_date.items())
    ]

    if not points:
        return {"name": lift_name, "best_1rm": None, "slope": None, "points": []}

    #ציר ה-x בחודשים מהאימון הראשון . 30.44 = אורך חודש ממוצע
    first = _date.fromisoformat(points[0]["date"])
    xs = [(_date.fromisoformat(p["date"]) - first).days / 30.44 for p in points]
    ys = [p["est_1rm"] for p in points]

    slope = linear_slope(xs, ys)

    #שיפוע על טווח קצר מדי הוא רעש . דורשים לפחות חודש של היסטוריה ושלוש נקודות
    if slope is not None and (xs[-1] < 1.0 or len(points) < 3):
        slope = None

    return {
        "name": lift_name,
        "best_1rm": round(max(ys), 1),
        "slope": round(slope, 2) if slope is not None else None,
        "points": points,
    }

 



#שלושת הליפטים בבקשה אחת . הטוטאל מוחזר רק אם יש נתונים בשלושתם
def all_progress():
    lifts = [lift_progress(name) for name in POWER_LIFTS]
    bests = [l["best_1rm"] for l in lifts]

    total = round(sum(bests), 1) if all(b is not None for b in bests) else None
    return {"lifts": lifts, "total": total}