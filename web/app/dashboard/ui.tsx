// The console's card system: one card shape, a KPI card, a delta badge.

import type { ReactNode } from "react";

export type Tone = "good" | "bad" | "neutral";

export function Card({ title, sub, aside, className = "", children }: {
  title: string; sub?: ReactNode; aside?: ReactNode; className?: string; children: ReactNode;
}) {
  return (
    <section className={`min-w-0 rounded-[20px] border border-line bg-card p-5 print:break-inside-avoid ${className}`}>
      <div className="flex flex-wrap items-start justify-between gap-x-6 gap-y-3">
        <div className="min-w-0">
          <h3 className="text-sm font-medium text-muted">{title}</h3>
          {sub && <p className="mt-1 text-sm text-ink2">{sub}</p>}
        </div>
        {aside}
      </div>
      <div className="mt-4">{children}</div>
    </section>
  );
}

export function DeltaBadge({ text, tone }: { text: string; tone: Tone }) {
  const cls = tone === "good"
    ? "bg-calm/15 text-calm"
    : tone === "bad"
      ? "bg-crisisbg text-crisis"
      : "bg-paper2 text-ink2";
  return <span className={`inline-flex shrink-0 items-center rounded-md px-1.5 py-0.5 text-xs font-semibold tabular-nums ${cls}`}>{text}</span>;
}

export type Change = { badge: string | null; tone: Tone; line: string };

/** Week-on-week change of a count. `upIsGood` false means a rise is shown neutral, not green. */
export function countChange(last: number | null, prev: number | null, upIsGood: boolean | null = true): Change {
  if (last === null || prev === null) return { badge: null, tone: "neutral", line: "Not enough data to compare" };
  if (prev === 0) return { badge: null, tone: "neutral", line: last === 0 ? "Same as last week" : "Up from 0 last week" };
  const pct = Math.round(((last - prev) / prev) * 100);
  return fromDiff(pct, `${Math.abs(pct)}%`, `${pct > 0 ? "+" : "-"}${Math.abs(pct)}%`, upIsGood);
}

/** Week-on-week change of a share, in percentage points. */
export function shareChange(last: number | null, prev: number | null, upIsGood: boolean | null = true): Change {
  if (last === null || prev === null) return { badge: null, tone: "neutral", line: "Not enough data to compare" };
  const pts = Math.round((last - prev) * 100);
  const unit = Math.abs(pts) === 1 ? "pt" : "pts";
  return fromDiff(pts, `${Math.abs(pts)} ${unit}`, `${pts > 0 ? "+" : "-"}${Math.abs(pts)} ${unit}`, upIsGood);
}

function fromDiff(diff: number, abs: string, signed: string, upIsGood: boolean | null): Change {
  if (diff === 0) return { badge: null, tone: "neutral", line: "Same as last week" };
  const up = diff > 0;
  const tone: Tone = upIsGood === null ? "neutral" : up === upIsGood ? "good" : "bad";
  return { badge: signed, tone, line: `${up ? "Up" : "Down"} ${abs} this week` };
}

export function KpiCard({ label, value, change, help }: { label: string; value: string; change: Change; help?: string }) {
  const small = value.length > 8;
  return (
    <section className="flex min-w-0 flex-col rounded-[20px] border border-line bg-card p-5 print:break-inside-avoid">
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-medium text-muted">{label}</h3>
        {change.badge && <DeltaBadge text={change.badge} tone={change.tone} />}
      </div>
      <p className={`mt-3 font-semibold tracking-tight tabular-nums text-ink ${small ? "text-xl" : "text-3xl"}`}>{value}</p>
      <p className="mt-2 text-sm text-ink2">{change.line}</p>
      {help && <p className="mt-1 text-xs text-muted">{help}</p>}
    </section>
  );
}
