"use client";

// Hand-written SVG charts for the staff console, no charting library. Every chart:
//  - draws at its real pixel width (measured), so labels stay readable from 390 px up;
//  - takes colour from theme variables (--viz-*, tokens), so dark and light both follow;
//  - starts its value axis at zero, and draws a hidden week (null) as a gap or a dashed
//    outline, never as zero;
//  - carries a visually hidden <table> with the same numbers, for screen readers;
//  - shows a tooltip on hover, and on keyboard focus with the arrow keys.

import { useEffect, useId, useRef, useState, type KeyboardEvent, type ReactNode } from "react";
import { fmtCount, fmtWeek, type Week } from "./data";

export function HiddenTable({ caption, columns, rows }: { caption: string; columns: string[]; rows: (string | number)[][] }) {
  // The wrapper is what's visually hidden: a table ignores a 1px height and would still push the page.
  return (
    <div className="sr-only">
    <table>
      <caption>{caption}</caption>
      <thead>
        <tr>{columns.map((c) => <th key={c} scope="col">{c}</th>)}</tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i}>{r.map((cell, j) => (j === 0 ? <th key={j} scope="row">{cell}</th> : <td key={j}>{cell}</td>))}</tr>
        ))}
      </tbody>
    </table>
    </div>
  );
}

/** Measures the element's width, so the SVG can be drawn 1:1 instead of scaled. */
function useWidth<T extends HTMLElement>(fallback = 560) {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(fallback);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => setWidth(Math.max(200, Math.round(e.contentRect.width))));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, width] as const;
}

function niceMax(v: number): number {
  if (v <= 10) return 10;
  const mag = 10 ** Math.floor(Math.log10(v));
  for (const m of [1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10]) if (m * mag >= v) return m * mag;
  return 10 * mag;
}

const num = (v: unknown): number | null => (typeof v === "number" ? v : null);

/** Shared keyboard handling for charts that step through weeks. */
function useWeekCursor(n: number) {
  const [active, setActive] = useState<number | null>(null);
  const onKeyDown = (e: KeyboardEvent) => {
    if (n === 0) return;
    const cur = active ?? n - 1;
    let next: number | null = null;
    if (e.key === "ArrowLeft") next = Math.max(0, cur - 1);
    else if (e.key === "ArrowRight") next = Math.min(n - 1, cur + 1);
    else if (e.key === "Home") next = 0;
    else if (e.key === "End") next = n - 1;
    else if (e.key === "Escape") { setActive(null); return; }
    if (next !== null) { e.preventDefault(); setActive(next); }
  };
  return { active, setActive, onKeyDown, onFocus: () => setActive((a) => a ?? n - 1), onBlur: () => setActive(null) };
}

function Tooltip({ id, x, width, children }: { id: string; x: number; width: number; children: ReactNode }) {
  // Keep the box inside the chart: flip to the left of the cursor near the right edge.
  const flip = x > width - 180;
  return (
    <div
      id={id}
      role="tooltip"
      className="pointer-events-none absolute top-2 z-10 min-w-36 rounded-xl border border-line bg-paper px-3 py-2 text-xs shadow-lg"
      style={flip ? { right: width - x + 12 } : { left: x + 12 }}
    >
      {children}
    </div>
  );
}

export type Series = { key: string; label: string; color: string; area?: boolean };

