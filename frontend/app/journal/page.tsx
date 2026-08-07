"use client";
import { useState, useEffect, useCallback } from "react";

type WorkoutSet = { reps: number; weight: number };
type Exercise = { name: string; sets: WorkoutSet[] };
type Workout = {
  id: number;
  date: string;
  workout_type: string;
  exercises: Exercise[];
};

// טיוטת תרגיל בטופס - נושאת גם את שדות הקלט שלה
type DraftExercise = Exercise & {
  numSets: number;
  reps: number;
  weight: number;
};

const HEBREW_MONTHS = [
  "ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני",
  "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר",
];

const WEEKDAYS = ["א", "ב", "ג", "ד", "ה", "ו", "ש"];

const WORKOUT_TYPES = ["רגליים", "חזה", "גב", "כתפיים", "ידיים", "גוף מלא"];

// שלושת הראשונים הם תרגילי הפאוורליפטינג - אסור לשנות את האיות
const BASE_EXERCISES = [
  "סקוואט", "בנץ", "דדליפט",
  "לחיצת רגליים", "לחיצת כתפיים", "עליות מתח", "חתירה",
  "פולי עליון", "לחיצת חזה בשיפוע", "כפיפת מרפקים", "פשיטת מרפקים",
  "לאנג׳ים", "כפיפת ברכיים", "הרחקות כתף", "בטן",
];

