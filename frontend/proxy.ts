import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function proxy(req: NextRequest) { 
  const cookie = req.cookies.get("auth")?.value;

  if (cookie && cookie === process.env.AUTH_SECRET) {
    return NextResponse.next();
  }

  return NextResponse.redirect(new URL("/login", req.url));
}

// כל הדפים חוץ מ-login, ה-API של ההתחברות, וקבצים סטטיים
export const config = {
  matcher: ["/((?!api|login|_next|favicon.ico).*)"],
};