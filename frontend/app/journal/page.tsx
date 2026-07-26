"use client";
import { useState, useEffect, useCallback } from "react";

type WorkoutSet = { reps: number; weight: number };
type Exercise = { name: string; sets: WorkoutSet[] };
type Workout = { id: number; date: string; workout_type: string; exercises: Exercise[] };

// טיוטת תרגיל בטופס - נושאת גם את שדות הקלט שלה
type DraftExercise = Exercise & { numSets: number; reps: number; weight: number };

const HEBREW_MONTHS = ["ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני",
  "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"];

const WEEKDAYS = ["א", "ב", "ג", "ד", "ה", "ו", "ש"];

const WORKOUT_TYPES = ["רגליים", "חזה", "גב", "כתפיים", "ידיים", "גוף מלא"];

// שלושת הראשונים הם תרגילי הפאוורליפטינג - אסור לשנות את האיות
const BASE_EXERCISES = [
  "סקוואט", "בנץ", "דדליפט",
  "לחיצת רגליים", "לחיצת כתפיים", "עליות מתח", "חתירה",
  "פולי עליון", "לחיצת חזה בשיפוע", "כפיפת מרפקים", "פשיטת מרפקים",
  "לאנג׳ים", "כפיפת ברכיים", "הרחקות כתף", "בטן",
];

const TYPE_COLORS: Record<string, string> = {
  "רגליים": "#F2B705",
  "חזה": "#2DD4BF",
  "גב": "#818CF8",
  "כתפיים": "#FB7185",
  "ידיים": "#34D399",
  "גוף מלא": "#F472B6",
};

const API = "/api/backend";