// צבעי דיסקיות מכוילות - כל סוג אימון מקבל משקל
const TYPE_COLORS: Record<string, string> = {
  "רגליים": "#F5B301", // 15 ק"ג
  "חזה": "#C4342E", // 25
  "גב": "#1F5FA8", // 20
  "כתפיים": "#2E8B57", // 10
  "ידיים": "#E9E4DA", // 5
  "גוף מלא": "#9AA0A6", // כרום
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

const dayMonth = new Intl.DateTimeFormat("he-IL", {
  day: "numeric",
  month: "long",
});

// "2026-07-17" -> "17 ביולי"
function prettyDate(key: string) {
  const [y, m, d] = key.split("-").map(Number);
  if (!y || !m || !d) return key;
  return dayMonth.format(new Date(y, m - 1, d));
}

export default function JournalPage() {
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [names, setNames] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [booting, setBooting] = useState(true);
  const [selected, setSelected] = useState<string | null>(null);
  const [confirmId, setConfirmId] = useState<number | null>(null);
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
  const [notice, setNotice] = useState<{ text: string; ok: boolean } | null>(null);
  const [lastWorkout, setLastWorkout] = useState<Workout | null>(null);

  const loadWorkouts = useCallback(() => {
    fetch(`${API}/workouts/full`)
      .then((res) => {
        if (!res.ok) throw new Error();
        return res.json();
      })
      .then((data) => {
        setWorkouts(Array.isArray(data) ? data : []);
        setError("");
      })
      .catch(() => setError("לא הצלחתי לטעון את האימונים. בדוק שהשרת פועל."))
      .finally(() => setBooting(false));
  }, []);

  const loadNames = useCallback(() => {
    fetch(`${API}/exercises/names`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setNames(Array.isArray(data) ? data : []))
      .catch(() => setNames([]));
  }, []);

// האימון האחרון מהסוג הנבחר שקדם לתאריך בטופס. 404 הוא תשובה תקינה - אין אימון כזה
  const loadLast = useCallback((type: string, before: string) => {
    fetch(`${API}/workouts/last/${encodeURIComponent(type)}?before=${before}`)
      .then((res) => (res.ok ? res.json() : null))
      .then(setLastWorkout)
      .catch(() => setLastWorkout(null));
  }, []);

  useEffect(() => {
    loadWorkouts();
    loadNames();
  }, [loadWorkouts, loadNames]);

  useEffect(() => {
    loadLast(wType, wDate);
  }, [wType, wDate, loadLast]);


  // איחוד הרשימה הבסיסית עם תרגילים שהוזנו ידנית בעבר
  const exerciseList = [
    ...BASE_EXERCISES,
    ...names.filter((n) => !BASE_EXERCISES.includes(n)),
    "אחר",
  ];

  function updateDraft(i: number, patch: Partial<DraftExercise>) {
    setDraft((prev) => prev.map((ex, j) => (j === i ? { ...ex, ...patch } : ex)));
  }

  function addExercise() {
    const name = pick === "אחר" ? customName.trim() : pick;
    if (!name) {
      setNotice({ text: "צריך לבחור או להקליד שם תרגיל", ok: false });
      return;
    }
    if (draft.length === 0) setStartedDate(wDate);
    setDraft((prev) => [
      ...prev,
      { name, sets: [], numSets: 1, reps: 8, weight: 50 },
    ]);
    setCustomName("");
    setNotice(null);
  }

  function duplicateLast() {
    if (!lastWorkout) return;
    if (draft.length > 0) {
      setNotice({ text: "יש כבר תרגילים בטופס. נקה קודם כדי לשכפל", ok: false });
      return;
    }
    setStartedDate(wDate);
    setDraft(
      lastWorkout.exercises.map((ex) => ({
        name: ex.name,
        sets: ex.sets.map((s) => ({ ...s })), // עותק ולא הפניה למקור
        numSets: 1,
        reps: 8,
        weight: 50,
      })),
    );
    setNotice(null);
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
    setDraft((prev) => prev.filter((_, j) => j !== i));
  }

  function clearForm() {
    setDraft([]);
    setStartedDate(null);
    setNotice(null);
  }

  async function saveWorkout() {
    const empty = draft.filter((ex) => ex.sets.length === 0).map((ex) => ex.name);
    if (empty.length > 0) {
      setNotice({ text: `יש תרגילים בלי סטים: ${empty.join(", ")}`, ok: false });
      return;
    }

    setSaving(true);
    setNotice(null);
    try {
      const res = await fetch(`${API}/workouts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          date: wDate,
          workout_type: wType,
          exercises: draft.map((ex) => ({ name: ex.name, sets: ex.sets })),
        }),
      });
      if (!res.ok) throw new Error();
      clearForm();
      setNotice({ text: "האימון נשמר", ok: true });
      loadWorkouts();
      loadNames();
      loadLast(wType, wDate); // כדי שכפתור השכפול יציע את החדש ולא את הקודם
    } catch {
      setNotice({ text: "השמירה נכשלה. נסה שוב", ok: false });
    } finally {
      setSaving(false);
    }
  }

  async function deleteWorkout(id: number) {
    try {
      const res = await fetch(`${API}/workouts/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error();
      setConfirmId(null);
      setSelected(null);
      loadWorkouts();
      loadLast(wType, wDate);
    } catch {
      setError("המחיקה נכשלה. נסה שוב");
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
    setView((prev) => {
      const d = new Date(prev.year, prev.month + delta, 1);
      return { year: d.getFullYear(), month: d.getMonth() };
    });
  }

  const selectedWorkouts = selected ? (byDate[selected] ?? []) : [];
  const dateChanged =
    draft.length > 0 && startedDate !== null && startedDate !== wDate;

  // אילו סוגי אימון מופיעים בחודש המוצג - למקרא
  const typesThisMonth = new Set<string>();
  for (const [key, list] of Object.entries(byDate)) {
    if (key.startsWith(`${view.year}-${String(view.month + 1).padStart(2, "0")}`)) {
      list.forEach((w) => typesThisMonth.add(w.workout_type));
    }
  }

  return (
    <div className="page">
      <div className="mb-8">
        <p className="eyebrow">היומן</p>
        <h1 className="mt-1">יומן אימונים</h1>
      </div>

      {error && (
        <p className="mb-6 rounded-card border border-bad/35 bg-bad/8 px-4 py-3 text-sm">
          {error}
        </p>
      )}

      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)] lg:gap-10">
        {/* ═══ אימון חדש ═══════════════════════════════════ */}
        <section>
          <h2 className="mb-4">אימון חדש</h2>

          <div className="flex gap-3">
            <div className="flex-1">
              <label className="label" htmlFor="wdate">תאריך</label>
              <input
                id="wdate"
                type="date"
                value={wDate}
                onChange={(e) => setWDate(e.target.value)}
                className="field field-num"
              />
            </div>
            <div className="flex-1">
              <label className="label" htmlFor="wtype">סוג אימון</label>
              <select
                id="wtype"
                value={wType}
                onChange={(e) => setWType(e.target.value)}
                className="field"
              >
                {WORKOUT_TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
          </div>

          {dateChanged && (
            <p className="mt-3 rounded-card border border-accent/30 bg-accent/8 px-4 py-3 text-[0.8rem] leading-relaxed">
              התחלת את הטופס ב־{prettyDate(startedDate!)} ועכשיו נבחר{" "}
              {prettyDate(wDate)}. כל התרגילים יישמרו יחד בתאריך החדש. אם
              התכוונת לאימון נפרד — שמור או נקה את הטופס קודם.
            </p>
          )}

          {lastWorkout && draft.length === 0 && (
            <button onClick={duplicateLast} className="btn btn-secondary mt-3 w-full">
              שכפל אימון {wType} מ־{prettyDate(lastWorkout.date)}
            </button>
          )}

          {/* הוספת תרגיל */}
          <div className="mt-6 flex flex-wrap gap-2">
            <select
              value={pick}
              onChange={(e) => setPick(e.target.value)}
              className="field flex-1"
              aria-label="בחר תרגיל"
            >
              {exerciseList.map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
            {pick === "אחר" && (
              <input
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
                placeholder="שם התרגיל"
                className="field flex-1"
              />
            )}
            <button onClick={addExercise} className="btn btn-secondary">
              הוסף תרגיל
            </button>
          </div>

          {/* טיוטה - האחרון שנוסף מוצג ראשון */}
          {draft.length === 0 ? (
            <div className="empty mt-4">
              <p className="text-sm">עוד לא הוספת תרגילים לאימון הזה.</p>
            </div>
          ) : (
            <div className="mt-4 space-y-3">
              {draft
                .map((ex, i) => ({ ex, i }))
                .reverse()
                .map(({ ex, i }) => (
                  <div key={i} className="card">
                    <div className="flex items-start justify-between gap-3">
                      <h3>{ex.name}</h3>
                      <button
                        onClick={() => removeExercise(i)}
                        className="btn btn-ghost h-8 min-h-0 px-2 text-[0.75rem]"
                      >
                        הסר
                      </button>
                    </div>

                    {ex.sets.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {ex.sets.map((s, j) => (
                          <button
                            key={j}
                            onClick={() => removeSet(i, j)}
                            title="הסר סט"
                            className="group flex items-center gap-1.5 rounded-control border border-line-strong px-2.5 py-1 text-[0.8rem] transition-colors hover:border-bad hover:text-bad"
                          >
                            <span className="num">{s.reps}×{s.weight}</span>
                            <span className="text-faint group-hover:text-bad">✕</span>
                          </button>
                        ))}
                      </div>
                    )}

                    <div className="mt-3 flex items-end gap-2">
                      <div className="flex-1">
                        <label className="label text-[0.7rem]">סטים</label>
                        <input
                          type="number" min={1} max={15} value={ex.numSets}
                          onChange={(e) => updateDraft(i, { numSets: Number(e.target.value) })}
                          className="field field-num h-10 min-h-0 text-sm"
                        />
                      </div>
                      <div className="flex-1">
                        <label className="label text-[0.7rem]">חזרות</label>
                        <input
                          type="number" min={1} max={100} value={ex.reps}
                          onChange={(e) => updateDraft(i, { reps: Number(e.target.value) })}
                          className="field field-num h-10 min-h-0 text-sm"
                        />
                      </div>
                      <div className="flex-1">
                        <label className="label text-[0.7rem]">משקל</label>
                        <input
                          type="number" min={0} max={600} step={2.5} value={ex.weight}
                          onChange={(e) => updateDraft(i, { weight: Number(e.target.value) })}
                          className="field field-num h-10 min-h-0 text-sm"
                        />
                      </div>
                      <button
                        onClick={() => addSets(i)}
                        className="btn btn-secondary h-10 min-h-0 px-3 text-sm"
                      >
                        הוסף
                      </button>
                    </div>
                  </div>
                ))}
            </div>
          )}

          {draft.length > 0 && (
            <div className="mt-4 flex gap-2">
              <button
                onClick={saveWorkout}
                disabled={saving}
                className="btn btn-primary flex-1"
              >
                {saving ? "שומר…" : "שמור אימון"}
              </button>
              <button onClick={clearForm} className="btn btn-ghost">
                נקה טופס
              </button>
            </div>
          )}

          {notice && (
            <p
              role="status"
              className={`mt-3 text-sm ${notice.ok ? "text-good" : "text-bad"}`}
            >
              {notice.text}
            </p>
          )}
        </section>

        {/* ═══ היסטוריה ════════════════════════════════════ */}
        <section>
          <h2 className="mb-4">היסטוריה</h2>

          <div className="card">
            <div className="flex items-center justify-between">
              <button
                onClick={() => shiftMonth(-1)}
                className="btn btn-ghost h-9 min-h-0 px-3 text-sm"
                aria-label="החודש הקודם"
              >
                ‹
              </button>
              <h3 className="font-semibold">
                {HEBREW_MONTHS[view.month]} <span className="num">{view.year}</span>
              </h3>
              <button
                onClick={() => shiftMonth(1)}
                className="btn btn-ghost h-9 min-h-0 px-3 text-sm"
                aria-label="החודש הבא"
              >
                ›
              </button>
            </div>

            <div className="mt-4 grid grid-cols-7 gap-1">
              {WEEKDAYS.map((d) => (
                <div key={d} className="pb-1.5 text-center text-[0.7rem] font-semibold text-faint">
                  {d}
                </div>
              ))}

              {Array.from({ length: firstWeekday }, (_, i) => <div key={`pad-${i}`} />)}

              {Array.from({ length: daysInMonth }, (_, i) => {
                const day = i + 1;
                const key = dateKey(view.year, view.month, day);
                const list = byDate[key] ?? [];
                const isSel = key === selected;
                const isToday = key === today;

                return (
                  <button
                    key={key}
                    onClick={() => {
                      setSelected(isSel ? null : key);
                      setConfirmId(null);
                    }}
                    aria-label={`${day} ${HEBREW_MONTHS[view.month]}${list.length ? ", יש אימון" : ""}`}
                    className={[
                      "relative flex aspect-square flex-col items-center justify-center gap-1 rounded-control text-sm transition-colors",
                      isSel
                        ? "bg-accent font-semibold text-on-accent"
                        : list.length
                          ? "bg-raised font-medium text-ink hover:bg-line"
                          : "bg-surface text-muted hover:bg-raised",
                      isToday && !isSel ? "ring-1 ring-inset ring-accent/60" : "",
                    ].join(" ")}
                  >
                    <span className="num leading-none">{day}</span>
                    {list.length > 0 && (
                      <span className="flex gap-0.5">
                        {list.slice(0, 3).map((w, k) => (
                          <span
                            key={k}
                            className="h-1.5 w-1.5 rounded-full"
                            style={{
                              background: isSel
                                ? "rgba(23,19,11,.55)"
                                : (TYPE_COLORS[w.workout_type] ?? "#9AA0A6"),
                            }}
                          />
                        ))}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            {/* מקרא - רק סוגים שבאמת מופיעים החודש */}
            {typesThisMonth.size > 0 && (
              <div className="mt-4 flex flex-wrap gap-x-3 gap-y-1.5 border-t border-line pt-3">
                {WORKOUT_TYPES.filter((t) => typesThisMonth.has(t)).map((t) => (
                  <span key={t} className="flex items-center gap-1.5 text-[0.7rem] text-muted">
                    <span
                      className="h-1.5 w-1.5 rounded-full"
                      style={{ background: TYPE_COLORS[t] }}
                    />
                    {t}
                  </span>
                ))}
                <span className="flex items-center gap-1.5 text-[0.7rem] text-faint">
                  <span className="h-2.5 w-2.5 rounded-[3px] ring-1 ring-accent/60" />
                  היום
                </span>
              </div>
            )}
          </div>

          {/* פירוט היום הנבחר */}
          <div className="mt-4">
            {booting ? (
              <div className="skeleton h-28 w-full" />
            ) : workouts.length === 0 ? (
              <div className="empty">
                <p className="text-sm">אין עדיין אימונים ביומן.</p>
                <p className="mt-1 text-[0.8rem] text-faint">
                  שמור את הראשון והוא יופיע כאן.
                </p>
              </div>
            ) : !selected ? (
              <p className="px-1 text-[0.8rem] text-faint">
                בחר יום בלוח כדי לראות מה עשית בו.
              </p>
            ) : selectedWorkouts.length === 0 ? (
              <div className="empty">
                <p className="text-sm">אין אימון ב־{prettyDate(selected)}.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {selectedWorkouts.map((w) => (
                  <div key={w.id} className="card">
                    <div className="mb-3 flex items-center gap-3">
                      <span
                        className="rounded-full px-2.5 py-0.5 text-[0.775rem] font-semibold"
                        style={{
                          background: TYPE_COLORS[w.workout_type] ?? "#9AA0A6",
                          color: "#17130B",
                        }}
                      >
                        {w.workout_type}
                      </span>
                      <span className="text-[0.8rem] text-muted">
                        {prettyDate(w.date)}
                      </span>
                    </div>

                    <div className="space-y-1.5">
                      {w.exercises.map((ex, i) => (
                        <p key={i} className="text-[0.875rem]">
                          <span className="font-semibold">{ex.name}</span>
                          <span className="text-faint"> · </span>
                          <span className="num text-muted">
                            {ex.sets.map((s) => `${s.reps}×${s.weight}`).join("  ")}
                          </span>
                        </p>
                      ))}
                    </div>

                    {confirmId === w.id ? (
                      <div className="mt-4 flex items-center gap-2 border-t border-line pt-3">
                        <span className="flex-1 text-[0.8rem] text-muted">
                          למחוק את האימון?
                        </span>
                        <button
                          onClick={() => deleteWorkout(w.id)}
                          className="btn btn-danger h-8 min-h-0 px-3 text-[0.775rem]"
                        >
                          כן, מחק
                        </button>
                        <button
                          onClick={() => setConfirmId(null)}
                          className="btn btn-ghost h-8 min-h-0 px-3 text-[0.775rem]"
                        >
                          ביטול
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setConfirmId(w.id)}
                        className="btn btn-ghost mt-3 h-8 min-h-0 px-2 text-[0.775rem]"
                      >
                        מחק אימון
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}