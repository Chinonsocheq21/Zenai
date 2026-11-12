"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  type AggregateData, type Week, CHECKIN_LABELS, FOCUS_LABELS, HANDOFF_LAYER_LABELS, SPEED_LABELS,
  demoData, metric, safeShare, fmtWeek, fmtCount, fmtPct,
} from "./data";
import { AreaTrend, DotFunnel, Gauge, SegmentedBar, StackedWeeks, WeekBars } from "./charts";
import Console, { VIEWS, type View } from "./Console";
import { Card, DeltaBadge, KpiCard, countChange, shareChange, type Change } from "./ui";

const CODE_KEY = "zenai-pilot-code";
const RANGE_OPTIONS = [4, 8, 12] as const;
type Range = (typeof RANGE_OPTIONS)[number];
const CHECKIN_COLORS = ["#2f7a5e", "#5c9a74", "#c7a23a", "#d9772f", "#b3321f"]; // calm to crisis, one ramp
const FOCUS_COLORS: Record<string, string> = { academic: "var(--viz-1)", stress_relief: "var(--viz-2)", wellness: "var(--viz-3)", referral: "var(--viz-4)" };
const SPEED_COLORS: Record<string, string> = { fast: "var(--viz-4)", ok: "var(--viz-1)", slow: "var(--viz-2)" };
const TREND_SERIES = [
  { key: "messages", label: "Messages", color: "var(--viz-1)", area: true },
  { key: "conversations", label: "Conversations", color: "var(--viz-2)", area: true },
];

// ---- derived figures (all from weekly counts; nothing finer than a week) ----

function lastTwo(weeks: Week[], key: string): [number | null, number | null] {
  const n = weeks.length;
  return [n ? metric(weeks[n - 1], key) : null, n > 1 ? metric(weeks[n - 2], key) : null];
}

/** A range total of the weeks that are shown. Hidden weeks stay out, so the total is "at least". */
function total(weeks: Week[], key: string): { value: number | null; partial: boolean } {
  let t = 0, partial = false, any = false;
  for (const w of weeks) {
    const v = metric(w, key);
    if (v === null) partial = true; else { t += v; any = true; }
  }
  return { value: any || !partial ? t : null, partial: partial && any };
}
const fmtTotal = (t: { value: number | null; partial: boolean }) => (t.partial ? `at least ${t.value}` : fmtCount(t.value));

const afterHoursShare = (w: Week) => safeShare(metric(w, "after_hours"), metric(w, "messages"));
const passRate = (w: Week) => safeShare(metric(w, "first_pass"), metric(w, "checked"));
const fastShare = (w: Week) => {
  const parts = Object.keys(SPEED_LABELS).map((k) => metric(w, `speed:${k}`));
  if (parts.some((p) => p === null)) return null;
  return safeShare(metric(w, "speed:fast"), (parts as number[]).reduce((a, b) => a + b, 0));
};
/** signed_in is counted per message, so "open" is messages minus signed in. A difference under 10
 * is hidden too: subtracting two shown counts must not reveal a small group. */
function openMessages(w: Week): number | null {
  const msgs = metric(w, "messages"), signedIn = metric(w, "signed_in");
  const diff = msgs === null || signedIn === null ? null : Math.max(0, msgs - signedIn);
  return diff !== null && diff > 0 && diff < 10 ? null : diff;
}
function shares(weeks: Week[], f: (w: Week) => number | null): [number | null, number | null] {
  const n = weeks.length;
  return [n ? f(weeks[n - 1]) : null, n > 1 ? f(weeks[n - 2]) : null];
}

