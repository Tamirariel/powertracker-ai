"use client";
import { useState } from "react";

type Msg = { role: "user" | "assistant"; content: string };

export default function ChatPage() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function send() {
    const question = input.trim();
    if (!question || loading) return;

    setInput("");
    setMessages(prev => [...prev, { role: "user", content: question }]);
    setLoading(true);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chat`, {
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
    <main dir="rtl" className="mx-auto max-w-3xl p-8">
      <h1 className="text-2xl font-bold">PowerTracker - צ׳אט</h1>
      <p className="mt-1 text-sm text-gray-500">
        שאל אותי על הביצועים שלך, על האימונים מהיומן, או כל שאלה על פאוורליפטינג
      </p>

      <div className="my-6 space-y-3">
        {messages.map((m, i) => (
          <div
            key={i}
            className={
              m.role === "user"
                ? "rounded-lg bg-blue-50 p-3"
                : "rounded-lg bg-gray-100 p-3"
            }
          >
            <div className="mb-1 text-xs text-gray-500">
              {m.role === "user" ? "אתה" : "PowerTracker"}
            </div>
            <div className="whitespace-pre-wrap">{m.content}</div>
          </div>
        ))}
        {loading && <div className="animate-pulse text-sm text-gray-500">בודק את הנתונים...</div>}
      </div>

      <div className="flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && send()}
          placeholder="אני מרים 140 בסקוואט, כמה אני ביחס לאחרים?"
          className="flex-1 rounded-lg border px-4 py-3"
        />
        <button
          onClick={send}
          disabled={loading}
          className="rounded-lg bg-blue-600 px-5 py-3 text-white disabled:opacity-50"
        >
          שלח
        </button>
      </div>
    </main>
  );
}