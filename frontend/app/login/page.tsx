"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const router = useRouter();

  async function submit() {
    if (!password || busy) return;
    setBusy(true);
    setError("");
    try {
      const res = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      if (res.ok) {
        router.push("/journal");
      } else {
        const data = await res.json();
        setError(data.error ?? "שגיאה");
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto mt-24 max-w-sm p-8">
      <h1 className="text-2xl font-bold">PowerTracker</h1>
      <h2 className="mt-1 text-white/60">כניסה</h2>

      <input
        type="password"
        value={password}
        onChange={e => setPassword(e.target.value)}
        onKeyDown={e => e.key === "Enter" && submit()}
        placeholder="סיסמה"
        className="mt-6 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 outline-none focus:border-blue-500"
      />

      <button
        onClick={submit}
        disabled={busy}
        className="mt-3 w-full rounded-lg bg-blue-600 px-4 py-3 font-bold disabled:opacity-50"
      >
        {busy ? "בודק..." : "כניסה"}
      </button>

      {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
    </main>
  );
}