function downloadCsv(data: AggregateData) {
  const metricKeys = Array.from(new Set(data.weeks.flatMap((w) => Object.keys(w).filter((k) => k !== "week"))));
  const header = ["week", ...metricKeys];
  const rows = data.weeks.map((w) => [w.week, ...metricKeys.map((k) => fmtCount(metric(w, k)))]);
  const csv = [header, ...rows].map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `zenai-${data.campus.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-weekly.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function campusName(isDemo: boolean, data: AggregateData | null): string {
  if (isDemo) return "Sample Campus (demo)";
  if (!data) return "";
  return data.campus === "morgan.edu" ? "Morgan State University" : data.campus;
}

// ---- shared cards ----

function Headline({ label, color, value, change }: { label: string; color: string; value: string; change: Change }) {
  return (
    <div>
      <p className="flex items-center gap-1.5 text-xs text-muted"><span className="inline-block h-2 w-2 rounded-full" style={{ background: color }} />{label}</p>
      <p className="mt-1 flex items-center gap-2">
        <span className="text-2xl font-semibold tabular-nums text-ink">{value}</span>
        {change.badge && <DeltaBadge text={change.badge} tone={change.tone} />}
      </p>
    </div>
  );
}

function TrendCard({ weeks, className = "" }: { weeks: Week[]; className?: string }) {
  const conv = total(weeks, "conversations"), msg = total(weeks, "messages");
  const [cl, cp] = lastTwo(weeks, "conversations"), [ml, mp] = lastTwo(weeks, "messages");
  const cc = countChange(cl, cp), mc = countChange(ml, mp);
  return (
    <Card
      className={className} title="Conversations and messages"
      sub={`Conversations ${cc.line.toLowerCase()}, messages ${mc.line.toLowerCase()}.`}
      aside={
        <div className="flex gap-6">
          <Headline label="Conversations" color="var(--viz-2)" value={fmtTotal(conv)} change={cc} />
          <Headline label="Messages" color="var(--viz-1)" value={fmtTotal(msg)} change={mc} />
        </div>
      }
    >
      <AreaTrend weeks={weeks} series={TREND_SERIES} caption="Conversations and messages by week" />
      <p className="mt-2 text-xs text-muted">Totals for the weeks shown. Badges compare this week with last week. Hover or use the arrow keys for a week.</p>
    </Card>
  );
}

function FunnelCard({ weeks, className = "" }: { weeks: Week[]; className?: string }) {
  const t = (k: string) => total(weeks, k).value;
  const stages = [
    { label: "Messages", value: t("messages") },
    { label: "Checked", value: t("checked") },
    { label: "Passed first draft", value: t("first_pass") },
    { label: "Rewritten", value: t("rewritten") },
    { label: "Safe fallback", value: t("fallback") },
  ];
  const rate = safeShare(stages[2].value, stages[1].value);
  return (
    <Card
      className={className} title="The safety pipeline"
      sub="Every reply is checked before a student sees it. Shares are of all messages in the weeks shown."
      aside={<div><p className="text-xs text-muted">First-draft pass rate</p><p className="text-2xl font-semibold tabular-nums text-ink">{fmtPct(rate)}</p></div>}
    >
      <div className="pt-4"><DotFunnel stages={stages} caption="The safety pipeline, weeks shown" /></div>
      <p className="mt-4 text-xs text-muted">A week with fewer than 10 in a stage is left out of that stage&apos;s total.</p>
    </Card>
  );
}

function SpeedGaugeCard({ weeks, className = "" }: { weeks: Week[]; className?: string }) {
  const [l, p] = shares(weeks, fastShare);
  const c = shareChange(l, p);
  const last = weeks[weeks.length - 1];
  return (
    <Card className={className} title="Reply speed: share under 3 s" aside={c.badge ? <DeltaBadge text={c.badge} tone={c.tone} /> : undefined}>
      <Gauge value={l} label="replies under 3 s" caption="Share of replies under 3 seconds, this week" />
      <div className="mt-3 flex justify-between gap-3 border-t border-dashed border-line pt-3 text-sm">
        <span className="text-ink2">Checked this week</span>
        <span className="font-semibold tabular-nums text-ink">{fmtCount(metric(last, "checked"))}</span>
      </div>
    </Card>
  );
}

function SignedInGaugeCard({ weeks, className = "" }: { weeks: Week[]; className?: string }) {
  const last = weeks[weeks.length - 1];
  const [l, p] = shares(weeks, (w) => safeShare(metric(w, "signed_in"), metric(w, "messages")));
  const c = shareChange(l, p, null);
  return (
    <Card className={className} title="Students signed in" sub="Share of this week's messages from signed-in students." aside={c.badge ? <DeltaBadge text={c.badge} tone={c.tone} /> : undefined}>
      <Gauge value={l} label="of messages" caption="Share of messages from signed-in students, this week" color="var(--viz-1)" />
      <dl className="mt-3 space-y-2 border-t border-dashed border-line pt-3 text-sm">
        <div className="flex justify-between"><dt className="text-ink2">Signed in</dt><dd className="font-semibold tabular-nums text-ink">{fmtCount(metric(last, "signed_in"))}</dd></div>
        <div className="flex justify-between"><dt className="text-ink2">Open (not signed in)</dt><dd className="font-semibold tabular-nums text-ink">{fmtCount(openMessages(last))}</dd></div>
      </dl>
    </Card>
  );
}

function FocusCard({ weeks, className = "" }: { weeks: Week[]; className?: string }) {
  const items = Object.entries(FOCUS_LABELS).map(([k, label]) => ({ label, value: total(weeks, `focus:${k}`).value, color: FOCUS_COLORS[k] }));
  const top = items.reduce<(typeof items)[number] | null>((b, i) => (i.value !== null && i.value > 0 && (b === null || i.value > (b.value ?? 0)) ? i : b), null);
  const [al, ap] = lastTwo(weeks, "focus:academic");
  const ac = countChange(al, ap, null);
  return (
    <Card className={className} title="Focus areas" sub="Which specialist a reply came from, in the weeks shown.">
      <dl className="grid grid-cols-2 gap-4 border-b border-dashed border-line pb-4 text-sm sm:grid-cols-3">
        <div><dt className="text-xs text-muted">Replies routed</dt><dd className="mt-0.5 font-semibold tabular-nums text-ink">{fmtTotal(total(weeks, "checked"))}</dd></div>
        <div><dt className="text-xs text-muted">Most common</dt><dd className="mt-0.5 font-semibold text-ink">{top?.label ?? "not enough data"}</dd></div>
        <div><dt className="text-xs text-muted">Academic</dt><dd className="mt-0.5 font-semibold text-ink">{ac.line}</dd></div>
      </dl>
      <div className="pt-5"><SegmentedBar items={items} caption="Focus areas, weeks shown" /></div>
    </Card>
  );
}

function SpeedBarCard({ weeks, className = "" }: { weeks: Week[]; className?: string }) {
  const items = Object.entries(SPEED_LABELS).map(([k, label]) => ({ label, value: total(weeks, `speed:${k}`).value, color: SPEED_COLORS[k] }));
  return (
    <Card className={className} title="Reply speed" sub="How quickly a checked reply reached the student, in the weeks shown.">
      <div className="pt-2"><SegmentedBar items={items} caption="Reply speed, weeks shown" /></div>
    </Card>
  );
}

function HandoffTableCard({ weeks, className = "" }: { weeks: Week[]; className?: string }) {
  const rows: [string, string][] = [...Object.entries(HANDOFF_LAYER_LABELS).map(([k, l]) => [l, `handoff_by:${k}`] as [string, string]), ["All hand-offs", "handoffs"]];
  return (
    <Card className={className} title="Crisis hand-offs by layer" sub="Which safety layer stopped the conversation and showed 988 and the counseling center.">
      <div className="-mx-1 overflow-x-auto px-1">
      <table className="w-full text-left text-sm">
        <caption className="sr-only">Crisis hand-offs by layer</caption>
        <thead className="text-xs text-muted">
          <tr><th scope="col" className="pb-2 font-medium">Layer</th><th scope="col" className="pb-2 pl-3 text-right font-medium">This week</th><th scope="col" className="pb-2 pl-3 text-right font-medium">Last week</th></tr>
        </thead>
        <tbody>
          {rows.map(([label, key]) => {
            const [l, p] = lastTwo(weeks, key);
            const last = key === "handoffs";
            return (
              <tr key={key} className={`border-t border-dashed border-line ${last ? "font-semibold" : ""}`}>
                <th scope="row" className="py-2.5 font-medium text-ink">{label}</th>
                <td className="whitespace-nowrap py-2.5 pl-3 text-right tabular-nums text-ink2">{fmtCount(l)}</td>
                <td className="whitespace-nowrap py-2.5 pl-3 text-right tabular-nums text-ink2">{fmtCount(p)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      </div>
      <p className="mt-3 flex justify-between gap-3 border-t border-dashed border-line pt-3 text-sm">
        <span className="text-ink2">All hand-offs, weeks shown</span>
        <span className="font-semibold tabular-nums text-ink">{fmtTotal(total(weeks, "handoffs"))}</span>
      </p>
    </Card>
  );
}

function CheckinCard({ weeks, className = "" }: { weeks: Week[]; className?: string }) {
  return (
    <Card className={className} title="How heavy check-ins felt" sub="Every conversation starts with a check-in. The mix of levels students chose, by week.">
      <StackedWeeks weeks={weeks} keyPrefix="checkin:" labels={CHECKIN_LABELS} colors={CHECKIN_COLORS} caption="Check-in levels by week" />
    </Card>
  );
}

function AfterHoursCard({ weeks, className = "" }: { weeks: Week[]; className?: string }) {
  return (
    <Card className={className} title="After hours by week" sub="Share of messages sent while the Counseling Center was closed, by its published hours.">
      <WeekBars weeks={weeks} values={weeks.map(afterHoursShare)} caption="Share of messages after hours by week" label="After hours"
        color="var(--viz-3)" format={(v) => `${Math.round(v * 100)}%`} hiddenText="not enough data"
        scaleMax={Math.max(...weeks.map((w) => afterHoursShare(w) ?? 0)) > 0.5 ? 1 : 0.5} height={200} />
    </Card>
  );
}

// ---- views ----

function Overview({ weeks }: { weeks: Week[] }) {
  const [cl, cp] = lastTwo(weeks, "conversations"), [ml, mp] = lastTwo(weeks, "messages"), [hl, hp] = lastTwo(weeks, "handoffs");
  const [al, ap] = shares(weeks, afterHoursShare), [pl, pp] = shares(weeks, passRate);
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
      <KpiCard label="Conversations" value={fmtCount(cl)} change={countChange(cl, cp)} />
      <KpiCard label="Messages" value={fmtCount(ml)} change={countChange(ml, mp)} />
      <KpiCard label="Crisis hand-offs" value={fmtCount(hl)} change={countChange(hl, hp, null)} />
      <KpiCard label="Share after hours" value={fmtPct(al)} change={shareChange(al, ap, null)} />
      <KpiCard label="First-draft pass rate" value={fmtPct(pl)} change={shareChange(pl, pp)} />

      <TrendCard weeks={weeks} className="sm:col-span-2 xl:col-span-3" />
      <FunnelCard weeks={weeks} className="sm:col-span-2 xl:col-span-2" />

      <SpeedGaugeCard weeks={weeks} className="xl:col-span-1" />
      <FocusCard weeks={weeks} className="xl:col-span-2" />
      <HandoffTableCard weeks={weeks} className="sm:col-span-2 xl:col-span-2" />

      <CheckinCard weeks={weeks} className="sm:col-span-2 xl:col-span-3" />
      <AfterHoursCard weeks={weeks} className="sm:col-span-2 xl:col-span-2" />
    </div>
  );
}

function Safety({ weeks }: { weeks: Week[] }) {
  const [kl, kp] = lastTwo(weeks, "checked"), [rl, rp] = lastTwo(weeks, "rewritten"), [fl, fp] = lastTwo(weeks, "fallback"), [hl, hp] = lastTwo(weeks, "handoffs");
  const [pl, pp] = shares(weeks, passRate);
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
      <KpiCard label="Replies checked" value={fmtCount(kl)} change={countChange(kl, kp)} />
      <KpiCard label="First-draft pass rate" value={fmtPct(pl)} change={shareChange(pl, pp)} />
      <KpiCard label="Rewritten, then passed" value={fmtCount(rl)} change={countChange(rl, rp, null)} />
      <KpiCard label="Safe fallback" value={fmtCount(fl)} change={countChange(fl, fp, false)} />
      <KpiCard label="Crisis hand-offs" value={fmtCount(hl)} change={countChange(hl, hp, null)} />

      <FunnelCard weeks={weeks} className="sm:col-span-2 xl:col-span-3" />
      <SpeedGaugeCard weeks={weeks} className="sm:col-span-2 xl:col-span-2" />

      <Card className="sm:col-span-2 xl:col-span-3" title="Crisis hand-offs by week" sub="Each one is a moment ZenAI stopped and showed 988 and your counseling center. A week with fewer than 10 shows as a dashed outline.">
        <WeekBars weeks={weeks} values={weeks.map((w) => metric(w, "handoffs"))} caption="Crisis hand-offs by week" label="Crisis hand-offs" color="var(--color-crisis)" format={String} />
      </Card>
      <HandoffTableCard weeks={weeks} className="sm:col-span-2 xl:col-span-2" />

      <SpeedBarCard weeks={weeks} className="sm:col-span-2 xl:col-span-2" />
      <Card className="sm:col-span-2 xl:col-span-3" title="The check, week by week" sub={<>Advice, false reassurance and diagnosis are caught and rewritten before a student sees them. <Link href="/safety/" className="font-semibold text-navy underline underline-offset-2">How the safety check works</Link></>}>
        <WeekTable weeks={weeks} caption="Safety check by week" cols={[["Checked", "checked"], ["First draft", "first_pass"], ["Rewritten", "rewritten"], ["Fallback", "fallback"]]} />
      </Card>
    </div>
  );
}

function Students({ weeks }: { weeks: Week[] }) {
  const [cl, cp] = lastTwo(weeks, "conversations"), [al, ap] = shares(weeks, afterHoursShare);
  const [sl, sp] = shares(weeks, (w) => safeShare(metric(w, "signed_in"), metric(w, "messages")));
  const [ql, qp] = shares(weeks, (w) => safeShare(metric(w, "messages"), metric(w, "conversations")));
  const perConv = (v: number | null) => (v === null ? "not enough data" : v.toFixed(1));
  const qc = countChange(ql, qp, null);
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <KpiCard label="Conversations" value={fmtCount(cl)} change={countChange(cl, cp)} />
      <KpiCard label="Messages per conversation" value={perConv(ql)} change={qc} />
      <KpiCard label="Share after hours" value={fmtPct(al)} change={shareChange(al, ap, null)} />
      <KpiCard label="Signed in (messages)" value={fmtPct(sl)} change={shareChange(sl, sp, null)} />

      <TrendCard weeks={weeks} className="sm:col-span-2 xl:col-span-3" />
      <SignedInGaugeCard weeks={weeks} className="sm:col-span-2 xl:col-span-1" />

      <FocusCard weeks={weeks} className="sm:col-span-2 xl:col-span-2" />
      <Card className="sm:col-span-2 xl:col-span-2" title="Focus areas by week">
        <WeekTable weeks={weeks} caption="Focus areas by week" cols={Object.entries(FOCUS_LABELS).map(([k, l]) => [l, `focus:${k}`] as [string, string])} />
      </Card>

      <CheckinCard weeks={weeks} className="sm:col-span-2 xl:col-span-2" />
      <AfterHoursCard weeks={weeks} className="sm:col-span-2 xl:col-span-2" />
    </div>
  );
}

function WeekTable({ weeks, caption, cols }: { weeks: Week[]; caption: string; cols: [string, string | ((w: Week) => string)][] }) {
  return (
    <div className="-mx-1 overflow-x-auto px-1">
      <table className="w-full min-w-[420px] text-left text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead className="text-xs text-muted">
          <tr>
            <th scope="col" className="pb-2 font-medium">Week of</th>
            {cols.map(([l]) => <th key={l} scope="col" className="pb-2 text-right font-medium">{l}</th>)}
          </tr>
        </thead>
        <tbody>
          {weeks.map((w) => (
            <tr key={w.week} className="border-t border-dashed border-line">
              <th scope="row" className="py-2 font-medium text-ink">{fmtWeek(w.week)}</th>
              {cols.map(([l, k]) => <td key={l} className="py-2 text-right tabular-nums text-ink2">{typeof k === "string" ? fmtCount(metric(w, k)) : k(w)}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Reports({ data, onPrint }: { data: AggregateData; onPrint: () => void }) {
  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-5">
      <Card className="xl:col-span-2" title="Export" sub="The weekly counts for the range you picked, as a spreadsheet or a one-page report.">
        <div className="flex flex-wrap gap-2 print:hidden">
          <button type="button" onClick={() => downloadCsv(data)} className="rounded-xl bg-navy px-4 py-2.5 text-sm font-semibold text-white hover:bg-navy2">Download CSV</button>
          <button type="button" onClick={onPrint} className="rounded-xl border border-line bg-paper px-4 py-2.5 text-sm font-semibold text-ink hover:bg-paper2">Print weekly report</button>
        </div>
        <h4 className="mt-6 text-sm font-semibold text-ink">What is counted</h4>
        <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm text-ink2">
          <li>Counts only, per week. ZenAI never stores what students write, or who they are.</li>
          <li>Any count under {data.min_group} shows as &quot;fewer than 10&quot;, and a difference that would reveal one is hidden too.</li>
          <li>Conversations, messages and replies checked, how each reply passed the safety check, and crisis hand-offs by the layer that caught them.</li>
          <li>After hours uses the Counseling Center&apos;s published hours in campus time. Signed in is counted per message.</li>
        </ul>
      </Card>
      <Card className="xl:col-span-3" title="Week by week">
        <WeekTable
          weeks={data.weeks} caption="Week by week"
          cols={[["Conversations", "conversations"], ["Messages", "messages"], ["Crisis hand-offs", "handoffs"], ["After hours", (w) => fmtPct(afterHoursShare(w))]]}
        />
      </Card>
    </div>
  );
}

// ---- the console ----

export default function Dashboard() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const isDemo = searchParams.get("demo") === "1";

  const [code, setCode] = useState(() => {
    if (isDemo || typeof window === "undefined") return "";
    return sessionStorage.getItem(CODE_KEY) ?? "";
  });
  const [codeInput, setCodeInput] = useState("");
  const [range, setRange] = useState<Range>(8);
  const [data, setData] = useState<AggregateData | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [view, setView] = useState<View>("overview");
  const [printing, setPrinting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function run() {
      if (isDemo) {
        setError("");
        try {
          const r = await fetch(`/api/aggregate/demo?weeks=${range}`);
          const d = r.ok ? await r.json() : null;
          if (!cancelled) setData(d && Array.isArray(d.weeks) ? { ...d, weeks: d.weeks.slice(-range) } : demoData(range));
        } catch { if (!cancelled) setData(demoData(range)); }
        return;
      }
      if (!code) return;
      setBusy(true); setError("");
      try {
        const r = await fetch(`/api/aggregate?weeks=${range}`, { headers: { "X-Pilot-Code": code } });
        const d = await r.json().catch(() => ({}));
        if (cancelled) return;
        if (!r.ok) { setError(d.detail?.message || d.message || "That didn't work. Try again later."); setData(null); }
        else { setData(d); sessionStorage.setItem(CODE_KEY, code); }
      } catch {
        if (!cancelled) setError("That didn't work. Check your connection and try again.");
      }
      if (!cancelled) setBusy(false);
    }
    run();
    return () => { cancelled = true; };
  }, [code, range, isDemo]);

  // The view lives in the hash (#safety), so a link or a reload opens the same page.
  useEffect(() => {
    const read = () => {
      const h = window.location.hash.slice(1);
      if (VIEWS.some((v) => v.id === h)) setView(h as View);
    };
    read();
    window.addEventListener("hashchange", read);
    return () => window.removeEventListener("hashchange", read);
  }, []);
  function chooseView(v: View) {
    setView(v);
    history.replaceState(null, "", `${window.location.pathname}${window.location.search}#${v}`);
    window.scrollTo({ top: 0 });
  }

  // Print renders every page stacked, then goes back to the one you were on.
  useEffect(() => {
    if (!printing) return;
    const done = () => setPrinting(false);
    window.addEventListener("afterprint", done);
    const t = window.setTimeout(() => window.print(), 50);
    return () => { window.clearTimeout(t); window.removeEventListener("afterprint", done); };
  }, [printing]);

  function signOut() {
    sessionStorage.removeItem(CODE_KEY);
    setCode(""); setData(null); setCodeInput("");
  }

  const campus = campusName(isDemo, data);
  const weeks = useMemo(() => data?.weeks ?? [], [data]);
  const title = data || isDemo ? VIEWS.find((v) => v.id === view)!.label : "Sign in";

  const controls = data || isDemo ? (
    <>
      <label className="relative flex items-center">
        <span className="sr-only">Date range</span>
        <svg className="pointer-events-none absolute left-3 text-muted" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="3" /><path d="M3 10h18M8 3v4M16 3v4" /></svg>
        <select
          aria-label="Date range" value={range} onChange={(e) => setRange(Number(e.target.value) as Range)}
          className="appearance-none rounded-xl border border-line bg-card py-2 pl-9 pr-9 text-sm font-medium text-ink"
        >
          {RANGE_OPTIONS.map((r) => <option key={r} value={r}>Last {r} weeks</option>)}
        </select>
        <svg className="pointer-events-none absolute right-3 text-muted" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M6 9l6 6 6-6" /></svg>
      </label>
      {campus && (
        <span className="flex items-center gap-2 rounded-xl border border-line bg-card px-3 py-2 text-sm font-medium text-ink">
          <span className={`inline-block h-2 w-2 rounded-full ${isDemo ? "bg-orangefill" : "bg-calm"}`} aria-hidden="true" />
          {campus}
        </span>
      )}
    </>
  ) : undefined;

  const banner = isDemo ? (
    <p className="mt-4 rounded-xl border border-orange/30 bg-orangefill/10 px-4 py-2.5 text-sm font-semibold text-orange print:border-ink print:bg-transparent print:text-ink">
      Sample data, not a real campus. Every number in this console is made up for demonstration.
    </p>
  ) : null;

  const signOutAction = isDemo ? () => { setData(null); router.push("/dashboard/"); } : data ? signOut : null;

  if (!isDemo && !data) {
    return (
      <Console view={view} onView={chooseView} title={title} navEnabled={false} onSignOut={null} signOutLabel="Sign out">
        <div className="flex min-h-[60dvh] items-center justify-center">
          <div className="w-full max-w-md">
            <form
              onSubmit={(e) => { e.preventDefault(); if (codeInput.trim()) setCode(codeInput.trim()); }}
              className="rounded-[20px] border border-line bg-card p-6"
            >
              <h2 className="text-lg font-semibold text-ink">Campus console</h2>
              <p className="mt-1 text-sm text-ink2">Weekly counts for a campus in a ZenAI pilot. Never conversations, never names.</p>
              <label htmlFor="code" className="mt-5 block text-sm font-medium text-ink2">Pilot access code</label>
              <input
                id="code" value={codeInput} onChange={(e) => setCodeInput(e.target.value)} autoComplete="off" spellCheck={false}
                className="mt-2 w-full rounded-xl border border-line bg-paper px-4 py-3 font-mono text-ink outline-none focus:border-navy"
              />
              {error && <p role="alert" className="mt-3 text-sm text-crisis">{error}</p>}
              <button type="submit" disabled={busy} className="mt-4 w-full rounded-xl bg-navy px-6 py-3 font-semibold text-white hover:bg-navy2 disabled:opacity-60">
                {busy ? "Opening..." : "Open the dashboard"}
              </button>
            </form>
            <div className="mt-6 text-center">
              <Link href="/dashboard/?demo=1" className="font-semibold text-navy underline underline-offset-2">See a demo with sample data</Link>
              <p className="mt-1 text-sm text-muted">No code needed. Shows a made-up campus so you can see the console before signing a pilot.</p>
            </div>
          </div>
        </div>
      </Console>
    );
  }

  return (
    <Console
      view={view} onView={chooseView} title={title} controls={controls} banner={banner}
      navEnabled onSignOut={signOutAction} signOutLabel={isDemo ? "Leave demo" : "Sign out"}
    >
      {error && <p role="alert" className="mb-4 text-sm text-crisis print:hidden">{error}</p>}
      {!data ? (
        <p className="text-ink2">{busy ? "Loading..." : "No data yet."}</p>
      ) : weeks.length === 0 ? (
        <p className="text-ink2">No weeks to show yet.</p>
      ) : printing ? (
        <div className="space-y-8">
          <p className="text-sm text-ink2">{campus}, last {range} weeks. Counts only; any number under 10 shows as &quot;fewer than 10&quot;.</p>
          <Overview weeks={weeks} />
          <h2 className="font-serif text-2xl">Safety</h2>
          <Safety weeks={weeks} />
          <h2 className="font-serif text-2xl">Students</h2>
          <Students weeks={weeks} />
        </div>
      ) : view === "overview" ? (
        <Overview weeks={weeks} />
      ) : view === "safety" ? (
        <Safety weeks={weeks} />
      ) : view === "students" ? (
        <Students weeks={weeks} />
      ) : (
        <Reports data={data} onPrint={() => setPrinting(true)} />
      )}
    </Console>
  );
}
