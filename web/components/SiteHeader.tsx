"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import Orb from "./Orb";

const LINKS = [
  { href: "/", label: "Home" },
  { href: "/how-it-works/", label: "How it works" },
  { href: "/safety/", label: "Safety" },
  { href: "/get-the-app/", label: "Get the app" },
  { href: "/universities/", label: "For universities" },
  { href: "/help/", label: "Help" },
];

export default function SiteHeader() {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  const menuBtn = useRef<HTMLButtonElement>(null);

  // Escape closes the mobile menu and puts focus back on the button that opened it.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") { setOpen(false); menuBtn.current?.focus(); }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);
  const here = (h: string) => (h === "/" ? path === "/" : path?.startsWith(h));

  return (
    <header className="sticky top-0 z-40 border-b border-line/70 bg-paper/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-4 px-5">
        <Link href="/" className="flex items-center gap-2.5" aria-label="ZenAI home">
          <Orb size={30} />
          <span className="font-serif text-[22px]">ZenAI</span>
        </Link>

        <nav aria-label="Main" className="ml-6 hidden items-center gap-1 md:flex">
          {LINKS.slice(1).map((l) => (
            <Link key={l.href} href={l.href}
              className={`rounded-full px-3.5 py-2 text-[15px] transition-colors hover:bg-paper2 ${here(l.href) ? "font-semibold text-navy" : "text-ink2"}`}
              aria-current={here(l.href) ? "page" : undefined}>
              {l.label}
            </Link>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-2">
          <Link href="/help/" className="rounded-full border border-crisis/30 bg-crisisbg px-3.5 py-2 text-sm font-semibold text-crisis hover:bg-crisis hover:text-white">
            Get help now
          </Link>
          <a href="/app/" className="hidden rounded-full bg-navy px-4 py-2 text-sm font-semibold text-white hover:bg-navy2 sm:inline-block">
            Open ZenAI
          </a>
          <button ref={menuBtn} type="button" className="rounded-full p-2 md:hidden" aria-expanded={open} aria-controls="mobile-nav"
            aria-label={open ? "Close menu" : "Open menu"} onClick={() => setOpen(!open)}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              {open ? <path d="M6 6l12 12M18 6L6 18" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
            </svg>
          </button>
        </div>
      </div>

      {open && (
        <nav id="mobile-nav" aria-label="Main" className="border-t border-line bg-paper px-5 pb-5 pt-2 md:hidden">
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} onClick={() => setOpen(false)}
              className={`block rounded-xl px-3 py-3 text-[17px] ${here(l.href) ? "bg-paper2 font-semibold text-navy" : "text-ink"}`}>
              {l.label}
            </Link>
          ))}
          <a href="/app/" className="mt-3 block rounded-full bg-navy px-4 py-3 text-center font-semibold text-white">Open ZenAI</a>
          <p className="mt-2 text-center text-sm text-ink2">Sign in with your Morgan email or an invite code.</p>
        </nav>
      )}
    </header>
  );
}
