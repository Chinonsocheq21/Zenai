"use client";

// Hand-written SVG charts, no charting library. Every chart:
//  - uses theme tokens (CSS variables) for color, so dark mode follows for free;
//  - starts its value axis at zero;
//  - carries a visually hidden <table> with the same numbers, for screen readers;
//  - labels series directly where there are few enough to read, and otherwise
//    falls back to a small legend.

import { fmtCount, fmtWeek, type Week } from "./data";

function HiddenTable({ caption, columns, rows }: { caption: string; columns: string[]; rows: (string | number)[][] }) {
  return (
    <table className="sr-only">
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
  );
}

const SERIES_COLOR: Record<string, string> = {
  conversations: "var(--color-navy)",
  handoffs: "var(--color-crisis)",
};

/** The weekly conversations line, with a direct end label instead of a legend. Hand-offs
 * are a different scale (a handful against dozens), so they get their own chart below. */
export function TrendChart({ weeks }: { weeks: Week[] }) {
  const W = 640, H = 220, PAD_L = 34, PAD_R = 86, PAD_T = 16, PAD_B = 28;
  const plotW = W - PAD_L - PAD_R, plotH = H - PAD_T - PAD_B;
  const series: { key: "conversations" | "handoffs"; label: string }[] = [
    { key: "conversations", label: "Conversations" },
  ];
  const maxV = Math.max(1, ...weeks.flatMap((w) => series.map((s) => (typeof w[s.key] === "number" ? (w[s.key] as number) : 0))));
  const x = (i: number) => PAD_L + (weeks.length <= 1 ? plotW / 2 : (i / (weeks.length - 1)) * plotW);
  const y = (v: number) => PAD_T + plotH - (v / maxV) * plotH;

  const linePath = (key: "conversations" | "handoffs") => {
    const pts = weeks.map((w, i) => (typeof w[key] === "number" ? [x(i), y(w[key] as number)] : null));
    let d = "";
    let drawing = false;
    pts.forEach((p) => {
      if (!p) { drawing = false; return; }
      d += `${drawing ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)} `;
      drawing = true;
    });
    return d.trim();
  };

  const tickCount = 4;
  const ticks = Array.from({ length: tickCount + 1 }, (_, i) => Math.round((maxV / tickCount) * i));

  return (
    <figure className="m-0">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Conversations by week" className="h-auto w-full">
        {ticks.map((t) => (
          <g key={t}>
            <line x1={PAD_L} x2={W - PAD_R} y1={y(t)} y2={y(t)} stroke="var(--color-line)" strokeWidth={1} />
            <text x={PAD_L - 8} y={y(t)} textAnchor="end" dominantBaseline="middle" fontSize={10} fill="var(--color-muted)">{t}</text>
          </g>
        ))}
        <line x1={PAD_L} x2={W - PAD_R} y1={PAD_T + plotH} y2={PAD_T + plotH} stroke="var(--color-line)" strokeWidth={1} />
        {weeks.map((w, i) => (
          i % Math.ceil(weeks.length / 8 || 1) === 0 ? (
            <text key={w.week} x={x(i)} y={H - 8} textAnchor="middle" fontSize={10} fill="var(--color-muted)">{fmtWeek(w.week)}</text>
          ) : null
        ))}
        {series.map((s) => (
          <path key={s.key} d={linePath(s.key)} fill="none" stroke={SERIES_COLOR[s.key]} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
        ))}
        {series.map((s) => {
          let lastIdx = -1;
          weeks.forEach((w, i) => { if (typeof w[s.key] === "number") lastIdx = i; });
          if (lastIdx < 0) return null;
          const v = weeks[lastIdx][s.key] as number;
          return (
            <g key={`${s.key}-label`}>
              <circle cx={x(lastIdx)} cy={y(v)} r={3} fill={SERIES_COLOR[s.key]} />
              <text x={x(lastIdx) + 8} y={y(v)} dominantBaseline="middle" fontSize={11} fontWeight={600} fill={SERIES_COLOR[s.key]}>
                {s.label} ({v})
              </text>
            </g>
          );
        })}
        {weeks.some((w) => w.conversations === null) && (
          <text x={PAD_L} y={14} fontSize={10} fill="var(--color-muted)">Gaps are weeks with fewer than 10</text>
        )}
      </svg>
      <HiddenTable
        caption="Conversations by week"
        columns={["Week", "Conversations"]}
        rows={weeks.map((w) => [fmtWeek(w.week), fmtCount(w.conversations as number | null)])}
      />
    </figure>
  );
}

