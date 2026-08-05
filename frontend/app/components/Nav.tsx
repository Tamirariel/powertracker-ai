"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/journal", label: "יומן" },
  { href: "/powerlifting", label: "פאוורליפטינג" },
  { href: "/chat", label: "צ׳אט" },
];

export default function Nav() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50">
      <nav className="flex items-center gap-1 bg-base/85 px-5 py-3 backdrop-blur-md md:px-8">
        {/* סימן המותג — Oswald, כמו חותמת על ציוד */}
        <Link
          href="/journal"
          className="ms-1 me-5 font-mono text-[0.95rem] font-semibold tracking-[0.14em] text-ink"
        >
          POWER<span className="text-accent">TRACKER</span>
        </Link>

        {links.map(({ href, label }) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? "page" : undefined}
              className={`rounded-control px-3 py-1.5 text-sm transition-colors ${
                active
                  ? "bg-raised font-semibold text-accent"
                  : "font-medium text-muted hover:text-ink"
              }`}
            >
              {label}
            </Link>
          );
        })}

        <form action="/api/logout" method="post" className="ms-auto">
          <button type="submit" className="btn btn-ghost h-9 min-h-0 px-3 text-sm">
            יציאה
          </button>
        </form>
      </nav>

      {/* מוט טעון — רצף דיסקיות שנמוג לאפור */}
      <div className="loaded-bar" />
    </header>
  );
}