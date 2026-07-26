"use client";
import { useState, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

type Point = { date: string; est_1rm: number };
type Lift = { name: string; best_1rm: number | null; slope: number | null; points: Point[] };
type Progress = { lifts: Lift[]; total: number | null };
type Profile = { sex: string | null; age: number | null; bodyweight: number | null };

const API = "/api/backend";

export default function PowerliftingPage() {
  const [data, setData] = useState<Progress>({ lifts: [], total: null });
  const [profile, setProfile] = useState<Profile>({ sex: null, age: null, bodyweight: null });
  const [error, setError] = useState("");
  const [saveMsg, setSaveMsg] = useState("");

  // תשובות הסוכן לפי מפתח - כל כפתור שומר את התשובה שלו בנפרד
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);

  const loadProgress = useCallback(() => {
    fetch(`${API}/powerlifting/progress`)
      .then(res => {
        if (!res.ok) throw new Error(`שגיאה ${res.status}`);
        return res.json();
      })
      .then(setData)
      .catch(e => setError(String(e)));
  }, []);

  useEffect(() => {
    loadProgress();
    fetch(`${API}/profile`).then(res => res.json()).then(setProfile).catch(() => {});
  }, [loadProgress]);

  async function saveProfile() {
    if (profile.age === null || profile.bodyweight === null) {
      setSaveMsg("חובה להזין גיל ומשקל גוף");
      return;
    }
    try {
      await fetch(`${API}/profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      });
      setSaveMsg("הפרופיל נשמר");
      setTimeout(() => setSaveMsg(""), 2000);
    } catch {
      setSaveMsg("שגיאה בשמירה");
    }
  }

  // שאלת הסוכן . ההקשר (פרופיל + יומן) נבנה בשרת - שולחים רק את השאלה
  async function ask(key: string, question: string) {
    if (profile.age === null) {
      setAnswers(prev => ({ ...prev, [key]: "צריך לשמור פרופיל קודם" }));
      return;
    }
    setBusy(key);
    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const json = await res.json();
      setAnswers(prev => ({ ...prev, [key]: json.answer }));
    } catch (e) {
      setAnswers(prev => ({ ...prev, [key]: `שגיאה: ${e}` }));
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="text-2xl font-bold">פאוורליפטינג</h1>
      <p className="mt-1 text-sm text-white/50">
        הנתונים כאן נשלפים אוטומטית מיומן האימונים. כל סט של סקוואט, בנץ או דדליפט שנשמר ביומן מופיע כאן
      </p>

      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}

      {/* ===== פרופיל ===== */}
      <div className="mt-6 rounded-lg border border-white/10 p-4">
        <h2 className="font-bold">הפרופיל שלי</h2>

        <div className="mt-3 flex flex-wrap items-end gap-3">
          <div>
            <label className="mb-1 block text-xs text-white/50">מגדר</label>
            <div className="flex gap-2">
              {["זכר", "נקבה"].map(s => (
                <button
                  key={s}
                  onClick={() => setProfile({ ...profile, sex: s })}
                  className={
                    profile.sex === s
                      ? "rounded-lg bg-blue-600 px-3 py-1.5 text-sm"
                      : "rounded-lg bg-white/5 px-3 py-1.5 text-sm"
                  }
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="mb-1 block text-xs text-white/50">גיל</label>
            <input
              type="number"
              value={profile.age ?? ""}
              onChange={e => setProfile({ ...profile, age: e.target.value === "" ? null : Number(e.target.value) })}
              className="w-24 rounded-lg border border-white/10 bg-white/5 px-2 py-1.5 text-sm outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs text-white/50">משקל גוף (ק״ג)</label>
            <input
              type="number" step={0.5}
              value={profile.bodyweight ?? ""}
              onChange={e => setProfile({ ...profile, bodyweight: e.target.value === "" ? null : Number(e.target.value) })}
              className="w-28 rounded-lg border border-white/10 bg-white/5 px-2 py-1.5 text-sm outline-none focus:border-blue-500"
            />
          </div>

          <button onClick={saveProfile} className="rounded-lg bg-blue-600 px-4 py-1.5 text-sm">
            שמור פרופיל
          </button>
          {saveMsg && <span className="text-sm text-white/60">{saveMsg}</span>}
        </div>
      </div>

      {/* ===== שלושת הליפטים ===== */}
      {data.lifts.map(lift => {
        const compareKey = `compare_${lift.name}`;
        const predictKey = `predict_${lift.name}`;

        return (
          <section key={lift.name} className="mt-8">
            <h2 className="text-lg font-bold">{lift.name}</h2>

            {lift.best_1rm === null ? (
              <p className="mt-2 text-sm text-white/50">עדיין אין אימוני {lift.name} ביומן</p>
            ) : (
              <>
                <div className="mt-3 flex gap-3">
                  <div className="flex-1 rounded-lg bg-white/5 p-3">
                    <div className="text-xs text-white/50">שיא משוער (1RM)</div>
                    <div className="mt-1 text-xl font-bold">{lift.best_1rm.toFixed(1)} ק״ג</div>
                  </div>
                  <div className="flex-1 rounded-lg bg-white/5 p-3">
                    <div className="text-xs text-white/50">קצב אישי</div>
                    <div className="mt-1 text-xl font-bold">
                      {lift.slope !== null
                        ? `${lift.slope > 0 ? "+" : ""}${lift.slope.toFixed(2)} ק״ג/חודש`
                        : <span className="text-sm font-normal text-white/50">צריך עוד אימונים</span>}
                    </div>
                  </div>
                </div>

                {/* הגרף ב-LTR . ציר זמן נקרא משמאל לימין גם בעברית */}
                {lift.points.length > 1 && (
                  <div dir="ltr" className="mt-4 h-56 w-full">
                    <ResponsiveContainer>
                      <LineChart data={lift.points} margin={{ top: 8, right: 16, bottom: 0, left: -16 }}>
                        <CartesianGrid stroke="#ffffff18" />
                        <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#ffffff80" }} />
                        <YAxis tick={{ fontSize: 11, fill: "#ffffff80" }} domain={["auto", "auto"]} />
                        <Tooltip
                          contentStyle={{ background: "#1c1f2b", border: "1px solid #ffffff20", borderRadius: 8 }}
                          labelStyle={{ color: "#ffffffcc" }}
                        />
                        <Line
                          type="monotone" dataKey="est_1rm"
                          stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }}
                          name="1RM"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}

                <div className="mt-4 flex gap-2">
                  <button
                    onClick={() => ask(compareKey,
                      `אני מרים ${lift.best_1rm!.toFixed(0)} קג ב${lift.name} (1RM משוער). איפה אני עומד ביחס לאחרים?`)}
                    disabled={busy !== null}
                    className="flex-1 rounded-lg bg-white/10 px-4 py-2 text-sm disabled:opacity-50"
                  >
                    {busy === compareKey ? "בודק..." : `השווה אותי לאחרים`}
                  </button>
                  <button
                    onClick={() => ask(predictKey,
                      `אני מרים ${lift.best_1rm!.toFixed(0)} קג ב${lift.name}. מה קצב ההתקדמות הצפוי שלי?`)}
                    disabled={busy !== null}
                    className="flex-1 rounded-lg bg-white/10 px-4 py-2 text-sm disabled:opacity-50"
                  >
                    {busy === predictKey ? "מחשב..." : "חזה את הקצב שלי"}
                  </button>
                </div>

                {answers[compareKey] && (
                  <div className="prose prose-sm prose-invert mt-3 max-w-none rounded-lg bg-white/5 p-3">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{answers[compareKey]}</ReactMarkdown>
                  </div>
                )}

                {answers[predictKey] && (
                  <div className="mt-3 rounded-lg bg-white/5 p-3">
                    <div className="prose prose-sm prose-invert max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{answers[predictKey]}</ReactMarkdown>
                    </div>
                    {lift.slope !== null && (
                      <p className="mt-3 rounded-lg bg-blue-500/10 p-2 text-sm text-blue-200">
                        לפי היומן שלך, הקצב האמיתי שלך כרגע הוא {lift.slope > 0 ? "+" : ""}
                        {lift.slope.toFixed(2)} ק״ג לחודש
                      </p>
                    )}
                  </div>
                )}
              </>
            )}
          </section>
        );
      })}

      {/* ===== טוטאל ===== */}
      {data.total !== null && (
        <section className="mt-8 border-t border-white/10 pt-6">
          <h2 className="text-lg font-bold">טוטאל</h2>
          <div className="mt-3 rounded-lg bg-white/5 p-3">
            <div className="text-xs text-white/50">סכום שלושת השיאים</div>
            <div className="mt-1 text-xl font-bold">{data.total.toFixed(1)} ק״ג</div>
          </div>

          <button
            onClick={() => ask("total",
              `הטוטאל שלי הוא ${data.total!.toFixed(0)} קג. איפה אני עומד ביחס לאחרים?`)}
            disabled={busy !== null}
            className="mt-3 w-full rounded-lg bg-white/10 px-4 py-2 text-sm disabled:opacity-50"
          >
            {busy === "total" ? "בודק..." : "השווה את הטוטאל שלי לאחרים"}
          </button>

          {answers["total"] && (
            <div className="prose prose-sm prose-invert mt-3 max-w-none rounded-lg bg-white/5 p-3">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{answers["total"]}</ReactMarkdown>
            </div>
          )}
        </section>
      )}
    </main>
  );
}