"use client";
import { useState, useEffect, useRef } from "react";

const API = "/api/backend";

export type Profile = {
  sex: string | null;
  age: number | null;
  bodyweight: number | null;
};

type Props = {
  /** panel = עמודה צדדית (צ׳אט) · row = שורה אופקית (פאוורליפטינג) */
  variant?: "panel" | "row";
  /** מאפשר להורה לעקוב אחרי הפרופיל בלי לנהל אותו */
  onChange?: (profile: Profile) => void;
};

export default function ProfileCard({ variant = "panel", onChange }: Props) {
  const [profile, setProfile] = useState<Profile>({
    sex: null,
    age: null,
    bodyweight: null,
  });
  const [state, setState] = useState<{ text: string; ok: boolean } | null>(null);

  // ref כדי ש-onChange לא יגרור טעינה חוזרת בכל רינדור
  const notify = useRef(onChange);
  notify.current = onChange;

  useEffect(() => {
    fetch(`${API}/profile`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && typeof data === "object") {
          setProfile(data);
          notify.current?.(data);
        }
      })
      .catch(() => {});
  }, []);

  function update(patch: Partial<Profile>) {
    const next = { ...profile, ...patch };
    setProfile(next);
    notify.current?.(next);
  }

  async function save() {
    if (profile.age === null || profile.bodyweight === null) {
      setState({ text: "צריך גיל ומשקל גוף כדי להשוות אותך לאחרים", ok: false });
      return;
    }
    try {
      const res = await fetch(`${API}/profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      });
      if (!res.ok) throw new Error();
      setState({ text: "הפרופיל נשמר", ok: true });
      setTimeout(() => setState(null), 2500);
    } catch {
      setState({ text: "השמירה נכשלה. נסה שוב", ok: false });
    }
  }

  const row = variant === "row";

  const fields = (
    <>
      <div>
        <span className="label">מגדר</span>
        <div className="flex gap-2">
          {["זכר", "נקבה"].map((s) => (
            <button
              key={s}
              aria-pressed={profile.sex === s}
              onClick={() => update({ sex: s })}
              className={`toggle-option ${row ? "px-4" : "flex-1"}`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="label" htmlFor="pf-age">גיל</label>
        <input
          id="pf-age"
          type="number"
          inputMode="numeric"
          value={profile.age ?? ""}
          onChange={(e) =>
            update({ age: e.target.value === "" ? null : Number(e.target.value) })
          }
          className={`field field-num ${row ? "w-24" : ""}`}
        />
      </div>

      <div>
        <label className="label" htmlFor="pf-bw">משקל גוף (ק״ג)</label>
        <input
          id="pf-bw"
          type="number"
          step={0.5}
          inputMode="decimal"
          value={profile.bodyweight ?? ""}
          onChange={(e) =>
            update({
              bodyweight: e.target.value === "" ? null : Number(e.target.value),
            })
          }
          className={`field field-num ${row ? "w-28" : ""}`}
        />
      </div>
    </>
  );

  if (row) {
    return (
      <div className="card">
        <p className="eyebrow mb-3">הפרופיל שלי</p>
        <div className="flex flex-wrap items-end gap-3">
          {fields}
          <button onClick={save} className="btn btn-secondary">
            שמור פרופיל
          </button>
          {state && (
            <span
              role="status"
              className={`text-[0.8rem] ${state.ok ? "text-good" : "text-bad"}`}
            >
              {state.text}
            </span>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <p className="eyebrow">הפרופיל שלי</p>
      <p className="mt-1.5 mb-4 text-[0.775rem] leading-relaxed text-muted">
        הנתונים האלה קובעים לאיזו קבוצת ייחוס אתה מושווה.
      </p>
      <div className="space-y-3.5">
        {fields}
        <button onClick={save} className="btn btn-secondary w-full">
          שמור פרופיל
        </button>
        {state && (
          <p
            role="status"
            className={`text-[0.775rem] ${state.ok ? "text-good" : "text-bad"}`}
          >
            {state.text}
          </p>
        )}
      </div>
    </div>
  );
}