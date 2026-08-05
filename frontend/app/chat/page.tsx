"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import ProfileCard from "../components/ProfileCard";

const API = "/api/backend";

type Msg = {
  role: "user" | "assistant";
  content: string;
  error?: boolean;
};

// שאלות פתיחה — כל אחת ממפה ליכולת אמיתית של הסוכן
const STARTERS = [
  "איך הסקוואט שלי משתווה למתאמנים בגילי ובמשקלי?",
  "מה קצב ההתקדמות שלי בשלושת הליפטים?",
  "על איזה ליפט כדאי לי להתמקד עכשיו?",
  "מה השיאים שלי בחודש האחרון?",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [slow, setSlow] = useState(false);

  const streamEnd = useRef<HTMLDivElement>(null);
  const composer = useRef<HTMLTextAreaElement>(null);

  // גלילה להודעה החדשה
  useEffect(() => {
    streamEnd.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  // אחרי 4 שניות מחליפים את הודעת הטעינה — הסוכן לוקח זמן, השתיקה מטרידה
  useEffect(() => {
    if (!loading) {
      setSlow(false);
      return;
    }
    const t = setTimeout(() => setSlow(true), 4000);
    return () => clearTimeout(t);
  }, [loading]);

  const ask = useCallback(
    async (question: string) => {
      const q = question.trim();
      if (!q || loading) return;

      setInput("");
      if (composer.current) composer.current.style.height = "auto";
      setMessages((prev) => [...prev, { role: "user", content: q }]);
      setLoading(true);

      try {
        const res = await fetch(`${API}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: q }),
        });
        if (!res.ok) throw new Error();
        const data = await res.json();
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: data.answer },
        ]);
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "לא הצלחתי להגיע לשרת. בדוק את החיבור ונסה שוב.",
            error: true,
          },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [loading],
  );

  // שליחה חוזרת של השאלה האחרונה
  function retry() {
    const lastUser = [...messages].reverse().find((m) => m.role === "user");
    if (!lastUser) return;
    setMessages((prev) => prev.slice(0, -1));
    ask(lastUser.content);
  }

  function onComposerInput(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }

  const empty = messages.length === 0 && !loading;

  return (
    <div className="mx-auto flex h-[calc(100dvh-3.8rem)] w-full max-w-6xl flex-col gap-6 px-5 py-6 lg:flex-row lg:px-8">
      {/* ── שיחה ─────────────────────────────────────────── */}
      <section className="order-first flex min-h-0 flex-1 flex-col">
        <div className="shrink-0 pb-4">
          <p className="eyebrow">הסוכן</p>
          <h1 className="mt-1">שאל על האימונים שלך</h1>
        </div>

        {/* זרם ההודעות */}
        <div className="min-h-0 flex-1 overflow-y-auto">
          {empty ? (
            <div className="flex h-full flex-col justify-start pt-2 pb-8">
              <p className="lede max-w-lg text-[0.95rem]">
                אני קורא את היומן שלך ומשווה אותו לתוצאות תחרות אמיתיות של מעל
                מיליון מתאמנים. אפשר לשאול על השוואה לקבוצת הייחוס שלך, על קצב
                התקדמות, או כל דבר בפאוורליפטינג.
              </p>

              <p className="eyebrow mt-8 mb-3">נסה לשאול</p>
              <div className="flex flex-wrap gap-2">
                {STARTERS.map((s) => (
                  <button key={s} className="chip" onClick={() => ask(s)}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-5 py-1">
              {messages.map((m, i) =>
                m.role === "user" ? (
                  <div key={i} className="flex justify-start">
                    <div className="max-w-[85%] rounded-card rounded-ss-sm bg-raised px-4 py-2.5 text-[0.95rem] whitespace-pre-wrap">
                      {m.content}
                    </div>
                  </div>
                ) : (
                  <div key={i}>
                    <div className="mb-1.5 flex items-center gap-2">
                      <span
                        className={`h-1.5 w-1.5 rounded-full ${
                          m.error ? "bg-bad" : "bg-accent"
                        }`}
                      />
                      <span className="eyebrow">POWERTRACKER</span>
                    </div>

                    {m.error ? (
                      <div className="rounded-card border border-bad/35 bg-bad/8 px-4 py-3">
                        <p className="text-[0.95rem] text-ink">{m.content}</p>
                        <button
                          onClick={retry}
                          className="btn btn-danger mt-3 h-9 min-h-0 text-[0.8rem]"
                        >
                          נסה שוב
                        </button>
                      </div>
                    ) : (
                      <div className="prose prose-sm prose-invert max-w-none prose-headings:text-ink prose-strong:text-ink prose-a:text-accent prose-td:border-line prose-th:border-line">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {m.content}
                        </ReactMarkdown>
                      </div>
                    )}
                  </div>
                ),
              )}

              {loading && (
                <div>
                  <div className="mb-1.5 flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                    <span className="eyebrow">POWERTRACKER</span>
                  </div>
                  <div className="flex items-center gap-3 text-sm text-muted">
                    <span className="flex gap-1">
                      {[0, 1, 2].map((i) => (
                        <span
                          key={i}
                          className="h-1.5 w-1.5 animate-bounce rounded-full bg-accent"
                          style={{ animationDelay: `${i * 0.15}s` }}
                        />
                      ))}
                    </span>
                    {slow ? "משווה מול נתוני התחרויות…" : "בודק את הנתונים שלך…"}
                  </div>
                </div>
              )}

              <div ref={streamEnd} />
            </div>
          )}
        </div>

        {/* תיבת כתיבה — מעוגנת לתחתית */}
        <div className="shrink-0 pt-4">
          <div className="flex items-end gap-2 rounded-card border border-line-strong bg-surface p-2 focus-within:border-accent">
            <textarea
              ref={composer}
              rows={1}
              value={input}
              onChange={onComposerInput}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  ask(input);
                }
              }}
              placeholder="אני מרים 140 בסקוואט, כמה זה ביחס לאחרים?"
              className="max-h-40 flex-1 resize-none bg-transparent px-2 py-2 text-[0.95rem] outline-none placeholder:text-faint"
            />
            <button
              onClick={() => ask(input)}
              disabled={loading || !input.trim()}
              className="btn btn-primary h-10 min-h-0"
            >
              שלח
            </button>
          </div>
          <p className="mt-2 text-[0.7rem] text-faint">
            Enter לשליחה · Shift+Enter לשורה חדשה
          </p>
        </div>
      </section>

      {/* ── פרופיל ───────────────────────────────────────── */}
      <aside className="order-last w-full shrink-0 lg:order-none lg:w-64 lg:self-start">
        <ProfileCard />
      </aside>
    </div>
  );
}