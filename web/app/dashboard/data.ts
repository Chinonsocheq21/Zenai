// Shared shape for GET /api/aggregate (and /api/aggregate/demo once the server ships it).
// {campus, min_group, weeks:[{week:'YYYY-MM-DD', <metric>: number|null}]}
// null means "fewer than min_group" (a small group hidden to protect students);
// a missing key means 0 (nothing happened that week), which is not the same thing.

export type Week = { week: string } & Record<string, number | null | string>;
export type AggregateData = { campus: string; min_group: number; weeks: Week[] };

export const CHECKIN_LABELS = ["Light", "A bit much", "Heavy", "Very heavy", "I'm not okay"];
export const FOCUS_LABELS: Record<string, string> = {
  academic: "Academic",
  stress_relief: "Stress relief",
  wellness: "Wellness",
  referral: "Resource and referral",
};
export const HANDOFF_LAYER_LABELS: Record<string, string> = {
  patterns: "Clear language",
  context: "Conversation context",
  screen: "Model screen",
};
export const SPEED_LABELS: Record<string, string> = { fast: "Fast", ok: "OK", slow: "Slow" };

/** Reads a metric: a present number (incl. null for "fewer than min_group"), or 0 if the key is absent. */
export function metric(w: Week, key: string): number | null {
  if (!(key in w)) return 0;
  const v = w[key];
  return typeof v === "number" ? v : null;
}

/** A ratio from two possibly-hidden counts. Never divides using a hidden cell: returns null ("not enough data") instead. */
export function safeShare(numerator: number | null, denominator: number | null): number | null {
  if (numerator === null || denominator === null || denominator === 0) return null;
  return numerator / denominator;
}

export function sum(w: Week, keys: string[]): number | null {
  let total = 0;
  for (const k of keys) {
    const v = metric(w, k);
    if (v === null) return null;
    total += v;
  }
  return total;
}

export function fmtWeek(week: string): string {
  return new Date(week + "T12:00:00").toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function fmtCount(v: number | null): string {
  return v === null ? "fewer than 10" : String(v);
}

export function fmtPct(v: number | null): string {
  return v === null ? "not enough data" : `${Math.round(v * 100)}%`;
}

/** Deterministic pseudo-random generator so demo screenshots and tests are stable across runs. */
function mulberry32(seed: number) {
  let a = seed;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Client-side sample data with the exact server contract shape, used for demo mode until
 * GET /api/aggregate/demo ships. The endpoint takes precedence once it answers; this is the
 * fallback, built to look like a real, modestly-sized pilot campus.
 */
export function demoData(weeks: number): AggregateData {
  const rand = mulberry32(20261112);
  const since = new Date();
  since.setUTCHours(12, 0, 0, 0);
  since.setUTCDate(since.getUTCDate() - since.getUTCDay() + 1 - (weeks - 1) * 7); // a Monday, `weeks` back

  const out: Week[] = [];
  for (let i = 0; i < weeks; i++) {
    const d = new Date(since);
    d.setUTCDate(d.getUTCDate() + i * 7);
    const trend = 1 + i * 0.03; // a gentle upward trend over the term
    const conversations = Math.round((60 + rand() * 30) * trend);
    const messages = Math.round(conversations * (3.2 + rand() * 1.4));
    const handoffs = Math.max(0, Math.round(conversations * (0.02 + rand() * 0.02)));
    const checked = Math.round(messages * (0.94 + rand() * 0.04));
    const fallback = Math.max(0, Math.round(checked * (0.01 + rand() * 0.015)));
    const rewritten = Math.round(checked * (0.08 + rand() * 0.06));
    const firstPass = Math.max(0, checked - rewritten - fallback);
    const afterHours = Math.round(conversations * (0.22 + rand() * 0.1));
    const signedIn = Math.round(conversations * (0.55 + rand() * 0.2));

    const checkinShares = [0.38, 0.3, 0.17, 0.09, 0.06];
    const focusShares: Record<string, number> = { academic: 0.42, stress_relief: 0.27, wellness: 0.2, referral: 0.11 };
    const handoffShares: Record<string, number> = { patterns: 0.55, context: 0.3, screen: 0.15 };
    const speedShares: Record<string, number> = { fast: 0.62, ok: 0.31, slow: 0.07 };

    const w: Week = { week: d.toISOString().slice(0, 10) };
    w.conversations = conversations;
    w.messages = messages;
    w.handoffs = handoffs;
    w.checked = checked;
    w.first_pass = firstPass;
    w.rewritten = rewritten;
    w.fallback = fallback;
    w.after_hours = afterHours;
    w.signed_in = signedIn;
    checkinShares.forEach((s, idx) => (w[`checkin:${idx}`] = Math.round(conversations * s)));
    Object.entries(focusShares).forEach(([k, s]) => (w[`focus:${k}`] = Math.round(conversations * s)));
    Object.entries(handoffShares).forEach(([k, s]) => (w[`handoff_by:${k}`] = Math.round(handoffs * s)));
    Object.entries(speedShares).forEach(([k, s]) => (w[`speed:${k}`] = Math.round(messages * s)));
    out.push(w);
  }

  // The most recent week of a small pilot is often genuinely under 10 for the rarest counts:
  // keep that true-to-life even in the sample so the "fewer than 10" treatment is visible.
  const last = out[out.length - 1];
  last.handoffs = null;
  last["handoff_by:screen"] = null;

  return { campus: "Sample Campus (demo)", min_group: 10, weeks: out };
}
