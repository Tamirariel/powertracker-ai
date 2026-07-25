
"use client";
import { useState, useEffect } from "react";
export default function Home() {
  const [result, setResult] = useState("טרם נבדק");

  async function checkHealth() {
    setResult("בודק...");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`);
      const data = await res.json();
      setResult(`✅ השרת עונה: ${JSON.stringify(data)}`);
    } catch (e) {
      setResult(`❌ שגיאה: ${e}`);
    }
  }

  return (
    <main dir="rtl" className="mx-auto max-w-xl p-8">
      <h1 className="mb-4 text-2xl font-bold">PowerTracker</h1>
      <button onClick={checkHealth} className="rounded bg-blue-600 px-4 py-2 text-white">
        בדוק חיבור לשרת
      </button>
      <p className="mt-4">{result}</p>
    </main>
  );
}