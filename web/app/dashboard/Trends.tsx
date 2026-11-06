"use client";

import { useState } from "react";

type Week = { week: string } & Record<string, number | null | string>;
type Data = { campus: string; min_group: number; weeks: Week[] };

const CHECKINS = ["Light", "A bit much", "Heavy", "Very heavy", "I'm not okay"];
const FOCUS: Record<string, string> = {
  academic: "Academic Stress", stress_relief: "Stress-Relief", wellness: "Wellness Schedule", referral: "Resource and Referral",
};

const fmtWeek = (w: string) => new Date(w + "T12:00:00").toLocaleDateString(undefined, { month: "short", day: "numeric" });
const num = (v: unknown) => (typeof v === "number" ? v : null);

function Cell({ v }: { v: number | null }) {
  return v === null ? <span className="text-muted" title="Fewer than 10, hidden to protect students">&lt;10</span> : <span>{v}</span>;
}

export default function Trends() {
  const [code, setCode] = useState("");
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load(e?: React.FormEvent) {
    e?.preventDefault();
    if (!code.trim()) return;
    setBusy(true); setError("");
    try {
      const r = await fetch("/api/aggregate?weeks=8", { headers: { "X-Pilot-Code": code.trim() } });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) { setError(d.detail?.message || "That didn't work. Try again later."); setData(null); }
      else setData(d);
    } catch { setError("That didn't work. Check your connection and try again."); }
    setBusy(false);
  }

  if (!data) {
    return (
      <form onSubmit={load} className="mx-auto max-w-md rounded-3xl border border-line bg-card p-6">
        <label htmlFor="code" className="text-sm font-medium text-ink2">Pilot access code</label>
        <input id="code" value={code} onChange={(e) => setCode(e.target.value)} autoComplete="off" spellCheck={false}
          className="mt-2 w-full rounded-2xl border border-line bg-paper px-4 py-3 font-mono outline-none focus:border-navy" />
        {error && <p role="alert" className="mt-3 text-sm text-crisis">{error}</p>}
        <button type="submit" disabled={busy} className="mt-4 w-full rounded-full bg-navy px-6 py-3.5 font-semibold text-white hover:bg-navy2 disabled:opacity-60">
          {busy ? "Opening..." : "Open the dashboard"}
        </button>
      </form>
    );
  }

  const weeks = data.weeks;
  const maxMsg = Math.max(1, ...weeks.map((w) => num(w.messages) ?? 0));
  const last = weeks[weeks.length - 1];

  return (
    <div className="space-y-8">
      <p className="text-ink2">
        <b className="text-ink">{data.campus === "open" ? "Students not signed in" : data.campus}</b>, last {weeks.length} weeks. Counts only: no student's words or identity are
        ever stored. Any number under {data.min_group} shows as &lt;10.
      </p>

      <section className="rounded-3xl border border-line bg-card p-6">
        <h2 className="font-semibold">Messages each week</h2>
        <div className="mt-5 flex h-40 items-end gap-2" role="img" aria-label="Messages per week">
          {weeks.map((w) => {
            const v = num(w.messages);
            return (
              <div key={w.week} className="flex flex-1 flex-col items-center gap-2">
                <div className={`w-full rounded-t-xl ${v === null ? "bg-line" : "bg-navy"}`} style={{ height: `${v === null ? 6 : Math.max(6, (v / maxMsg) * 140)}px` }} />
                <span className="text-[11px] text-muted">{fmtWeek(w.week)}</span>
              </div>
            );
          })}
        </div>
      </section>

      <section className="overflow-x-auto rounded-3xl border border-line bg-card p-6">
        <h2 className="font-semibold">Week by week</h2>
        <table className="mt-4 w-full min-w-[520px] text-left text-sm">
          <thead className="text-muted"><tr>
            <th className="py-2 font-medium">Week of</th><th className="font-medium">Conversations</th>
            <th className="font-medium">Messages</th><th className="font-medium">Crisis hand-offs</th>
          </tr></thead>
          <tbody>
            {weeks.map((w) => (
              <tr key={w.week} className="border-t border-line">
                <td className="py-2.5">{fmtWeek(w.week)}</td>
                <td><Cell v={num(w.conversations)} /></td><td><Cell v={num(w.messages)} /></td>
                <td><Cell v={num(w.handoffs)} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <div className="grid gap-6 md:grid-cols-2">
        <section className="rounded-3xl border border-line bg-card p-6">
          <h2 className="font-semibold">How heavy check-ins felt, this week</h2>
          <ul className="mt-4 space-y-2 text-sm">
            {CHECKINS.slice(0, 4).map((label, i) => (
              <li key={label} className="flex justify-between border-b border-line pb-2"><span>{label}</span><Cell v={num(last[`checkin:${i}`])} /></li>
            ))}
          </ul>
        </section>
        <section className="rounded-3xl border border-line bg-card p-6">
          <h2 className="font-semibold">Which focus replied, this week</h2>
          <ul className="mt-4 space-y-2 text-sm">
            {Object.entries(FOCUS).map(([k, label]) => (
              <li key={k} className="flex justify-between border-b border-line pb-2"><span>{label}</span><Cell v={num(last[`focus:${k}`])} /></li>
            ))}
          </ul>
        </section>
      </div>
      <button type="button" onClick={() => { setData(null); setCode(""); }} className="text-sm font-semibold text-navy hover:underline">Close the dashboard</button>
    </div>
  );
}
