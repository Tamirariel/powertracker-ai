import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

const BACKEND = process.env.BACKEND_URL;
const API_KEY = process.env.API_KEY;

// מעביר בקשות לבאק . מוסיף את המפתח בשרת - הדפדפן לא רואה אותו
async function forward(req: NextRequest, segments: string[]) {
  const store = await cookies();
  if (store.get("auth")?.value !== process.env.AUTH_SECRET) {
    return NextResponse.json({ detail: "לא מחובר" }, { status: 401 });
  }

  if (!BACKEND || !API_KEY) {
    return NextResponse.json({ detail: "הגדרות שרת חסרות" }, { status: 500 });
  }

  // encodeURIComponent כי יש נתיבים בעברית - /workouts/last/רגליים
  const path = segments.map(encodeURIComponent).join("/");
  const url = `${BACKEND}/${path}${req.nextUrl.search}`;

  const init: RequestInit = {
    method: req.method,
    headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
  };

  if (req.method !== "GET" && req.method !== "DELETE") {
    init.body = await req.text();
  }

  try {
    const res = await fetch(url, init);
    const body = await res.text();
    return new NextResponse(body, {
      status: res.status,
      headers: { "Content-Type": res.headers.get("Content-Type") ?? "application/json" },
    });
  } catch (e) {
    return NextResponse.json({ detail: `השרת לא זמין: ${e}` }, { status: 502 });
  }
}

type Ctx = { params: Promise<{ path: string[] }> };

export async function GET(req: NextRequest, ctx: Ctx) {
  return forward(req, (await ctx.params).path);
}

export async function POST(req: NextRequest, ctx: Ctx) {
  return forward(req, (await ctx.params).path);
}

export async function DELETE(req: NextRequest, ctx: Ctx) {
  return forward(req, (await ctx.params).path);
}