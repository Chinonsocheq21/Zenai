"use client";

import { useEffect, useState } from "react";

// Same key and values the app uses, so the choice carries between the site and the
// app when they share an origin on Vercel. Default is Light.
export const THEME_KEY = "zenai-theme";
type Theme = "light" | "dark" | "system";
const THEMES: Theme[] = ["light", "dark", "system"];

const OPTIONS: { value: Theme; label: string }[] = [
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
  { value: "system", label: "Match my phone" },
];

function applyTheme(theme: Theme) {
  document.documentElement.setAttribute("data-theme", theme);
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch {
    // Private browsing or storage blocked: the switch still works for this visit.
  }
}

export default function ThemeSwitch() {
  const [theme, setTheme] = useState<Theme>("light");

  useEffect(() => {
    // Reads the value the inline script in layout.tsx already set on <html> before paint,
    // so the switch highlights the right option after this client component mounts.
    const stored = document.documentElement.getAttribute("data-theme");
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time read of DOM state an external script set before mount, not a derived value.
    if (stored && THEMES.includes(stored as Theme)) setTheme(stored as Theme);
  }, []);

  function choose(value: Theme) {
    setTheme(value);
    applyTheme(value);
  }

  return (
    <div>
      <h2 className="mb-3 font-semibold text-ink">Theme</h2>
      <div role="radiogroup" aria-label="Theme" className="inline-flex flex-wrap gap-1 rounded-full border border-line bg-card p-1">
        {OPTIONS.map((o) => (
          <button
            key={o.value}
            type="button"
            role="radio"
            aria-checked={theme === o.value}
            onClick={() => choose(o.value)}
            className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
              theme === o.value ? "bg-navy text-white" : "text-ink2 hover:bg-paper2"
            }`}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}
