"use client";
import { useState, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import ProfileCard, { type Profile } from "../components/ProfileCard";

type Point = { date: string; est_1rm: number };
type Lift = {
  name: string;
  best_1rm: number | null;
  slope: number | null;
  points: Point[];
};
type Progress = { lifts: Lift[]; total: number | null };

const API = "/api/backend";

// טוקנים מ-globals.css. Recharts דורש ערכים ממשיים ולא var()
const C = {
  accent: "#F5B301",
  grid: "#332E28",
  axis: "#A69C8E",
  surface: "#1C1916",
  line: "#453E36",
  ink: "#F5F1EA",
};

// "2026-07-17" -> "17.7"
function shortDate(d: string) {
  const [, m, day] = d.split("-");
  return m && day ? `${Number(day)}.${Number(m)}` : d;
}

export default function PowerliftingPage() {
  const [data, setData] = useState<Progress>({ lifts: [], total: null });
  const [profile, setProfile] = useState<Profile>({
    sex: null, age: null, bodyweight: null,
  });
  const [error, setError] = useState("");
  const [booting, setBooting] = useState(true);

  // תשובות הסוכן לפי מפתח - כל כפתור שומר את התשובה שלו בנפרד
  const [answers, setAnswers] = useState<Record<string, { text: string; error?: boolean }>>({});
  const [busy, setBusy] = useState<string | null>(null);

  const loadProgress = useCallback(() => {
    fetch(`${API}/powerlifting/progress`)
      .then((res) => {
        if (!res.ok) throw new Error();
        return res.json();
      })
      .then((json) => {
        setData({
          lifts: Array.isArray(json?.lifts) ? json.lifts : [],
          total: json?.total ?? null,
        });
        setError("");
      })
      .catch(() => setError("לא הצלחתי לטעון את הנתונים. בדוק שהשרת פועל."))
      .finally(() => setBooting(false));
  }, []);

  useEffect(() => {
    loadProgress();
  }, [loadProgress]);

  // ההקשר (פרופיל + יומן) נבנה בשרת - שולחים רק את השאלה
  async function ask(key: string, question: string) {
    if (profile.age === null || profile.bodyweight === null) {
      setAnswers((p) => ({
        ...p,
        [key]: { text: "שמור קודם גיל ומשקל גוף בפרופיל למעלה.", error: true },
      }));
      return;
    }
    setBusy(key);
    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!res.ok) throw new Error();
      const json = await res.json();
      setAnswers((p) => ({ ...p, [key]: { text: json.answer } }));
    } catch {
      setAnswers((p) => ({
        ...p,
        [key]: { text: "לא הצלחתי להגיע לסוכן. נסה שוב.", error: true },
      }));
    } finally {
      setBusy(null);
    }
  }

  const withData = data.lifts.filter((l) => l.best_1rm !== null);

  return (
    <div className="page">
      <div className="mb-6">
        <p className="eyebrow">הביצועים</p>
        <h1 className="mt-1">פאוורליפטינג</h1>
        <p className="lede mt-2 max-w-xl text-[0.9rem]">
          כל סט של סקוואט, בנץ או דדליפט שנשמר ביומן נספר כאן אוטומטית.
        </p>
      </div>

      {error && (
        <p className="mb-6 rounded-card border border-bad/35 bg-bad/8 px-4 py-3 text-sm">
          {error}
        </p>
      )}

      <ProfileCard variant="row" onChange={setProfile} />

      {/* ═══ טוטאל — המספר של הענף ═══════════════════════ */}
      {booting ? (
        <div className="skeleton mt-6 h-40 w-full" />
      ) : data.total === null ? (
        <div className="empty mt-6">
          <p className="text-sm">עוד אין נתוני פאוורליפטינג.</p>
          <p className="mt-1 text-[0.8rem] text-faint">
            שמור ביומן אימון עם סקוואט, בנץ או דדליפט והמספרים יופיעו כאן.
          </p>
        </div>
      ) : (
        <section className="card-raised mt-6">
          <p className="eyebrow">טוטאל · סכום שלושת השיאים</p>
          <p className="stat-value is-record mt-2">
            {data.total.toFixed(1)}
            <span className="stat-unit">ק״ג</span>
          </p>

          {/* רצועת לוח תוצאות */}
          {withData.length > 0 && (
            <div className="mt-5 grid grid-cols-3 gap-px overflow-hidden rounded-control bg-line">
              {withData.map((l) => (
                <div key={l.name} className="bg-surface px-3 py-2.5 text-center">
                  <p className="text-[0.7rem] text-faint">{l.name}</p>
                  <p className="num mt-0.5 text-lg font-semibold">
                    {l.best_1rm!.toFixed(1)}
                  </p>
                </div>
              ))}
            </div>
          )}

          <button
            onClick={() =>
              ask("total", `הטוטאל שלי הוא ${data.total!.toFixed(0)} קג. איפה אני עומד ביחס לאחרים?`)
            }
            disabled={busy !== null}
            className="btn btn-primary mt-5 w-full"
          >
            {busy === "total" ? "בודק…" : "השווה את הטוטאל שלי לאחרים"}
          </button>

          <AgentAnswer answer={answers["total"]} />
        </section>
      )}

      {/* ═══ שלושת הליפטים ═══════════════════════════════ */}
      {data.lifts.map((lift) => {
        const compareKey = `compare_${lift.name}`;
        const predictKey = `predict_${lift.name}`;
        const up = (lift.slope ?? 0) > 0;

        return (
          <section key={lift.name} className="mt-10">
            <div className="mb-4 flex items-baseline gap-3">
              <h2>{lift.name}</h2>
              <span className="h-px flex-1 bg-line" />
            </div>

            {lift.best_1rm === null ? (
              <div className="empty">
                <p className="text-sm">עדיין אין אימוני {lift.name} ביומן.</p>
              </div>
            ) : (
              <>
                <div className="flex flex-col gap-3 sm:flex-row">
                  <div className="stat flex-1">
                    <p className="stat-label">שיא משוער · 1RM</p>
                    <p className="stat-value mt-1 !text-[2rem]">
                      {lift.best_1rm.toFixed(1)}
                      <span className="stat-unit">ק״ג</span>
                    </p>
                  </div>
                  <div className="stat flex-1">
                    <p className="stat-label">קצב אישי</p>
                    {lift.slope !== null ? (
                      <p
                        className={`num mt-2 text-2xl font-semibold ${up ? "text-accent" : "text-bad"}`}
                      >
                        {up ? "+" : ""}
                        {lift.slope.toFixed(2)}
                        <span className="stat-unit">ק״ג לחודש</span>
                      </p>
                    ) : (
                      <p className="mt-2.5 text-sm text-muted">
                        צריך עוד אימונים כדי לחשב מגמה
                      </p>
                    )}
                  </div>
                </div>

                {/* הגרף ב-LTR. ציר זמן נקרא משמאל לימין גם בעברית */}
                {lift.points.length > 1 && (
                  <div dir="ltr" className="card mt-3 h-60 w-full !px-2 !py-4">
                    <ResponsiveContainer>
                      <LineChart
                        data={lift.points}
                        margin={{ top: 8, right: 16, bottom: 0, left: -18 }}
                      >
                        <CartesianGrid stroke={C.grid} vertical={false} />
                        <XAxis
                          dataKey="date"
                          tickFormatter={shortDate}
                          tick={{ fontSize: 11, fill: C.axis }}
                          tickLine={false}
                          axisLine={{ stroke: C.grid }}
                        />
                        <YAxis
                          tick={{ fontSize: 11, fill: C.axis }}
                          tickLine={false}
                          axisLine={false}
                          domain={["auto", "auto"]}
                          width={44}
                        />
                        <Tooltip
                          contentStyle={{
                            background: C.surface,
                            border: `1px solid ${C.line}`,
                            borderRadius: 10,
                            fontSize: 13,
                          }}
                          labelStyle={{ color: C.axis }}
                          itemStyle={{ color: C.ink }}
                          labelFormatter={(label) => shortDate(String(label))}
                          formatter={(value) => [`${Number(value).toFixed(1)} kg`, "1RM"] as [string, string]}
                        />
                        <Line
                          type="monotone"
                          dataKey="est_1rm"
                          stroke={C.accent}
                          strokeWidth={2.5}
                          dot={{ r: 3, fill: C.accent, strokeWidth: 0 }}
                          activeDot={{ r: 5, fill: C.accent, strokeWidth: 0 }}
                          name="1RM"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}

                <div className="mt-3 flex flex-col gap-2 sm:flex-row">
                  <button
                    onClick={() =>
                      ask(compareKey,
                        `אני מרים ${lift.best_1rm!.toFixed(0)} קג ב${lift.name} (1RM משוער). איפה אני עומד ביחס לאחרים?`)
                    }
                    disabled={busy !== null}
                    className="btn btn-secondary flex-1"
                  >
                    {busy === compareKey ? "בודק…" : "השווה אותי לאחרים"}
                  </button>
                  <button
                    onClick={() =>
                      ask(predictKey,
                        `אני מרים ${lift.best_1rm!.toFixed(0)} קג ב${lift.name}. מה קצב ההתקדמות הצפוי שלי?`)
                    }
                    disabled={busy !== null}
                    className="btn btn-secondary flex-1"
                  >
                    {busy === predictKey ? "מחשב…" : "חזה את הקצב שלי"}
                  </button>
                </div>

                <AgentAnswer answer={answers[compareKey]} />

                <AgentAnswer answer={answers[predictKey]}>
                  {lift.slope !== null && !answers[predictKey]?.error && (
                    <p className="mt-3 rounded-control border border-accent/25 bg-accent/8 px-3 py-2 text-[0.8rem]">
                      לפי היומן שלך, הקצב בפועל הוא{" "}
                      <span className="num font-semibold text-accent">
                        {up ? "+" : ""}{lift.slope.toFixed(2)}
                      </span>{" "}
                      ק״ג לחודש.
                    </p>
                  )}
                </AgentAnswer>
              </>
            )}
          </section>
        );
      })}
    </div>
  );
}

/* תשובת הסוכן - אותו סימון כמו במסך הצ׳אט */
function AgentAnswer({
  answer,
  children,
}: {
  answer?: { text: string; error?: boolean };
  children?: React.ReactNode;
}) {
  if (!answer) return null;

  return (
    <div className="mt-4">
      <div className="mb-1.5 flex items-center gap-2">
        <span
          className={`h-1.5 w-1.5 rounded-full ${answer.error ? "bg-bad" : "bg-accent"}`}
        />
        <span className="eyebrow">POWERTRACKER</span>
      </div>

      {answer.error ? (
        <p className="rounded-card border border-bad/35 bg-bad/8 px-4 py-3 text-sm">
          {answer.text}
        </p>
      ) : (
        <div className="rounded-card border border-line bg-surface px-4 py-3">
          <div className="prose prose-sm prose-invert max-w-none prose-headings:text-ink prose-strong:text-ink prose-a:text-accent">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{answer.text}</ReactMarkdown>
          </div>
          {children}
        </div>
      )}
    </div>
  );
}