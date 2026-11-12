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

// A believable term: a quiet start, a midterm bump, a dip, then finals climbing.
// The same series as the server's GET /api/aggregate/demo (src/zenai/api/routes/aggregate.py).
const DEMO_CONVERSATIONS = [78, 86, 81, 97, 112, 104, 91, 88, 99, 108, 121, 116];
const DEMO_HANDOFFS = [4, 6, 5, 9, 12, 8, 6, 5, 7, 11, 13, 9];
const MIN_GROUP = 10;

/** One deterministic demo week, mirroring the server's _demo_week: replies checked are
 * messages minus hand-offs, check-ins add up to conversations, focus uses the four ids,
 * and some small counts fall under 10 so the hidden-group treatment shows. */
function demoWeek(i: number): Record<string, number> {
  const conversations = DEMO_CONVERSATIONS[i % DEMO_CONVERSATIONS.length];
  const messages = Math.round(conversations * (2.9 + (i % 4) * 0.15));
  const handoffs = DEMO_HANDOFFS[i % DEMO_HANDOFFS.length];
  const byPatterns = Math.round(handoffs * 0.6);
  const byContext = Math.round(handoffs * 0.25);
  const checked = messages - handoffs;
  const rewritten = 11 + ((i * 3) % 9);
  const fallback = 1 + (i % 3);
  const fast = Math.round(checked * 0.62);
  const ok = Math.round(checked * 0.31);
  const m: Record<string, number> = {
    messages, conversations, handoffs,
    "handoff_by:patterns": byPatterns, "handoff_by:context": byContext,
    "handoff_by:screen": Math.max(0, handoffs - byPatterns - byContext),
    checked, first_pass: checked - rewritten, rewritten, fallback,
    after_hours: Math.round(messages * (0.3 + (i % 4) * 0.03)), signed_in: Math.round(messages * 0.72),
    "speed:fast": fast, "speed:ok": ok, "speed:slow": checked - fast - ok,
  };
  let left = conversations;
  [0.3, 0.31, 0.22, 0.11].forEach((share, k) => {
    m[`checkin:${k}`] = Math.round(conversations * share);
    left -= m[`checkin:${k}`];
  });
  m[`checkin:${CHECKIN_LABELS.length - 1}`] = Math.max(0, left);
  ([["academic", 0.45], ["stress_relief", 0.25], ["wellness", 0.2], ["referral", 0.1]] as const).forEach(([id, share]) => {
    m[`focus:${id}`] = Math.round(checked * share);
  });
  return m;
}

/**
 * Client-side sample data with the exact server contract shape, used for demo mode when
 * GET /api/aggregate/demo doesn't answer (a local static build). The endpoint wins when it
 * does. Counts under 10 become null, exactly as the server hides them.
 */
export function demoData(weeks: number): AggregateData {
  const total = 12;
  const since = new Date();
  since.setUTCHours(12, 0, 0, 0);
  since.setUTCDate(since.getUTCDate() - ((since.getUTCDay() + 6) % 7) - (total - 1) * 7); // a Monday, 12 weeks back
  const out: Week[] = [];
  for (let i = 0; i < total; i++) {
    const d = new Date(since);
    d.setUTCDate(d.getUTCDate() + i * 7);
    const w: Week = { week: d.toISOString().slice(0, 10) };
    for (const [k, n] of Object.entries(demoWeek(i))) w[k] = n >= MIN_GROUP ? n : null;
    out.push(w);
  }
  return { campus: "Sample Campus (demo)", min_group: MIN_GROUP, weeks: out.slice(-weeks) };
}
