"use client";
import { useState, useEffect } from "react";

type WorkoutSet = { reps: number; weight: number };
type Exercise = { name: string; sets: WorkoutSet[] };
type Workout = { id: number; date: string; workout_type: string; exercises: Exercise[] };

const HEBREW_MONTHS = ["ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני",
  "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"];

// סדר טבעי - dir="rtl" יסדר אותם מימין לשמאל לבד
const WEEKDAYS = ["א", "ב", "ג", "ד", "ה", "ו", "ש"];

const TYPE_COLORS: Record<string, string> = {
  "רגליים": "#F2B705",
  "חזה": "#2DD4BF",
  "גב": "#818CF8",
  "כתפיים": "#FB7185",
  "ידיים": "#34D399",
  "גוף מלא": "#F472B6",
};

// YYYY-MM-DD בזמן מקומי. toISOString היה מזיז יום אחורה בגלל UTC
function dateKey(year: number, month: number, day: number) {
  return `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

export default function JournalPage() {
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [view, setView] = useState(() => {
    const t = new Date();
    return { year: t.getFullYear(), month: t.getMonth() };
  });

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/workouts/full`)
      .then(res => {
        if (!res.ok) throw new Error(`שגיאה ${res.status}`);
        return res.json();
      })
      .then(setWorkouts)
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  // קיבוץ לפי תאריך - מחושב מחדש בכל רינדור, זה זול
  const byDate: Record<string, Workout[]> = {};
  for (const w of workouts) {
    (byDate[w.date] ??= []).push(w);
  }

  const firstWeekday = new Date(view.year, view.month, 1).getDay();   // 0 = ראשון
  const daysInMonth = new Date(view.year, view.month + 1, 0).getDate();

  const now = new Date();
  const todayKey = dateKey(now.getFullYear(), now.getMonth(), now.getDate());

  function shiftMonth(delta: number) {
    setSelected(null);
    setView(prev => {
      const d = new Date(prev.year, prev.month + delta, 1);
      return { year: d.getFullYear(), month: d.getMonth() };
    });
  }

  const selectedWorkouts = selected ? byDate[selected] ?? [] : [];

  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="text-2xl font-bold">יומן אימונים</h1>

      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
      {loading && <p className="mt-4 text-sm text-white/50">טוען...</p>}

      <div className="mt-6 flex items-center justify-between">
        <button onClick={() => shiftMonth(-1)} className="rounded-lg bg-white/5 px-4 py-2">
          ‹ הקודם
        </button>
        <h2 className="text-lg font-bold">
          {HEBREW_MONTHS[view.month]} {view.year}
        </h2>
        <button onClick={() => shiftMonth(1)} className="rounded-lg bg-white/5 px-4 py-2">
          הבא ›
        </button>
      </div>

      <div className="mt-4 grid grid-cols-7 gap-1">
        {WEEKDAYS.map(d => (
          <div key={d} className="pb-1 text-center text-sm font-bold text-white/50">
            {d}
          </div>
        ))}

        {Array.from({ length: firstWeekday }, (_, i) => <div key={`pad-${i}`} />)}

        {Array.from({ length: daysInMonth }, (_, i) => {
          const day = i + 1;
          const key = dateKey(view.year, view.month, day);
          const hasWorkout = key in byDate;
          const isToday = key === todayKey;
          const isSelected = key === selected;

          return (
            <button
              key={key}
              onClick={() => setSelected(isSelected ? null : key)}
              className={[
                "aspect-square rounded-lg text-sm transition",
                hasWorkout ? "bg-blue-600/80 font-bold" : "bg-white/5",
                isSelected ? "ring-2 ring-white/60" : "",
                isToday && !isSelected ? "ring-1 ring-white/30" : "",
              ].join(" ")}
            >
              {day}
              {hasWorkout && <span className="block text-[10px] leading-none">🔥</span>}
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
              </div>
            ))
          )}
        </div>
      )}
    </main>
  );
}