import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const { password } = await req.json();

  const correct = process.env.APP_PASSWORD;
  const secret = process.env.AUTH_SECRET;

  if (!correct || !secret) {
    return NextResponse.json(
      { error: "לא הוגדרה סיסמה למערכת. פנה למנהל המערכת" },
      { status: 500 }
    );
  }

  if (password !== correct) {
    return NextResponse.json({ error: "סיסמה שגויה" }, { status: 401 });
  }

  const res = NextResponse.json({ ok: true });
  res.cookies.set("auth", secret, {
    httpOnly: true,      // JS בדפדפן לא יכול לקרוא את זה
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 30,   // 30 יום
    secure: process.env.NODE_ENV === "production",
  });
  return res;
}