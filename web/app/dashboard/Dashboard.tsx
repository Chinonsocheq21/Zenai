"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  type AggregateData, type Week, CHECKIN_LABELS, FOCUS_LABELS, HANDOFF_LAYER_LABELS, SPEED_LABELS,
  demoData, metric, safeShare, fmtWeek, fmtCount, fmtPct,
} from "./data";
import { TrendChart, StackedBarChart, HBarGroup } from "./charts";

const CODE_KEY = "zenai-pilot-code";
const RANGE_OPTIONS = [4, 8, 12] as const;
const CHECKIN_COLORS = ["#2f7a5e", "#5c9a74", "#c7a23a", "#d9772f", "#b3321f"]; // calm -> crisis, one ramp

type Tab = "overview" | "safety" | "use";

function KpiTile({ label, value, delta, help }: { label: string; value: string; delta: string | null; help?: string }) {
  return (
    <div className="rounded-3xl border border-line bg-card p-5">
      <p className="text-sm text-ink2">{label}</p>
      <p className="mt-2 font-serif text-3xl text-ink">{value}</p>
      {delta && <p className="mt-1 text-sm text-ink2">{delta}</p>}
      {help && <p className="mt-2 text-xs text-muted">{help}</p>}
    </div>
  );
}

function weekChange(weeks: Week[], key: string): { value: number | null; delta: string | null } {
  if (weeks.length === 0) return { value: null, delta: null };
  const last = metric(weeks[weeks.length - 1], key);
  if (weeks.length < 2) return { value: last, delta: null };
  const prev = metric(weeks[weeks.length - 2], key);
  if (last === null || prev === null) return { value: last, delta: "vs last week: not enough data" };
  if (prev === 0) return { value: last, delta: last === 0 ? "No change from last week" : "Up from 0 last week" };
  const pct = Math.round(((last - prev) / prev) * 100);
  const sign = pct > 0 ? "Up" : pct < 0 ? "Down" : "No change";
  return { value: last, delta: `${sign} ${Math.abs(pct)}% vs last week` };
}