/** Weekly lines on one shared count axis (both series are counts), with a crosshair and tooltip. */
export function AreaTrend({ weeks, series, caption, height = 240 }: { weeks: Week[]; series: Series[]; caption: string; height?: number }) {
  const [ref, W] = useWidth<HTMLDivElement>();
  const tipId = useId();
  const gradId = useId().replace(/:/g, "");
  const cursor = useWeekCursor(weeks.length);
  const H = height, PAD_L = 40, PAD_R = 12, PAD_T = 12, PAD_B = 30;
  const plotW = W - PAD_L - PAD_R, plotH = H - PAD_T - PAD_B;
  const maxV = niceMax(Math.max(1, ...weeks.flatMap((w) => series.map((s) => num(w[s.key]) ?? 0))));
  const x = (i: number) => PAD_L + (weeks.length <= 1 ? plotW / 2 : (i / (weeks.length - 1)) * plotW);
  const y = (v: number) => PAD_T + plotH - (v / maxV) * plotH;
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((t) => Math.round(maxV * t));
  const labelEvery = Math.ceil(weeks.length / Math.max(2, Math.floor(plotW / 70)));

  const segments = (key: string) => {
    const segs: [number, number][][] = [];
    let cur: [number, number][] = [];
    weeks.forEach((w, i) => {
      const v = num(w[key]);
      if (v === null) { if (cur.length) segs.push(cur); cur = []; return; }
      cur.push([x(i), y(v)]);
    });
    if (cur.length) segs.push(cur);
    return segs;
  };
  const line = (pts: [number, number][]) => pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ");

  function onMove(e: React.PointerEvent<SVGSVGElement>) {
    const r = e.currentTarget.getBoundingClientRect();
    const px = e.clientX - r.left;
    const i = weeks.length <= 1 ? 0 : Math.round(((px - PAD_L) / plotW) * (weeks.length - 1));
    cursor.setActive(Math.max(0, Math.min(weeks.length - 1, i)));
  }

  const a = cursor.active;
  return (
    <figure className="relative m-0" ref={ref}>
      <svg
        width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={caption}
        aria-describedby={a !== null ? tipId : undefined}
        tabIndex={0} onKeyDown={cursor.onKeyDown} onFocus={cursor.onFocus} onBlur={cursor.onBlur}
        onPointerMove={onMove} onPointerLeave={() => cursor.setActive(null)}
        className="block touch-pan-y rounded-lg"
      >
        <defs>
          {series.filter((s) => s.area).map((s) => (
            <linearGradient key={s.key} id={`${gradId}-${s.key}`} x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor={s.color} stopOpacity={0.28} />
              <stop offset="100%" stopColor={s.color} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        {ticks.map((t) => (
          <g key={t}>
            <line x1={PAD_L} x2={W - PAD_R} y1={y(t)} y2={y(t)} stroke="var(--color-line)" strokeDasharray={t === 0 ? undefined : "3 5"} />
            <text x={PAD_L - 8} y={y(t)} textAnchor="end" dominantBaseline="middle" fontSize={11} fill="var(--color-muted)" className="tabular-nums">{t}</text>
          </g>
        ))}
        {weeks.map((w, i) => (i % labelEvery === 0 || i === weeks.length - 1) && (i === weeks.length - 1 || weeks.length - 1 - i >= labelEvery / 2) ? (
          <text key={w.week} x={x(i)} y={H - 8} textAnchor={i === 0 ? "start" : i === weeks.length - 1 ? "end" : "middle"} fontSize={11} fill={a === i ? "var(--color-ink)" : "var(--color-muted)"} fontWeight={a === i ? 600 : 400}>{fmtWeek(w.week)}</text>
        ) : null)}
        {series.map((s) => segments(s.key).map((pts, k) => (
          <g key={`${s.key}-${k}`}>
            {s.area && pts.length > 1 && (
              <path d={`${line(pts)} L${pts[pts.length - 1][0].toFixed(1)},${y(0)} L${pts[0][0].toFixed(1)},${y(0)} Z`} fill={`url(#${gradId}-${s.key})`} />
            )}
            <path d={line(pts)} fill="none" stroke={s.color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
          </g>
        )))}
        {a !== null && (
          <g pointerEvents="none">
            <line x1={x(a)} x2={x(a)} y1={PAD_T} y2={PAD_T + plotH} stroke="var(--color-muted)" strokeDasharray="2 3" />
            {series.map((s) => {
              const v = num(weeks[a][s.key]);
              return v === null ? null : <circle key={s.key} cx={x(a)} cy={y(v)} r={5} fill={s.color} stroke="var(--color-card)" strokeWidth={2} />;
            })}
          </g>
        )}
      </svg>
      {a !== null && (
        <Tooltip id={tipId} x={x(a)} width={W}>
          <p className="font-semibold text-ink">Week of {fmtWeek(weeks[a].week)}</p>
          {series.map((s) => (
            <p key={s.key} className="mt-0.5 flex items-center gap-1.5 text-ink2 tabular-nums">
              <span className="inline-block h-2 w-2 rounded-full" style={{ background: s.color }} />
              {fmtCount(num(weeks[a][s.key]) ?? (s.key in weeks[a] ? null : 0))} {s.label.toLowerCase()}
            </p>
          ))}
        </Tooltip>
      )}
      <HiddenTable
        caption={caption}
        columns={["Week of", ...series.map((s) => s.label)]}
        rows={weeks.map((w) => [fmtWeek(w.week), ...series.map((s) => fmtCount(s.key in w ? num(w[s.key]) : 0))])}
      />
    </figure>
  );
}

/** One value per week as bars on its own scale. A hidden week is a dashed outline marked "<10". */
export function WeekBars({
  weeks, values, caption, label, color, format, scaleMax, hiddenText = "fewer than 10", height = 180,
}: {
  weeks: Week[]; values: (number | null)[]; caption: string; label: string; color: string;
  format: (v: number) => string; scaleMax?: number; hiddenText?: string; height?: number;
}) {
  const [ref, W] = useWidth<HTMLDivElement>();
  const tipId = useId();
  const cursor = useWeekCursor(weeks.length);
  const H = height, PAD_L = 8, PAD_R = 8, PAD_T = 22, PAD_B = 28;
  const plotW = W - PAD_L - PAD_R, plotH = H - PAD_T - PAD_B;
  const slot = plotW / Math.max(1, weeks.length);
  const barW = Math.max(6, Math.min(36, slot - 6));
  const maxV = scaleMax ?? niceMax(Math.max(10, ...values.map((v) => v ?? 0)));
  const y = (v: number) => PAD_T + plotH - (v / maxV) * plotH;
  const cx = (i: number) => PAD_L + i * slot + slot / 2;
  const labelEvery = Math.ceil(weeks.length / Math.max(2, Math.floor(plotW / 56)));
  const showValues = slot >= 34;
  const a = cursor.active;
  return (
    <figure className="relative m-0" ref={ref}>
      <svg
        width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={caption}
        aria-describedby={a !== null ? tipId : undefined}
        tabIndex={0} onKeyDown={cursor.onKeyDown} onFocus={cursor.onFocus} onBlur={cursor.onBlur}
        onPointerLeave={() => cursor.setActive(null)} className="block rounded-lg"
      >
        <line x1={PAD_L} x2={W - PAD_R} y1={y(0)} y2={y(0)} stroke="var(--color-line)" />
        {weeks.map((w, i) => {
          const v = values[i];
          const x0 = cx(i) - barW / 2;
          const dim = a !== null && a !== i;
          return (
            <g key={w.week} onPointerEnter={() => cursor.setActive(i)} opacity={dim ? 0.45 : 1}>
              <rect x={PAD_L + i * slot} y={PAD_T} width={slot} height={plotH} fill="transparent" />
              {v === null ? (
                <rect x={x0} y={y(maxV * 0.12)} width={barW} height={y(0) - y(maxV * 0.12)} rx={4} fill="none" stroke="var(--color-muted)" strokeDasharray="3 3" />
              ) : (
                <path d={roundTop(x0, y(v), barW, y(0) - y(v))} fill={color} />
              )}
              {showValues && (
                <text x={cx(i)} y={(v === null ? y(maxV * 0.12) : y(v)) - 6} textAnchor="middle" fontSize={11} fill="var(--color-ink2)" className="tabular-nums">
                  {v === null ? "<10" : format(v)}
                </text>
              )}
              {(i % labelEvery === 0 || i === weeks.length - 1) && (i === weeks.length - 1 || weeks.length - 1 - i >= labelEvery / 2) && (
                <text x={cx(i)} y={H - 8} textAnchor="middle" fontSize={11} fill="var(--color-muted)">{fmtWeek(w.week)}</text>
              )}
            </g>
          );
        })}
      </svg>
      {a !== null && (
        <Tooltip id={tipId} x={cx(a)} width={W}>
          <p className="font-semibold text-ink">Week of {fmtWeek(weeks[a].week)}</p>
          <p className="mt-0.5 text-ink2 tabular-nums">{label}: {values[a] === null ? hiddenText : format(values[a]!)}</p>
        </Tooltip>
      )}
      <HiddenTable caption={caption} columns={["Week of", label]}
        rows={weeks.map((w, i) => [fmtWeek(w.week), values[i] === null ? hiddenText : format(values[i]!)])} />
    </figure>
  );
}

/** A bar path with 4px rounded top corners and a square base on the axis. */
function roundTop(x: number, y: number, w: number, h: number) {
  if (h <= 0) return "";
  const r = Math.min(4, w / 2, h);
  return `M${x},${y + h} L${x},${y + r} Q${x},${y} ${x + r},${y} L${x + w - r},${y} Q${x + w},${y} ${x + w},${y + r} L${x + w},${y + h} Z`;
}

/** A stacked bar per week, one segment per level, with a legend and a per-week tooltip. */
export function StackedWeeks({
  weeks, keyPrefix, labels, colors, caption, height = 200,
}: {
  weeks: Week[]; keyPrefix: string; labels: string[]; colors: string[]; caption: string; height?: number;
}) {
  const [ref, W] = useWidth<HTMLDivElement>();
  const tipId = useId();
  const cursor = useWeekCursor(weeks.length);
  const H = height, PAD_L = 8, PAD_R = 8, PAD_T = 8, PAD_B = 28;
  const plotW = W - PAD_L - PAD_R, plotH = H - PAD_T - PAD_B;
  const slot = plotW / Math.max(1, weeks.length);
  const barW = Math.max(6, Math.min(36, slot - 6));
  const cell = (w: Week, i: number) => { const k = `${keyPrefix}${i}`; return k in w ? num(w[k]) : 0; };
  const totals = weeks.map((w) => labels.reduce((t, _, i) => t + (cell(w, i) ?? 0), 0));
  const maxV = niceMax(Math.max(1, ...totals));
  const y = (v: number) => PAD_T + plotH - (v / maxV) * plotH;
  const labelEvery = Math.ceil(weeks.length / Math.max(2, Math.floor(plotW / 56)));
  const a = cursor.active;
  const cx = (i: number) => PAD_L + i * slot + slot / 2;
  return (
    <figure className="relative m-0" ref={ref}>
      <ul className="mb-3 flex flex-wrap gap-x-4 gap-y-1.5 text-xs text-ink2" aria-hidden="true">
        {labels.map((l, i) => (
          <li key={l} className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: colors[i] }} />{l}
          </li>
        ))}
      </ul>
      <svg
        width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={caption}
        aria-describedby={a !== null ? tipId : undefined}
        tabIndex={0} onKeyDown={cursor.onKeyDown} onFocus={cursor.onFocus} onBlur={cursor.onBlur}
        onPointerLeave={() => cursor.setActive(null)} className="block rounded-lg"
      >
        <line x1={PAD_L} x2={W - PAD_R} y1={y(0)} y2={y(0)} stroke="var(--color-line)" />
        {weeks.map((w, wi) => {
          const x0 = cx(wi) - barW / 2;
          let base = y(0);
          const segs = labels.map((_, i) => {
            const v = cell(w, i) ?? 0;
            const h = (v / maxV) * plotH;
            const top = base - h;
            const el = h > 0 ? <rect key={i} x={x0} y={top} width={barW} height={Math.max(0, h - 2)} rx={2} fill={colors[i]} /> : null;
            base = top;
            return el;
          });
          return (
            <g key={w.week} onPointerEnter={() => cursor.setActive(wi)} opacity={a !== null && a !== wi ? 0.45 : 1}>
              <rect x={PAD_L + wi * slot} y={PAD_T} width={slot} height={plotH} fill="transparent" />
              {segs}
              {(wi % labelEvery === 0 || wi === weeks.length - 1) && (wi === weeks.length - 1 || weeks.length - 1 - wi >= labelEvery / 2) && (
                <text x={cx(wi)} y={H - 8} textAnchor="middle" fontSize={11} fill="var(--color-muted)">{fmtWeek(w.week)}</text>
              )}
            </g>
          );
        })}
      </svg>
      {a !== null && (
        <Tooltip id={tipId} x={cx(a)} width={W}>
          <p className="font-semibold text-ink">Week of {fmtWeek(weeks[a].week)}</p>
          {labels.map((l, i) => (
            <p key={l} className="mt-0.5 flex items-center gap-1.5 text-ink2 tabular-nums">
              <span className="inline-block h-2 w-2 rounded-full" style={{ background: colors[i] }} />
              {l}: {fmtCount(cell(weeks[a], i))}
            </p>
          ))}
        </Tooltip>
      )}
      <HiddenTable caption={caption} columns={["Week of", ...labels]}
        rows={weeks.map((w) => [fmtWeek(w.week), ...labels.map((_, i) => fmtCount(cell(w, i)))])} />
    </figure>
  );
}

/** The dotted progress funnel: each stage's share of the first, as a run of dots. */
export function DotFunnel({ stages, caption }: { stages: { label: string; value: number | null }[]; caption: string }) {
  const base = stages[0]?.value ?? null;
  const DOTS = 12;
  return (
    <figure className="m-0">
      <ol className="grid grid-cols-1 gap-x-3 gap-y-5 sm:grid-cols-5" aria-hidden="true">
        {stages.map((s, i) => {
          const share = s.value !== null && base ? s.value / base : null;
          const lit = share === null ? 0 : Math.max(1, Math.round(share * DOTS));
          return (
            <li key={s.label} className="min-w-0">
              <p className="text-xl font-semibold tabular-nums text-ink">{share === null ? "n/a" : `${Math.round(share * 100)}%`}</p>
              <div className="mt-2 flex items-center justify-between gap-0.5">
                {Array.from({ length: DOTS }, (_, d) => (
                  <span
                    key={d}
                    className={`inline-block rounded-full ${d === 0 ? "h-2.5 w-2.5" : "h-1.5 w-1.5"}`}
                    style={{ background: d < lit ? (i === 0 ? "var(--viz-1)" : "var(--viz-2)") : "var(--color-line)" }}
                  />
                ))}
              </div>
              <p className="mt-2 text-xs leading-snug text-muted">{s.label}</p>
              <p className="text-sm font-semibold tabular-nums text-ink">{fmtCount(s.value)}</p>
            </li>
          );
        })}
      </ol>
      <HiddenTable caption={caption} columns={["Stage", "Count", "Share of messages"]}
        rows={stages.map((s) => [s.label, fmtCount(s.value), s.value !== null && base ? `${Math.round((s.value / base) * 100)}%` : "not enough data"])} />
    </figure>
  );
}

/** A 240 degree gauge for one share, with the number in the middle. */
export function Gauge({ value, label, caption, color = "var(--viz-4)" }: { value: number | null; label: string; caption: string; color?: string }) {
  const S = 200, R = 80, C = S / 2, sweep = 240, start = 150;
  const pt = (deg: number) => [C + R * Math.cos((deg * Math.PI) / 180), C + R * Math.sin((deg * Math.PI) / 180)];
  const arc = (from: number, to: number) => {
    const [x1, y1] = pt(from), [x2, y2] = pt(to);
    return `M${x1.toFixed(2)},${y1.toFixed(2)} A${R},${R} 0 ${to - from > 180 ? 1 : 0} 1 ${x2.toFixed(2)},${y2.toFixed(2)}`;
  };
  const v = value === null ? 0 : Math.max(0, Math.min(1, value));
  return (
    <figure className="m-0 flex flex-col items-center">
      <svg viewBox={`0 0 ${S} ${S * 0.86}`} role="img" aria-label={`${caption}: ${value === null ? "not enough data" : `${Math.round(v * 100)}%`}`} className="h-auto w-full max-w-[240px]">
        <path d={arc(start, start + sweep)} fill="none" stroke="var(--color-line)" strokeWidth={12} strokeLinecap="round" />
        {value !== null && v > 0 && <path d={arc(start, start + sweep * v)} fill="none" stroke={color} strokeWidth={12} strokeLinecap="round" />}
        <text x={C} y={C + 2} textAnchor="middle" fontSize={36} fontWeight={600} fill="var(--color-ink)" className="tabular-nums">
          {value === null ? "n/a" : `${Math.round(v * 100)}%`}
        </text>
        <text x={C} y={C + 26} textAnchor="middle" fontSize={13} fill="var(--color-muted)">{label}</text>
      </svg>
    </figure>
  );
}

/** One bar split by category, 2px gaps, with a legend of counts. Hidden categories stay in the legend only. */
export function SegmentedBar({ items, caption }: { items: { label: string; value: number | null; color: string }[]; caption: string }) {
  const total = items.reduce((t, i) => t + (i.value ?? 0), 0);
  return (
    <figure className="m-0">
      <div className="flex h-3 w-full gap-0.5" aria-hidden="true">
        {items.map((it) => (it.value ? (
          <span key={it.label} className="h-full rounded-full" style={{ flexGrow: it.value, flexBasis: 0, background: it.color }} title={`${it.label}: ${it.value}`} />
        ) : null))}
        {total === 0 && <span className="h-full flex-1 rounded-full bg-paper2" />}
      </div>
      <ul className="mt-5 grid grid-cols-1 gap-x-6 gap-y-3 text-sm sm:grid-cols-2" aria-hidden="true">
        {items.map((it) => (
          <li key={it.label} className="flex items-center justify-between gap-3">
            <span className="flex min-w-0 items-center gap-2 text-ink2">
              <span className="inline-block h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: it.color }} />
              <span className="truncate">{it.label}</span>
            </span>
            <span className="font-semibold tabular-nums text-ink">
              {fmtCount(it.value)}
              {it.value !== null && total > 0 && <span className="ml-1.5 font-normal text-muted">{Math.round((it.value / total) * 100)}%</span>}
            </span>
          </li>
        ))}
      </ul>
      <HiddenTable caption={caption} columns={["Category", "Count"]} rows={items.map((i) => [i.label, fmtCount(i.value)])} />
    </figure>
  );
}
