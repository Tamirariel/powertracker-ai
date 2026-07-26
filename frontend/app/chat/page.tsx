"use client";
import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API = "/api/backend";

type Msg = { role: "user" | "assistant"; content: string };
type Profile = { sex: string | null; age: number | null; bodyweight: number | null };

export default function ChatPage() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState<Profile>({ sex: null, age: null, bodyweight: null });
  const [saveMsg, setSaveMsg] = useState("");

  useEffect(() => {
    fetch(`${API}/profile`)
      .then(res => res.json())
      .then(setProfile)
      .catch(() => {});
  }, []);

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

  async function send() {
    const question = input.trim();
    if (!question || loading) return;

    setInput("");
    setMessages(prev => [...prev, { role: "user", content: question }]);
    setLoading(true);

    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: "assistant", content: data.answer }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: "assistant", content: `שגיאה בחיבור לשרת: ${e}` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-5xl gap-6 p-8">
      <aside className="w-64 shrink-0 space-y-4">
        <h2 className="text-lg font-bold">הפרופיל שלי</h2>

        <div>
          <label className="mb-1 block text-sm text-white/60">מגדר</label>
          <div className="flex gap-2">
            {["זכר", "נקבה"].map(s => (
              <button
                key={s}
                onClick={() => setProfile({ ...profile, sex: s })}
                className={
                  profile.sex === s
                    ? "flex-1 rounded-lg bg-blue-600 px-3 py-2 text-sm"
                    : "flex-1 rounded-lg bg-white/5 px-3 py-2 text-sm"
                }
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm text-white/60">גיל</label>
          <input
            type="number"
            value={profile.age ?? ""}
            onChange={e => setProfile({ ...profile, age: e.target.value === "" ? null : Number(e.target.value) })}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 outline-none focus:border-blue-500"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm text-white/60">משקל גוף (ק״ג)</label>
          <input
            type="number"
            step="0.5"
            value={profile.bodyweight ?? ""}
            onChange={e => setProfile({ ...profile, bodyweight: e.target.value === "" ? null : Number(e.target.value) })}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 outline-none focus:border-blue-500"
          />
        </div>

        <button onClick={saveProfile} className="w-full rounded-lg bg-blue-600 px-4 py-2">
          שמור פרופיל
        </button>
        {saveMsg && <p className="text-sm text-white/60">{saveMsg}</p>}
      </aside>

      <main className="flex-1">
        <h1 className="text-2xl font-bold">PowerTracker - צ׳אט</h1>
        <p className="mt-1 text-sm text-white/50">
          שאל אותי על הביצועים שלך, על האימונים מהיומן, או כל שאלה על פאוורליפטינג
        </p>

        <div className="my-6 space-y-3">
          {messages.map((m, i) => (
            <div
              key={i}
              className={
                m.role === "user"
                  ? "rounded-lg border border-blue-500/20 bg-blue-500/10 p-3"
                  : "rounded-lg bg-white/5 p-3"
              }
            >
              <div className="mb-1 text-xs text-white/40">
                {m.role === "user" ? "אתה" : "PowerTracker"}
              </div>
              {m.role === "assistant" ? (
                <div className="prose prose-sm prose-invert max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
                </div>
              ) : (
                <div className="whitespace-pre-wrap">{m.content}</div>
              )}
            </div>
          ))}
          {loading && <div className="animate-pulse text-sm text-white/50">בודק את הנתונים...</div>}
        </div>

        <div className="flex gap-2">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && send()}
            placeholder="אני מרים 140 בסקוואט, כמה אני ביחס לאחרים?"
            className="flex-1 rounded-lg border border-white/10 bg-white/5 px-4 py-3 outline-none focus:border-blue-500"
          />
          <button
            onClick={send}
            disabled={loading}
            className="rounded-lg bg-blue-600 px-5 py-3 disabled:opacity-50"
          >
            שלח
          </button>
        </div>
      </main>
    </div>
  );
}