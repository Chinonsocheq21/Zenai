import Link from "next/link";
import { pageMeta } from "@/components/meta";

export const metadata = pageMeta(
  "/how-it-works/",
  "How it works",
  "What happens to a message in ZenAI, stage by stage, and how every reply is checked before a student sees it.",
);

const STAGES = [
  ["Privacy", "Names, emails, phone numbers and student IDs are removed from the message first. Every later stage only ever sees the redacted message, and ZenAI does not write message text to its logs."],
  ["Crisis check", "Rules, the conversation so far, today's check-in, and a model screen. If there is risk, the turn ends here. See Safety."],
  ["Mood", "A distress classifier reads how the message lands (anxiety, low mood, overwhelm, isolation and more), so the reply can meet it."],
  ["Route", "A fast model picks the focus that fits. If it is unavailable, keyword rules take over."],
  ["Memory", "Only notes the student chose to keep, from their own device, sent along with the message. Off by default. Removing names from saved notes too is being added."],
  ["Draft", "The reply is written on the Acceptance and Commitment Therapy protocol: reflect what was said, notice the thought, connect to what matters, ask one open question."],
  ["Fidelity Monitor", "Checks the draft before anyone sees it. Explained below."],
  ["Send", "Only a reply that passed. If every rewrite still drifts, a fixed protocol-safe line goes instead."],
];

const FOCUS = [
  ["Academic Stress", "Exams, grades, professors, deadlines, and what the work means to the student."],
  ["Stress-Relief", "Stress felt in the body right now, met with present-moment noticing."],
  ["Wellness Schedule", "Sleep, food, time and balance. The student names their own next step."],
  ["Resource and Referral", "When a student asks where to get help, verified Morgan offices appear beside the reply."],
];

const MONITOR = [
  ["A trained detector", "A classifier trained on real peer-support conversations scores each sentence for advice and reassurance."],
  ["A second opinion", "Anything it flags goes to a different model with the written protocol, which decides if it truly drifts. This cut false rejections of good replies."],
  ["Lines that never go out", "A short list of phrases (\"you'll be fine\", \"you should\") is blocked outright, whatever the scores say."],
];

export default function HowItWorks() {
  return (
    <div className="mx-auto max-w-5xl px-5 pb-10 pt-12">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-orange">How it works</p>
      <h1 className="mt-3 font-serif text-4xl leading-tight md:text-5xl">Every message, eight stages, every time.</h1>
      <p className="mt-5 max-w-2xl text-lg text-ink2">
        Most chat apps send whatever the model writes. ZenAI treats the model's draft as a draft: the checks that keep
        students safe run before it and after it, on every single reply.
      </p>

      <ol className="mt-10 space-y-3">
        {STAGES.map(([name, what], i) => {
          const key = name === "Crisis check" || name === "Fidelity Monitor";
          return (
            <li key={name} className={`flex gap-4 rounded-3xl border p-5 ${key ? "border-navy bg-navy text-white" : "border-line bg-card"}`}>
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-orange text-sm font-bold text-white">{i + 1}</span>
              <div>
                <h2 className="font-semibold">{name}</h2>
                <p className={`mt-1 text-[15px] leading-relaxed ${key ? "text-white/80" : "text-ink2"}`}>{what}</p>
              </div>
            </li>
          );
        })}
      </ol>

      <section aria-labelledby="monitor" className="mt-16">
        <h2 id="monitor" className="font-serif text-3xl md:text-4xl">The Fidelity Monitor</h2>
        <p className="mt-3 max-w-2xl text-ink2">
          Counselors are taught three things not to do: give advice, promise it will be fine, and label what someone is
          going through. The Fidelity Monitor checks every draft for all three, in three layers. A draft that drifts is
          rewritten, up to twice.
        </p>
        <div className="mt-6 grid gap-3 md:grid-cols-3">
          {MONITOR.map(([t, b]) => (
            <div key={t} className="rounded-3xl border border-line bg-card p-5">
              <h3 className="font-semibold">{t}</h3>
              <p className="mt-2 text-[15px] leading-relaxed text-ink2">{b}</p>
            </div>
          ))}
        </div>
      </section>

      <section aria-labelledby="focus" className="mt-16">
        <h2 id="focus" className="font-serif text-3xl md:text-4xl">One protocol, four kinds of focus</h2>
        <p className="mt-3 max-w-2xl text-ink2">Each focus is the same conversation with a different emphasis, checked by the same monitor, so none of them can step outside the protocol.</p>
        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          {FOCUS.map(([t, b]) => (
            <div key={t} className="rounded-3xl border border-line bg-card p-5">
              <h3 className="font-semibold">{t}</h3>
              <p className="mt-2 text-[15px] leading-relaxed text-ink2">{b}</p>
            </div>
          ))}
        </div>
      </section>

      <section aria-labelledby="see" className="mt-16 grid items-center gap-8 md:grid-cols-[1fr_1.3fr]">
        <div>
          <h2 id="see" className="font-serif text-3xl md:text-4xl">Nothing hidden</h2>
          <p className="mt-3 leading-relaxed text-ink2">
            During development, a workflow viewer shows each message moving through all eight stages: what was redacted,
            the crisis score, the focus it went to, every draft, what the monitor rejected and why, and what was sent.
            It runs only on the developer's laptop and is closed on the hosted site.
          </p>
          <p className="mt-4 leading-relaxed text-ink2">You can also talk out loud: your browser turns speech into text, and ZenAI answers in a calm voice. Audio is never kept.</p>
        </div>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/media/workflow.jpg" alt="The workflow viewer showing one message passing through each stage" loading="lazy"
          className="w-full rounded-3xl border border-line shadow-xl shadow-ink/10" />
      </section>

      <div className="mt-16 flex flex-wrap gap-3">
        <a href="/app/" className="rounded-full bg-navy px-6 py-3.5 font-semibold text-white hover:bg-navy2">Try ZenAI</a>
        <Link href="/safety/" className="rounded-full border border-line bg-card px-6 py-3.5 font-semibold hover:border-navy/40">Read about safety</Link>
      </div>
    </div>
  );
}