function afterHoursShareByWeek(w: Week): number | null {
  return safeShare(metric(w, "after_hours"), metric(w, "conversations"));
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

export default function Dashboard() {
  const searchParams = useSearchParams();
  const isDemo = searchParams.get("demo") === "1";

  const [code, setCode] = useState(() => {
    if (isDemo || typeof window === "undefined") return "";
    return sessionStorage.getItem(CODE_KEY) ?? "";
  });
  const [codeInput, setCodeInput] = useState("");
  const [range, setRange] = useState<(typeof RANGE_OPTIONS)[number]>(8);
  const [data, setData] = useState<AggregateData | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [tab, setTab] = useState<Tab>("overview");

  useEffect(() => {
    let cancelled = false;
    async function run() {
      if (isDemo) { setData(demoData(range)); setError(""); return; }
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

  function signOut() {
    sessionStorage.removeItem(CODE_KEY);
    setCode(""); setData(null); setCodeInput("");
  }

  const last = data?.weeks[data.weeks.length - 1];

  const kpis = useMemo(() => {
    if (!data) return null;
    const conv = weekChange(data.weeks, "conversations");
    const msg = weekChange(data.weeks, "messages");
    const ho = weekChange(data.weeks, "handoffs");
    const shares = data.weeks.map(afterHoursShareByWeek);
    const lastShare = shares[shares.length - 1] ?? null;
    const prevShare = shares.length > 1 ? shares[shares.length - 2] : null;
    let shareDelta: string | null = null;
    if (lastShare !== null && prevShare !== null) {
      const diff = Math.round((lastShare - prevShare) * 100);
      shareDelta = diff === 0 ? "No change from last week" : `${diff > 0 ? "Up" : "Down"} ${Math.abs(diff)} pts vs last week`;
    } else if (lastShare !== null) {
      shareDelta = null;
    } else {
      shareDelta = "Not enough data this week";
    }
    return { conv, msg, ho, lastShare, shareDelta };
  }, [data]);

  if (!isDemo && !data) {
    return (
      <div className="mx-auto max-w-md">
        <form
          onSubmit={(e) => { e.preventDefault(); if (codeInput.trim()) setCode(codeInput.trim()); }}
          className="rounded-3xl border border-line bg-card p-6"
        >
          <label htmlFor="code" className="text-sm font-medium text-ink2">Pilot access code</label>
          <input
            id="code" value={codeInput} onChange={(e) => setCodeInput(e.target.value)} autoComplete="off" spellCheck={false}
            className="mt-2 w-full rounded-2xl border border-line bg-paper px-4 py-3 font-mono outline-none focus:border-navy"
          />
          {error && <p role="alert" className="mt-3 text-sm text-crisis">{error}</p>}
          <button type="submit" disabled={busy} className="mt-4 w-full rounded-full bg-navy px-6 py-3.5 font-semibold text-white hover:bg-navy2 disabled:opacity-60">
            {busy ? "Opening..." : "Open the dashboard"}
          </button>
        </form>
        <div className="mt-6 text-center">
          <Link href="/dashboard/?demo=1" className="font-semibold text-navy underline underline-offset-2">
            See a demo with sample data
          </Link>
          <p className="mt-1 text-sm text-muted">No code needed. Shows a made-up campus so you can see the console before signing a pilot.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="print:block">
      {isDemo && (
        <p className="mb-6 rounded-2xl border border-orange/30 bg-orangefill/10 px-4 py-3 text-sm font-semibold text-orange print:border-ink print:bg-transparent">
          Sample data, not a real campus. Every number on this page is made up for demonstration.
        </p>
      )}

      <div className="flex flex-wrap items-center justify-between gap-4 print:hidden">
        <div>
          <p className="text-sm text-ink2">
            <b className="text-ink">{data?.campus ?? "..."}</b>{data?.min_group ? ` · any number under ${data.min_group} shows as "fewer than 10"` : ""}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div role="group" aria-label="Date range" className="flex rounded-full border border-line bg-card p-1">
            {RANGE_OPTIONS.map((r) => (
              <button
                key={r} type="button" onClick={() => setRange(r)}
                aria-pressed={range === r}
                className={`rounded-full px-3 py-1.5 text-sm font-medium ${range === r ? "bg-navy text-white" : "text-ink2 hover:bg-paper2"}`}
              >
                {r} weeks
              </button>
            ))}
          </div>
          <button
            type="button" disabled={!data} onClick={() => data && downloadCsv(data)}
            className="rounded-full border border-line bg-card px-4 py-2 text-sm font-semibold text-ink2 hover:bg-paper2 disabled:opacity-50"
          >
            Download CSV
          </button>
          <button
            type="button" onClick={() => window.print()}
            className="rounded-full border border-line bg-card px-4 py-2 text-sm font-semibold text-ink2 hover:bg-paper2"
          >
            Print weekly report
          </button>
          {!isDemo && (
            <button type="button" onClick={signOut} className="rounded-full px-3 py-2 text-sm font-semibold text-navy hover:underline">
              Sign out
            </button>
          )}
        </div>
      </div>

      {error && <p role="alert" className="mt-4 text-sm text-crisis print:hidden">{error}</p>}

      <nav aria-label="Dashboard section" className="mt-6 flex gap-1 border-b border-line print:hidden">
        {([["overview", "Overview"], ["safety", "Safety"], ["use", "Use"]] as [Tab, string][]).map(([key, label]) => (
          <button
            key={key} type="button" onClick={() => setTab(key)}
            aria-current={tab === key ? "page" : undefined}
            className={`-mb-px border-b-2 px-4 py-3 text-sm font-semibold ${tab === key ? "border-navy text-navy" : "border-transparent text-ink2 hover:text-ink"}`}
          >
            {label}
          </button>
        ))}
      </nav>

      {!data ? (
        <p className="mt-8 text-ink2 print:hidden">{busy ? "Loading..." : "No data yet."}</p>
      ) : (
        <>
          <section className={tab === "overview" ? "mt-8 space-y-8" : "hidden print:mt-8 print:block print:space-y-8"} aria-labelledby="overview-h">
            <h2 id="overview-h" className="font-serif text-2xl">Overview</h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <KpiTile label="Conversations, this week" value={fmtCount(kpis!.conv.value)} delta={kpis!.conv.delta} />
              <KpiTile label="Messages, this week" value={fmtCount(kpis!.msg.value)} delta={kpis!.msg.delta} />
              <KpiTile label="Crisis hand-offs, this week" value={fmtCount(kpis!.ho.value)} delta={kpis!.ho.delta} />
              <KpiTile label="Share after hours, this week" value={fmtPct(kpis!.lastShare)} delta={kpis!.shareDelta} help="After 6pm or before 8am, campus local time." />
            </div>

            <div className="rounded-3xl border border-line bg-card p-6">
              <h3 className="font-semibold">Conversations and hand-offs, by week</h3>
              <div className="mt-5"><TrendChart weeks={data.weeks} /></div>
            </div>

            <div className="rounded-3xl border border-line bg-card p-6">
              <h3 className="font-semibold">How heavy check-ins felt, by week</h3>
              <p className="mt-1 text-sm text-ink2">Every conversation starts with a check-in. This is the mix of levels students reported, from Light to &quot;I&apos;m not okay&quot;.</p>
              <div className="mt-5">
                <StackedBarChart
                  weeks={data.weeks} keyPrefix="checkin:" labels={CHECKIN_LABELS} colors={CHECKIN_COLORS}
                  caption="Check-in level mix by week"
                />
              </div>
            </div>
          </section>

          <section className={tab === "safety" ? "mt-8 space-y-8" : "hidden print:mt-8 print:block print:space-y-8"} aria-labelledby="safety-h">
            <h2 id="safety-h" className="font-serif text-2xl">Safety</h2>
            <p className="text-ink2">
              What used to be the student-facing &quot;Checked&quot; mark now lives here, for staff.{" "}
              <Link href="/safety/" className="font-semibold text-navy underline">How the safety check works</Link>.
            </p>

            <div className="grid gap-6 lg:grid-cols-2">
              <div className="rounded-3xl border border-line bg-card p-6">
                <h3 className="font-semibold">Replies checked, this week</h3>
                <p className="mt-1 text-sm text-ink2">Every reply is screened before a student sees it. This is how many were, out of messages sent.</p>
                <p className="mt-4 font-serif text-3xl">{fmtCount(metric(last!, "checked"))}</p>
              </div>
              <div className="rounded-3xl border border-line bg-card p-6">
                <h3 className="font-semibold">How a checked reply reached the student, this week</h3>
                <p className="mt-1 text-sm text-ink2">Passed on the first draft, sent back to be rewritten, or replaced with a safe fallback line.</p>
                <div className="mt-4">
                  <HBarGroup
                    color="var(--color-navy)"
                    items={[
                      { label: "Passed on the first draft", value: metric(last!, "first_pass") },
                      { label: "Rewritten, then passed", value: metric(last!, "rewritten") },
                      { label: "Replaced with a safe fallback", value: metric(last!, "fallback") },
                    ]}
                  />
                </div>
              </div>
              <div className="rounded-3xl border border-line bg-card p-6">
                <h3 className="font-semibold">Crisis hand-offs, by which layer caught them</h3>
                <p className="mt-1 text-sm text-ink2">Clear language, the conversation&apos;s own context, or a second-look model screen.</p>
                <div className="mt-4">
                  <HBarGroup
                    color="var(--color-crisis)"
                    items={Object.entries(HANDOFF_LAYER_LABELS).map(([k, label]) => ({ label, value: metric(last!, `handoff_by:${k}`) }))}
                  />
                </div>
              </div>
              <div className="rounded-3xl border border-line bg-card p-6">
                <h3 className="font-semibold">Reply speed, this week</h3>
                <p className="mt-1 text-sm text-ink2">How quickly a checked reply reached the student: fast, ok, or slow.</p>
                <div className="mt-4">
                  <HBarGroup
                    color="var(--color-orangefill)"
                    items={Object.entries(SPEED_LABELS).map(([k, label]) => ({ label, value: metric(last!, `speed:${k}`) }))}
                  />
                </div>
              </div>
            </div>
          </section>

          <section className={tab === "use" ? "mt-8 space-y-8" : "hidden print:mt-8 print:block print:space-y-8"} aria-labelledby="use-h">
            <h2 id="use-h" className="font-serif text-2xl">Use</h2>
            <div className="grid gap-6 lg:grid-cols-2">
              <div className="rounded-3xl border border-line bg-card p-6">
                <h3 className="font-semibold">Focus areas, this week</h3>
                <p className="mt-1 text-sm text-ink2">Which specialist a conversation was routed to.</p>
                <div className="mt-4">
                  <HBarGroup
                    color="var(--color-navy)"
                    items={Object.entries(FOCUS_LABELS).map(([k, label]) => ({ label, value: metric(last!, `focus:${k}`) }))}
                  />
                </div>
              </div>
              <div className="rounded-3xl border border-line bg-card p-6">
                <h3 className="font-semibold">Signed in versus open, this week</h3>
                <p className="mt-1 text-sm text-ink2">Signed-in conversations can sync check-ins between devices; open ones never create an account.</p>
                <div className="mt-4">
                  <HBarGroup
                    color="var(--color-calm)"
                    items={(() => {
                      const conv = metric(last!, "conversations");
                      const signedIn = metric(last!, "signed_in");
                      const open = conv === null || signedIn === null ? null : Math.max(0, conv - signedIn);
                      return [
                        { label: "Signed in", value: signedIn },
                        { label: "Open (not signed in)", value: open },
                      ];
                    })()}
                  />
                </div>
              </div>
              <div className="rounded-3xl border border-line bg-card p-6 lg:col-span-2">
                <h3 className="font-semibold">Share after hours, by week</h3>
                <p className="mt-1 text-sm text-ink2">After 6pm or before 8am, campus local time.</p>
                <table className="mt-4 w-full text-left text-sm">
                  <caption className="sr-only">Share of conversations after hours, by week</caption>
                  <thead className="text-muted"><tr><th className="py-1.5 font-medium">Week of</th><th className="font-medium">After hours</th></tr></thead>
                  <tbody>
                    {data.weeks.map((w) => (
                      <tr key={w.week} className="border-t border-line">
                        <td className="py-1.5">{fmtWeek(w.week)}</td>
                        <td>{fmtPct(afterHoursShareByWeek(w))}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          <div className="mt-10 hidden print:block">
            <h2 className="font-serif text-2xl">Week by week</h2>
            <table className="mt-4 w-full text-left text-sm">
              <thead><tr><th className="py-1.5">Week of</th><th>Conversations</th><th>Messages</th><th>Crisis hand-offs</th><th>After hours</th></tr></thead>
              <tbody>
                {data.weeks.map((w) => (
                  <tr key={w.week} className="border-t border-line">
                    <td className="py-1.5">{fmtWeek(w.week)}</td>
                    <td>{fmtCount(metric(w, "conversations"))}</td>
                    <td>{fmtCount(metric(w, "messages"))}</td>
                    <td>{fmtCount(metric(w, "handoffs"))}</td>
                    <td>{fmtPct(afterHoursShareByWeek(w))}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