// YYYY-MM-DD בזמן מקומי. toISOString היה מזיז יום אחורה בגלל UTC
function dateKey(year: number, month: number, day: number) {
  return `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function todayKey() {
  const t = new Date();
  return dateKey(t.getFullYear(), t.getMonth(), t.getDate());
}

export default function JournalPage() {
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [names, setNames] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [view, setView] = useState(() => {
    const t = new Date();
    return { year: t.getFullYear(), month: t.getMonth() };
  });

  // הטופס
  const [wDate, setWDate] = useState(todayKey);
  const [wType, setWType] = useState(WORKOUT_TYPES[0]);
  const [draft, setDraft] = useState<DraftExercise[]>([]);
  const [startedDate, setStartedDate] = useState<string | null>(null);
  const [pick, setPick] = useState(BASE_EXERCISES[0]);
  const [customName, setCustomName] = useState("");
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");
  const [lastWorkout, setLastWorkout] = useState<Workout | null>(null);

  const loadWorkouts = useCallback(() => {
    fetch(`${API}/workouts/full`)
      .then(res => {
        if (!res.ok) throw new Error(`שגיאה ${res.status}`);
        return res.json();
      })
      .then(setWorkouts)
      .catch(e => setError(String(e)));
  }, []);

  const loadNames = useCallback(() => {
    fetch(`${API}/exercises/names`)
      .then(res => res.json())
      .then(setNames)
      .catch(() => {});
  }, []);

  // האימון האחרון מהסוג הנבחר . 404 הוא תשובה תקינה - אין אימון כזה
  const loadLast = useCallback((type: string) => {
    fetch(`${API}/workouts/last/${encodeURIComponent(type)}`)
      .then(res => (res.ok ? res.json() : null))
      .then(setLastWorkout)
      .catch(() => setLastWorkout(null));
  }, []);

  useEffect(() => {
    loadWorkouts();
    loadNames();
  }, [loadWorkouts, loadNames]);

  // נטען מחדש בכל שינוי סוג אימון
  useEffect(() => {
    loadLast(wType);
  }, [wType, loadLast]);

  // איחוד הרשימה הבסיסית עם תרגילים שהוזנו ידנית בעבר
  const exerciseList = [
    ...BASE_EXERCISES,
    ...names.filter(n => !BASE_EXERCISES.includes(n)),
    "אחר",
  ];

  // עדכון תרגיל בודד בטיוטה . יוצר מערך חדש ולא מוטט את הקיים
  function updateDraft(i: number, patch: Partial<DraftExercise>) {
    setDraft(prev => prev.map((ex, j) => (j === i ? { ...ex, ...patch } : ex)));
  }

  function addExercise() {
    const name = pick === "אחר" ? customName.trim() : pick;
    if (!name) {
      setNotice("צריך לבחור או להקליד שם תרגיל");
      return;
    }
    if (draft.length === 0) setStartedDate(wDate);
    setDraft(prev => [...prev, { name, sets: [], numSets: 1, reps: 8, weight: 50 }]);
    setCustomName("");
    setNotice("");
  }

  function duplicateLast() {
    if (!lastWorkout) return;
    if (draft.length > 0) {
      setNotice("יש כבר תרגילים בטופס . נקה קודם אם אתה רוצה לשכפל");
      return;
    }
    setStartedDate(wDate);
    setDraft(
      lastWorkout.exercises.map(ex => ({
        name: ex.name,
        sets: ex.sets.map(s => ({ ...s })),   // עותק ולא הפניה לאובייקטים המקוריים
        numSets: 1,
        reps: 8,
        weight: 50,
      }))
    );
    setNotice("");
  }

  function addSets(i: number) {
    const ex = draft[i];
    const newSets = Array.from({ length: ex.numSets }, () => ({
      reps: ex.reps,
      weight: ex.weight,
    }));
    updateDraft(i, { sets: [...ex.sets, ...newSets] });
  }

  function removeSet(i: number, j: number) {
    updateDraft(i, { sets: draft[i].sets.filter((_, k) => k !== j) });
  }

  function removeExercise(i: number) {
    setDraft(prev => prev.filter((_, j) => j !== i));
  }

  function clearForm() {
    setDraft([]);
    setStartedDate(null);
    setNotice("");
  }

  async function saveWorkout() {
    const empty = draft.filter(ex => ex.sets.length === 0).map(ex => ex.name);
    if (empty.length > 0) {
      setNotice(`יש תרגילים בלי סטים: ${empty.join(", ")}`);
      return;
    }

    setSaving(true);
    setNotice("");
    try {
      const res = await fetch(`${API}/workouts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          date: wDate,
          workout_type: wType,
          exercises: draft.map(ex => ({ name: ex.name, sets: ex.sets })),
        }),
      });
      if (!res.ok) throw new Error(`שגיאה ${res.status}`);
      clearForm();
      setNotice("האימון נשמר!");
      loadWorkouts();
      loadNames();
      loadLast(wType);   // כדי שכפתור השכפול יציע את החדש ולא את הקודם
    } catch (e) {
      setNotice(`שגיאה בשמירה: ${e}`);
    } finally {
      setSaving(false);
    }
  }

  async function deleteWorkout(id: number) {
    try {
      const res = await fetch(`${API}/workouts/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error(`שגיאה ${res.status}`);
      setSelected(null);
      loadWorkouts();
      loadLast(wType);
    } catch (e) {
      setError(`שגיאה במחיקה: ${e}`);
    }
  }

  // לוח השנה
  const byDate: Record<string, Workout[]> = {};
  for (const w of workouts) {
    (byDate[w.date] ??= []).push(w);
  }

  const firstWeekday = new Date(view.year, view.month, 1).getDay();
  const daysInMonth = new Date(view.year, view.month + 1, 0).getDate();
  const today = todayKey();

  function shiftMonth(delta: number) {
    setSelected(null);
    setView(prev => {
      const d = new Date(prev.year, prev.month + delta, 1);
      return { year: d.getFullYear(), month: d.getMonth() };
    });
  }

  const selectedWorkouts = selected ? byDate[selected] ?? [] : [];
  const dateChanged = draft.length > 0 && startedDate !== null && startedDate !== wDate;

  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="text-2xl font-bold">יומן אימונים</h1>
      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}

      {/* ===== אימון חדש ===== */}
      <h2 className="mt-8 text-lg font-bold">אימון חדש</h2>

      <div className="mt-3 flex gap-3">
        <div className="flex-1">
          <label className="mb-1 block text-sm text-white/60">תאריך</label>
          <input
            type="date"
            value={wDate}
            onChange={e => setWDate(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 outline-none focus:border-blue-500"
          />
        </div>
        <div className="flex-1">
          <label className="mb-1 block text-sm text-white/60">סוג אימון</label>
          <select
            value={wType}
            onChange={e => setWType(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 outline-none focus:border-blue-500"
          >
            {WORKOUT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
      </div>

      {dateChanged && (
        <p className="mt-3 rounded-lg bg-yellow-500/10 p-3 text-sm text-yellow-300">
          שים לב: התחלת את הטופס בתאריך {startedDate} ועכשיו נבחר {wDate}. כל התרגילים
          בטופס יישמרו יחד בתאריך החדש. אם התכוונת לאימון נפרד — שמור או נקה את הטופס קודם.
        </p>
      )}

      {lastWorkout && (
        <button
          onClick={duplicateLast}
          className="mt-3 w-full rounded-lg bg-white/10 px-4 py-2 text-sm"
        >
          שכפל את אימון ה{wType} מ-{lastWorkout.date}
        </button>
      )}

      {/* הוספת תרגיל */}
      <div className="mt-4 flex gap-2">
        <select
          value={pick}
          onChange={e => setPick(e.target.value)}
          className="flex-1 rounded-lg border border-white/10 bg-white/5 px-3 py-2 outline-none focus:border-blue-500"
        >
          {exerciseList.map(n => <option key={n} value={n}>{n}</option>)}
        </select>
        {pick === "אחר" && (
          <input
            value={customName}
            onChange={e => setCustomName(e.target.value)}
            placeholder="שם התרגיל"
            className="flex-1 rounded-lg border border-white/10 bg-white/5 px-3 py-2 outline-none focus:border-blue-500"
          />
        )}
        <button onClick={addExercise} className="rounded-lg bg-white/10 px-4 py-2 text-sm">
          הוסף תרגיל
        </button>
      </div>

      {/* התרגילים בטיוטה - האחרון שנוסף מוצג ראשון */}
      {draft.map((_, i) => i).reverse().map(i => {
        const ex = draft[i];
        return (
          <div key={i} className="mt-4 rounded-lg border border-white/10 p-4">
            <h3 className="font-bold">{ex.name}</h3>

            {ex.sets.map((s, j) => (
              <div key={j} className="mt-2 flex items-center gap-3 text-sm">
                <span className="flex-1">סט {j + 1}: {s.reps} חזרות | {s.weight} ק״ג</span>
                <button onClick={() => removeSet(i, j)} className="text-white/50 hover:text-red-400">
                  מחק
                </button>
              </div>
            ))}

            <div className="mt-3 flex items-end gap-2">
              <div className="flex-1">
                <label className="mb-1 block text-xs text-white/50">סטים</label>
                <input
                  type="number" min={1} max={15} value={ex.numSets}
                  onChange={e => updateDraft(i, { numSets: Number(e.target.value) })}
                  className="w-full rounded-lg border border-white/10 bg-white/5 px-2 py-1.5 text-sm outline-none focus:border-blue-500"
                />
              </div>
              <div className="flex-1">
                <label className="mb-1 block text-xs text-white/50">חזרות</label>
                <input
                  type="number" min={1} max={100} value={ex.reps}
                  onChange={e => updateDraft(i, { reps: Number(e.target.value) })}
                  className="w-full rounded-lg border border-white/10 bg-white/5 px-2 py-1.5 text-sm outline-none focus:border-blue-500"
                />
              </div>
              <div className="flex-1">
                <label className="mb-1 block text-xs text-white/50">משקל (ק״ג)</label>
                <input
                  type="number" min={0} max={600} step={2.5} value={ex.weight}
                  onChange={e => updateDraft(i, { weight: Number(e.target.value) })}
                  className="w-full rounded-lg border border-white/10 bg-white/5 px-2 py-1.5 text-sm outline-none focus:border-blue-500"
                />
              </div>
              <button onClick={() => addSets(i)} className="rounded-lg bg-blue-600 px-4 py-1.5 text-sm">
                הוסף
              </button>
            </div>

            <button
              onClick={() => removeExercise(i)}
              className="mt-3 text-sm text-white/50 hover:text-red-400"
            >
              הסר תרגיל
            </button>
          </div>
        );
      })}

      {draft.length > 0 && (
        <div className="mt-4 flex gap-2">
          <button
            onClick={saveWorkout}
            disabled={saving}
            className="flex-1 rounded-lg bg-blue-600 px-4 py-2 font-bold disabled:opacity-50"
          >
            {saving ? "שומר..." : "שמור אימון"}
          </button>
          <button onClick={clearForm} className="rounded-lg bg-white/10 px-4 py-2">
            נקה טופס
          </button>
        </div>
      )}

      {notice && <p className="mt-3 text-sm text-white/70">{notice}</p>}

      {/* ===== היסטוריה ===== */}
      <hr className="my-8 border-white/10" />
      <h2 className="text-lg font-bold">היסטוריה</h2>

      <div className="mt-4 flex items-center justify-between">
        <button onClick={() => shiftMonth(-1)} className="rounded-lg bg-white/5 px-4 py-2">
          ‹ הקודם
        </button>
        <h3 className="font-bold">{HEBREW_MONTHS[view.month]} {view.year}</h3>
        <button onClick={() => shiftMonth(1)} className="rounded-lg bg-white/5 px-4 py-2">
          הבא ›
        </button>
      </div>

      <div className="mt-4 grid grid-cols-7 gap-1">
        {WEEKDAYS.map(d => (
          <div key={d} className="pb-1 text-center text-sm font-bold text-white/50">{d}</div>
        ))}

        {Array.from({ length: firstWeekday }, (_, i) => <div key={`pad-${i}`} />)}

        {Array.from({ length: daysInMonth }, (_, i) => {
          const day = i + 1;
          const key = dateKey(view.year, view.month, day);
          const has = key in byDate;
          const isSel = key === selected;

          return (
            <button
              key={key}
              onClick={() => setSelected(isSel ? null : key)}
              className={[
                "aspect-square rounded-lg text-sm transition",
                has ? "bg-blue-600/80 font-bold" : "bg-white/5",
                isSel ? "ring-2 ring-white/60" : "",
                key === today && !isSel ? "ring-1 ring-white/30" : "",
              ].join(" ")}
            >
              {day}
              {has && <span className="block text-[10px] leading-none">🔥</span>}
            </button>
          );
        })}
      </div>

      <p className="mt-3 text-xs text-white/40">🔥 = יום עם אימון | מסגרת = היום</p>

      {selected && (
        <div className="mt-6 space-y-3">
          {selectedWorkouts.length === 0 ? (
            <p className="text-sm text-white/50">אין אימון בתאריך {selected}</p>
          ) : (
            selectedWorkouts.map(w => (
              <div key={w.id} className="rounded-lg border border-white/10 p-4">
                <div className="mb-3 flex items-center gap-3">
                  <span
                    className="rounded-full px-3 py-1 text-sm font-semibold"
                    style={{ background: TYPE_COLORS[w.workout_type] ?? "#F2B705", color: "#12141C" }}
                  >
                    {w.workout_type}
                  </span>
                  <span className="text-sm text-white/60">{w.date}</span>
                </div>

                {w.exercises.map((ex, i) => (
                  <p key={i} className="text-sm">
                    <span className="font-bold">{ex.name}</span>
                    {": "}
                    {ex.sets.map(s => `${s.reps}×${s.weight}`).join(" , ")}
                  </p>
                ))}

                <button
                  onClick={() => deleteWorkout(w.id)}
                  className="mt-3 text-sm text-white/50 hover:text-red-400"
                >
                  מחק אימון
                </button>
              </div>
            ))
          )}
        </div>
      )}
    </main>
  );
}