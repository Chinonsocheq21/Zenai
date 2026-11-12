"use client";

// The staff console's frame: a collapsible left sidebar (a top sheet on phones), and a
// top bar with the page title, the range picker and the campus chip.

import Link from "next/link";
import { useEffect, useRef, useState, type ReactNode } from "react";
import Orb from "@/components/Orb";
import { THEME_KEY } from "@/components/ThemeSwitch";

export type View = "overview" | "safety" | "students" | "reports";
export const VIEWS: { id: View; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "safety", label: "Safety" },
  { id: "students", label: "Students" },
  { id: "reports", label: "Reports" },
];

const ICONS: Record<View | "design" | "help" | "out", ReactNode> = {
  overview: <path d="M4 5h6v6H4zM14 5h6v4h-6zM14 13h6v6h-6zM4 15h6v4H4z" />,
  safety: <path d="M12 3l7 3v5c0 4.5-3 8.3-7 10-4-1.7-7-5.5-7-10V6z M9 12l2 2 4-4" />,
  students: <path d="M9 11a3.5 3.5 0 100-7 3.5 3.5 0 000 7zM2.5 20c.8-3.4 3.4-5 6.5-5s5.7 1.6 6.5 5M16 4.5a3.5 3.5 0 010 6.6M18 15c2 .6 3.2 2.2 3.5 5" />,
  reports: <path d="M6 3h9l4 4v14H6zM14 3v5h5M9 13h7M9 17h7" />,
  design: <path d="M12 3l7 3v5c0 4.5-3 8.3-7 10-4-1.7-7-5.5-7-10V6z" />,
  help: <path d="M12 21a9 9 0 100-18 9 9 0 000 18zM9.5 9.5a2.5 2.5 0 114 2c-.9.6-1.5 1.1-1.5 2.5M12 17h.01" />,
  out: <path d="M15 4h4v16h-4M10 8l-4 4 4 4M6 12h10" />,
};

function Icon({ name }: { name: keyof typeof ICONS }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className="shrink-0">
      {ICONS[name]}
    </svg>
  );
}

type Theme = "light" | "dark" | "system";

/** The console is dark-first: with no saved choice it shows dark, without saving it, and
 * puts the site's default (light) back when you leave. A saved choice always wins. */
function useConsoleTheme() {
  const [theme, setTheme] = useState<Theme>("dark");
  useEffect(() => {
    let saved: string | null = null;
    try { saved = localStorage.getItem(THEME_KEY); } catch { /* storage blocked */ }
    const t: Theme = saved === "light" || saved === "system" || saved === "dark" ? saved : "dark";
    document.documentElement.setAttribute("data-theme", t);
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time read of the saved theme on mount.
    setTheme(t);
    return () => {
      let s: string | null = null;
      try { s = localStorage.getItem(THEME_KEY); } catch { /* storage blocked */ }
      if (!s) document.documentElement.setAttribute("data-theme", "light");
    };
  }, []);
  function choose(t: Theme) {
    setTheme(t);
    document.documentElement.setAttribute("data-theme", t);
    try { localStorage.setItem(THEME_KEY, t); } catch { /* this visit only */ }
  }
  return [theme, choose] as const;
}

