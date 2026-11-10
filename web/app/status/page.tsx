import Link from "next/link";
import { pageMeta } from "@/components/meta";

export const metadata = pageMeta(
  "/status/",
  "Status",
  "How to check whether ZenAI is up, and what each value in its health check means.",
  "ZenAI status",
);

const VALUES = [
  ["db", "ok", "unavailable", "The database for sign-in, synced check-ins, campus counts and pilot requests. When it is unavailable, chat and the crisis hand-off keep working; only sign-in, syncing and the campus dashboard pause."],
  ["limits", "redis", "memory", "Where usage limits are counted. \"redis\" is the normal hosted setting. \"memory\" means each server counts on its own, so limits are looser, but nothing else changes."],
  ["models", "ok", "missing", "ZenAI's own small models: the distress classifier and the Fidelity Monitor's detector. \"missing\" means they were not deployed with the service, which should not happen on the hosted site; please tell us. The crisis rules run before these models and do not need them."],
];

export default function Status() {
  return (
    <article className="mx-auto max-w-3xl px-5 pb-10 pt-12">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-orange">Status</p>
      <h1 className="mt-3 font-serif text-4xl leading-tight md:text-5xl">Is ZenAI up?</h1>
      <p className="mt-5 text-lg leading-relaxed text-ink2">
        ZenAI's API answers a health check at{" "}
        <a href="/api/health" className="font-semibold text-navy underline">/api/health</a>. If that address loads and shows
        three values, the service is running. If it doesn't load at all, ZenAI is down or unreachable from where you are.
      </p>

      <section aria-labelledby="values" className="mt-10">
        <h2 id="values" className="font-serif text-2xl md:text-3xl">What each value means</h2>
        <div className="mt-5 space-y-3">
          {VALUES.map(([key, good, other, what]) => (
            <div key={key} className="rounded-3xl border border-line bg-card p-5">
              <p className="font-mono text-[15px] font-semibold text-ink">{key}</p>
              <p className="mt-1 text-[15px] text-ink2">
                Normal: <code className="font-mono text-ink">{good}</code>. Otherwise: <code className="font-mono text-ink">{other}</code>.
              </p>
              <p className="mt-2 leading-relaxed text-ink2">{what}</p>
            </div>
          ))}
        </div>
      </section>

      <section aria-labelledby="crisis" className="mt-10">
        <h2 id="crisis" className="font-serif text-2xl md:text-3xl">If ZenAI is down</h2>
        <p className="mt-3 leading-relaxed text-ink2">
          The crisis hand-off is built to work even when the language model, the database or the usage-limit store is down.
          If ZenAI can't be reached at all, you don't need it to get help: call or text{" "}
          <a href="tel:988" className="font-semibold text-crisis underline">988</a> any time, or see{" "}
          <Link href="/help/" className="font-semibold text-crisis underline">Get help now</Link>.
        </p>
        <p className="mt-3 leading-relaxed text-ink2">
          To report an outage, see <Link href="/contact/" className="font-semibold text-navy underline">Contact</Link>.
        </p>
      </section>
    </article>
  );
}