/** A stacked bar per week, one segment per category, with a legend (five categories is too many to label directly). */
export function StackedBarChart({
  weeks, keyPrefix, labels, colors, caption,
}: {
  weeks: Week[]; keyPrefix: string; labels: string[]; colors: string[]; caption: string;
}) {
  const W = 640, H = 200, PAD_L = 8, PAD_R = 8, PAD_T = 10, PAD_B = 28;
  const plotW = W - PAD_L - PAD_R, plotH = H - PAD_T - PAD_B;
  const gap = 4;
  const barW = Math.max(6, plotW / weeks.length - gap);

  const totals = weeks.map((w) => {
    let known = 0, hidden = false;
    labels.forEach((_, i) => {
      const v = w[`${keyPrefix}${i}`];
      if (v === null) hidden = true; else if (typeof v === "number") known += v;
    });
    return { known, hidden };
  });
  const maxV = Math.max(1, ...totals.map((t) => t.known));

  return (
    <figure className="m-0">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={caption} className="h-auto w-full">
        <line x1={PAD_L} x2={W - PAD_R} y1={PAD_T + plotH} y2={PAD_T + plotH} stroke="var(--color-line)" strokeWidth={1} />
        {weeks.map((w, wi) => {
          const bx = PAD_L + wi * (barW + gap);
          const t = totals[wi];
          if (t.hidden && t.known === 0) {
            return (
              <g key={w.week}>
                <rect x={bx} y={PAD_T + plotH - 6} width={barW} height={6} fill="var(--color-line)" rx={2} />
                <text x={bx + barW / 2} y={H - 8} textAnchor="middle" fontSize={9} fill="var(--color-muted)">{fmtWeek(w.week)}</text>
              </g>
            );
          }
          let yCursor = PAD_T + plotH;
          return (
            <g key={w.week}>
              {labels.map((_, i) => {
                const v = w[`${keyPrefix}${i}`];
                const vNum = typeof v === "number" ? v : 0;
                const h = (vNum / maxV) * plotH;
                yCursor -= h;
                return h > 0 ? (
                  <rect key={i} x={bx} y={yCursor} width={barW} height={Math.max(0, h - 1)} fill={colors[i]} rx={1.5} />
                ) : null;
              })}
              <text x={bx + barW / 2} y={H - 8} textAnchor="middle" fontSize={9} fill="var(--color-muted)">{fmtWeek(w.week)}</text>
            </g>
          );
        })}
      </svg>
      <ul className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5 text-xs text-ink2" aria-hidden="true">
        {labels.map((l, i) => (
          <li key={l} className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: colors[i] }} />
            {l}
          </li>
        ))}
      </ul>
      <HiddenTable
        caption={caption}
        columns={["Week", ...labels]}
        rows={weeks.map((w) => [fmtWeek(w.week), ...labels.map((_, i) => fmtCount((w[`${keyPrefix}${i}`] as number | null | undefined) ?? 0))])}
      />
    </figure>
  );
}

/** A horizontal bar for each category of the most recent week: one accent colour, a direct value label. */
export function HBarGroup({
  items, color, unit,
}: {
  items: { label: string; value: number | null }[]; color: string; unit?: string;
}) {
  const max = Math.max(1, ...items.map((i) => i.value ?? 0));
  return (
    <div className="space-y-3">
      {items.map((it) => (
        <div key={it.label}>
          <div className="flex items-baseline justify-between text-sm">
            <span className="text-ink2">{it.label}</span>
            <span className="font-semibold text-ink">
              {it.value === null ? <span title="Fewer than 10, hidden to protect students">fewer than 10</span> : `${it.value}${unit ?? ""}`}
            </span>
          </div>
          <div className="mt-1 h-2.5 w-full overflow-hidden rounded-full bg-paper2">
            <div
              className="h-full rounded-full"
              style={{ width: it.value === null ? "4%" : `${Math.max(3, ((it.value ?? 0) / max) * 100)}%`, background: it.value === null ? "var(--color-line)" : color }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

/** One metric as a bar per week, on its own scale. A week with fewer than 10 is drawn as a
 * dashed outline marked "<10", never as zero, so a small number is never read as none. */
export function WeeklyBars({ weeks, metricKey, label, color }: { weeks: Week[]; metricKey: string; label: string; color: string }) {
  const W = 640, H = 150, PAD_L = 26, PAD_R = 8, PAD_T = 18, PAD_B = 26;
  const plotW = W - PAD_L - PAD_R, plotH = H - PAD_T - PAD_B;
  const slot = plotW / Math.max(1, weeks.length);
  const barW = Math.max(6, slot - 8);
  const vals = weeks.map((w) => w[metricKey]);
  const maxV = Math.max(10, ...vals.map((v) => (typeof v === "number" ? v : 0)));
  const y = (v: number) => PAD_T + plotH - (v / maxV) * plotH;
  return (
    <figure className="m-0">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${label} by week`} className="h-auto w-full">
        {[0, maxV].map((t) => (
          <g key={t}>
            <line x1={PAD_L} x2={W - PAD_R} y1={y(t)} y2={y(t)} stroke="var(--color-line)" strokeWidth={1} />
            <text x={PAD_L - 6} y={y(t)} textAnchor="end" dominantBaseline="middle" fontSize={10} fill="var(--color-muted)">{Math.round(t)}</text>
          </g>
        ))}
        {weeks.map((w, i) => {
          const v = vals[i];
          const x0 = PAD_L + i * slot + (slot - barW) / 2;
          const show = i % Math.ceil(weeks.length / 8 || 1) === 0;
          return (
            <g key={w.week}>
              {typeof v === "number" ? (
                <>
                  <rect x={x0} y={y(v)} width={barW} height={Math.max(0, PAD_T + plotH - y(v))} rx={3} fill={color} />
                  <text x={x0 + barW / 2} y={y(v) - 4} textAnchor="middle" fontSize={10} fontWeight={600} fill="var(--color-ink2)">{v}</text>
                </>
              ) : v === null ? (
                <>
                  <rect x={x0} y={y(10)} width={barW} height={PAD_T + plotH - y(10)} rx={3} fill="none" stroke="var(--color-muted)" strokeDasharray="3 3" />
                  <text x={x0 + barW / 2} y={y(10) - 4} textAnchor="middle" fontSize={10} fill="var(--color-muted)">&lt;10</text>
                </>
              ) : null}
              {show && <text x={x0 + barW / 2} y={H - 8} textAnchor="middle" fontSize={10} fill="var(--color-muted)">{fmtWeek(w.week)}</text>}
            </g>
          );
        })}
      </svg>
      <HiddenTable caption={`${label} by week`} columns={["Week", label]}
        rows={weeks.map((w) => [fmtWeek(w.week), fmtCount(w[metricKey] as number | null)])} />
    </figure>
  );
}