function ThemeToggle({ compact }: { compact: boolean }) {
  const [theme, choose] = useConsoleTheme();
  const opts: { v: Theme; label: string; icon: ReactNode }[] = [
    { v: "light", label: "Light", icon: <path d="M12 16a4 4 0 100-8 4 4 0 000 8zM12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /> },
    { v: "dark", label: "Dark", icon: <path d="M20 14.5A8 8 0 019.5 4 8 8 0 1020 14.5z" /> },
    { v: "system", label: "Match my phone", icon: <path d="M8 2.5h8a1.5 1.5 0 011.5 1.5v16a1.5 1.5 0 01-1.5 1.5H8A1.5 1.5 0 016.5 20V4A1.5 1.5 0 018 2.5zM11 18.5h2" /> },
  ];
  return (
    <div role="radiogroup" aria-label="Theme" className={`flex rounded-xl border border-line bg-paper p-1 ${compact ? "flex-col" : ""}`}>
      {opts.map((o) => (
        <button
          key={o.v} type="button" role="radio" aria-checked={theme === o.v} aria-label={o.label} title={o.label}
          onClick={() => choose(o.v)}
          className={`flex flex-1 items-center justify-center rounded-lg py-1.5 ${theme === o.v ? "bg-card text-ink shadow-sm" : "text-muted hover:text-ink"}`}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{o.icon}</svg>
        </button>
      ))}
    </div>
  );
}

function NavList({ view, onView, compact, enabled }: { view: View; onView: (v: View) => void; compact: boolean; enabled: boolean }) {
  if (!enabled) return null;
  return (
    <ul className="space-y-1">
      {VIEWS.map((v) => (
        <li key={v.id}>
          <button
            type="button" onClick={() => onView(v.id)} aria-current={view === v.id ? "page" : undefined} title={compact ? v.label : undefined}
            className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${compact ? "justify-center" : ""} ${
              view === v.id ? "bg-card text-ink shadow-sm ring-1 ring-line" : "text-ink2 hover:bg-card/60 hover:text-ink"}`}
          >
            <Icon name={v.id} />
            <span className={compact ? "sr-only" : ""}>{v.label}</span>
          </button>
        </li>
      ))}
    </ul>
  );
}

function BottomLinks({ compact, onSignOut, signOutLabel }: { compact: boolean; onSignOut: (() => void) | null; signOutLabel: string }) {
  const row = `flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-ink2 hover:bg-card/60 hover:text-ink ${compact ? "justify-center" : ""}`;
  return (
    <div className="space-y-1">
      <Link href="/safety/" className={row} title={compact ? "Safety design" : undefined}><Icon name="design" /><span className={compact ? "sr-only" : ""}>Safety design</span></Link>
      <Link href="/contact/" className={row} title={compact ? "Help and support" : undefined}><Icon name="help" /><span className={compact ? "sr-only" : ""}>Help and support</span></Link>
      <div className="px-1 py-2"><ThemeToggle compact={compact} /></div>
      {onSignOut && (
        <button type="button" onClick={onSignOut} className={row} title={compact ? signOutLabel : undefined}>
          <Icon name="out" /><span className={compact ? "sr-only" : ""}>{signOutLabel}</span>
        </button>
      )}
    </div>
  );
}

function Brand({ compact }: { compact: boolean }) {
  return (
    <Link href="/" className="flex min-w-0 items-center gap-2.5" aria-label="ZenAI home">
      <Orb size={28} />
      {!compact && (
        <span className="min-w-0 leading-tight">
          <span className="block font-serif text-xl text-ink">ZenAI</span>
          <span className="block text-xs text-muted">Campus console</span>
        </span>
      )}
    </Link>
  );
}

export default function Console({
  view, onView, title, controls, banner, navEnabled, onSignOut, signOutLabel, children,
}: {
  view: View; onView: (v: View) => void; title: string; controls?: ReactNode; banner?: ReactNode;
  navEnabled: boolean; onSignOut: (() => void) | null; signOutLabel: string; children: ReactNode;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const [sheet, setSheet] = useState(false);
  const sheetBtn = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!sheet) return;
    const onKey = (e: globalThis.KeyboardEvent) => { if (e.key === "Escape") { setSheet(false); sheetBtn.current?.focus(); } };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [sheet]);

  const go = (v: View) => { onView(v); setSheet(false); };

  return (
    <div className="flex min-h-dvh bg-paper print:block print:min-h-0 print:bg-white">
      {/* Sidebar, md and up. The outer column carries the colour the full page height. */}
      <div className="hidden shrink-0 border-r border-line bg-paper2 md:block print:hidden">
      <aside
        className={`sticky top-0 flex h-dvh flex-col overflow-y-auto p-3 transition-[width] ${collapsed ? "w-[76px]" : "w-[248px]"}`}
      >
        <div className={`flex items-center gap-2 px-2 pb-6 pt-2 ${collapsed ? "flex-col" : "justify-between"}`}>
          <Brand compact={collapsed} />
          <button
            type="button" onClick={() => setCollapsed(!collapsed)} aria-expanded={!collapsed}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="rounded-lg border border-line p-1.5 text-muted hover:text-ink"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <rect x="3" y="4" width="18" height="16" rx="3" />
              <path d={collapsed ? "M11 9l3 3-3 3" : "M14 9l-3 3 3 3"} />
            </svg>
          </button>
        </div>
        <nav aria-label="Console" className="flex-1">
          <NavList view={view} onView={go} compact={collapsed} enabled={navEnabled} />
        </nav>
        <BottomLinks compact={collapsed} onSignOut={onSignOut} signOutLabel={signOutLabel} />
      </aside>
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Phone bar with the top sheet */}
        <div className="sticky top-0 z-30 border-b border-line bg-paper2/95 backdrop-blur md:hidden print:hidden">
          <div className="flex h-14 items-center justify-between px-4">
            <Brand compact={false} />
            <button
              ref={sheetBtn} type="button" onClick={() => setSheet(!sheet)} aria-expanded={sheet} aria-controls="console-sheet"
              aria-label={sheet ? "Close console menu" : "Open console menu"} className="rounded-lg border border-line p-2 text-ink"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
                {sheet ? <path d="M6 6l12 12M18 6L6 18" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
              </svg>
            </button>
          </div>
          {sheet && (
            <div id="console-sheet" className="max-h-[80dvh] overflow-y-auto border-t border-line px-3 pb-4 pt-3">
              <nav aria-label="Console" className="pb-3"><NavList view={view} onView={go} compact={false} enabled={navEnabled} /></nav>
              <div className="border-t border-line pt-3"><BottomLinks compact={false} onSignOut={onSignOut} signOutLabel={signOutLabel} /></div>
            </div>
          )}
        </div>

        <main id="main" className="min-w-0 flex-1 px-4 pb-10 pt-6 sm:px-6 lg:px-8 print:p-0">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <h1 className="font-serif text-3xl text-ink">{title}</h1>
            {controls && <div className="flex flex-wrap items-center gap-2 print:hidden">{controls}</div>}
          </div>
          {banner}
          <div className="mt-6">{children}</div>
        </main>
      </div>
    </div>
  );
}
