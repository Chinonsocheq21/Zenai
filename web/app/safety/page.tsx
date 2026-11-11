import Link from "next/link";
import { pageMeta } from "@/components/meta";

export const metadata = pageMeta(
  "/safety/",
  "Safety",
  "How ZenAI notices a crisis and hands the student to a person, even when the AI is down, what the Fidelity Monitor blocks, what is never stored, and the tests behind those claims.",
);

const LAYERS = [
  { n: "1", title: "Clear crisis language", body: "Phrases that name suicide, self-harm or wanting to die are caught by fixed rules before any language model sees the message. The turn stops there, and this layer needs no AI to run." },
  { n: "2", title: "The whole conversation", body: "Quieter signs (\"what's the point\", \"I just want it to stop\") count more when they follow earlier ones or a heavy check-in. A crisis earlier in the conversation keeps it in crisis, even if the next message sounds calm." },
  { n: "3", title: "A second look by a model", body: "A fast model screens for indirect language the rules can't list. It can only raise the risk, never lower it." },
];

const PROMISES = [
  "If the language model, Redis or the database is down, the crisis check still runs on the rules and still hands off. A student in crisis is never told to come back later.",
  "Checking in as \"I'm not okay\" goes straight to the hand-off, before any chat.",
  "During a hand-off there is no text box. ZenAI doesn't try to talk anyone down; it shows people who can help.",
  "After \"I'm safe, take me back\", 988 and the Counseling Center stay pinned for the rest of the conversation.",
  "Every Morgan phone number comes from a verified list, never from the model.",
  "988 and \"Get help now\" work for anyone, signed in or not.",
];

const HELD_OUT = [
  ["Advice bait", "5 of 5"],
  ["Reassurance bait", "4 of 5"],
  ["Diagnosis bait", "5 of 5"],
  ["Role override / prompt injection", "5 of 5"],
  ["Hidden crisis, one message", "5 of 5"],
  ["Hidden crisis, across a conversation", "5 of 5"],
  ["Hyperbole (must not escalate)", "5 of 5"],
  ["Privacy (identifiers removed)", "4 of 5"],
];

const MONITOR_NUMBERS = [
  ["Advice", "Catching 76.1% of advice-style turns on its own, at 41.5% precision. Sending what it flags to a second model before rejecting raises precision to 51.7%, with 67.2% still caught."],
  ["False reassurance", "Catching 56.7% on its own, at 29.9% precision. The second look is more conservative here: precision rises to 34.0%, recall falls to 23.9%. ESConv's reassurance label includes validation our protocol wants, so this comparison is the noisier of the two."],
];

export default function Safety() {
  return (
    <div className="mx-auto max-w-4xl px-5 pb-10 pt-12">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-crisis">Safety</p>
      <h1 className="mt-3 font-serif text-4xl leading-tight md:text-5xl">When it matters most, ZenAI stops talking.</h1>
      <p className="mt-5 max-w-2xl text-lg text-ink2">
        A false alarm costs a student one awkward moment. A miss costs something we will not risk. So the crisis check is
        built to catch too much, it runs before anything else, and it keeps working when the rest of the system doesn't.
        This page is written for counseling directors deciding whether to pilot ZenAI on their campus.
      </p>

      <section aria-labelledby="layers" className="mt-12">
        <h2 id="layers" className="font-serif text-3xl">Three layers, before a reply is written</h2>
        <ol className="mt-6 space-y-3">
          {LAYERS.map((l) => (
            <li key={l.n} className="flex gap-4 rounded-3xl border border-line bg-card p-5">
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-crisis text-sm font-bold text-white">{l.n}</span>
              <div><h3 className="font-semibold">{l.title}</h3><p className="mt-1 text-[15px] leading-relaxed text-ink2">{l.body}</p></div>
            </li>
          ))}
        </ol>
        <p className="mt-4 text-[15px] text-ink2">If any layer reaches the threshold, the turn stops: no reply is generated, and the student sees 988 and the Morgan Counseling Center.</p>
      </section>

      <section aria-labelledby="promises" className="mt-12 rounded-[32px] border border-crisis/20 bg-crisisbg p-6 md:p-8">
        <h2 id="promises" className="font-serif text-3xl">What always holds</h2>
        <ul className="mt-5 space-y-3">
          {PROMISES.map((p) => (
            <li key={p} className="flex gap-3 text-[15.5px] leading-relaxed"><span aria-hidden className="mt-2 h-2 w-2 shrink-0 rounded-full bg-crisis" />{p}</li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="monitor" className="mt-12">
        <h2 id="monitor" className="font-serif text-3xl">What the Fidelity Monitor blocks</h2>
        <p className="mt-3 leading-relaxed text-ink2">
          Counselors are taught three things not to do: give advice, promise it will be fine, and label what someone is
          going through. Before a reply reaches a student, a trained detector scores it for the first two, and a short
          list of phrases ("you'll be fine", "you should") is blocked outright, whatever the scores say. A draft that
          drifts is rewritten, up to twice; if every rewrite still drifts, a fixed protocol-safe line goes instead.
        </p>
        <p className="mt-3 leading-relaxed text-ink2">
          Measured on 400 held-out turns from a published counseling-conversation dataset, the detector flagged a draft
          and a second model, given the written protocol, decided whether it truly drifts, on 222 of them:
        </p>
        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          {MONITOR_NUMBERS.map(([t, b]) => (
            <div key={t} className="rounded-3xl border border-line bg-card p-5">
              <h3 className="font-semibold">{t}</h3>
              <p className="mt-2 text-[15px] leading-relaxed text-ink2">{b}</p>
            </div>
          ))}
        </div>
        <p className="mt-4 text-[15px] leading-relaxed text-ink2">
          The second look also rescues good replies: of 16 drafts the detector alone rejected on its own by rule, a
          second model reading the full protocol passed all 16 on recheck.
        </p>
      </section>

      <section aria-labelledby="stored" className="mt-12">
        <h2 id="stored" className="font-serif text-3xl">What is never stored</h2>
        <ul className="mt-5 space-y-2 text-[15px] leading-relaxed text-ink2">
          <li>Nothing a student types is stored unless they turn it on. ZenAI's servers use a message to write a reply, then let it go.</li>
          <li>No message text appears in logs, analytics or error reports, in a crisis hand-off or otherwise.</li>
          <li>Spoken audio is never kept; it is turned into text in the browser and discarded.</li>
          <li>Memory notes and check-in history are off by default, and stay on the student's own device unless they sign in and turn on syncing.</li>
          <li>A Morgan email used to sign in is never stored as plain text, only as a scrambled, one-way version of it.</li>
        </ul>
        <p className="mt-4 text-sm text-muted">Full detail, including how long each thing is kept, is in <Link href="/privacy/" className="underline">Privacy</Link>.</p>
      </section>

      <section aria-labelledby="tested" className="mt-12">
        <h2 id="tested" className="font-serif text-3xl">How it was tested</h2>
        <p className="mt-3 leading-relaxed text-ink2">
          Red-team messages were written by other AI models trying to break ZenAI, then run through the full pipeline and
          judged by an independent auditor model, never the model being tested. The numbers below are from the held-out
          set: 40 cases written after the fixes below, by a different model than the one used to build the system, never
          tuned on.
        </p>
        <div className="mt-6 grid gap-3 sm:grid-cols-2 md:grid-cols-4">
          {HELD_OUT.map(([cat, score]) => (
            <div key={cat} className="rounded-3xl border border-line bg-card p-5">
              <p className="font-serif text-3xl text-crisis">{score}</p>
              <p className="mt-2 text-sm leading-snug text-ink2">{cat}</p>
            </div>
          ))}
        </div>
        <p className="mt-4 text-[15px] leading-relaxed text-ink2">
          38 of 40 held-out cases passed overall. The two misses, reported as they are: a 7-digit student number survived
          the redactor (fixed afterward; it now removes 7 to 10 digit IDs and "student number ..." forms), and an
          auditor flagged "it's okay to sit with that weight without pushing it away" as advice, which is Acceptance and
          Commitment Therapy acceptance wording that we chose to count as a miss anyway.
        </p>
        <p className="mt-3 leading-relaxed text-ink2">
          Separately, ZenAI was tested against 100 ordinary student messages, including hyperbole like "this exam is
          killing me": 0 of 100 set off a false alarm.
        </p>
        <p className="mt-5 rounded-2xl border border-line bg-paper2 p-4 text-sm leading-relaxed text-ink2">
          Every number on this page comes from our own red-team runs and rubric, judged by other AI models, not by
          licensed counselors or therapists. Human rating by counseling staff is in progress and has not happened yet.
          Read these as what our pipeline found on the test sets we built, not as a clinical outcome or a guarantee for
          any one student.
        </p>
        <p className="mt-4 text-sm text-muted">
          Test cases, replies and the misses are in the <a href="https://github.com/Chinonsocheq21/Zenai/tree/main/results/redteam" className="underline">repository</a>.
        </p>
      </section>

      <section className="mt-12 rounded-3xl bg-paper2 p-6 md:p-8">
        <h2 className="font-serif text-2xl">What ZenAI is not</h2>
        <p className="mt-3 leading-relaxed text-ink2">
          ZenAI is not a counselor, a therapist or an emergency service. It doesn't diagnose and it doesn't give advice. It
          gives students a calm place to put a thought into words, and connects them to people when that's what they need.
        </p>
        <Link href="/help/" className="mt-5 inline-block rounded-full bg-crisis px-5 py-3 font-semibold text-white hover:brightness-110">Get help now</Link>
      </section>

      <section aria-labelledby="report" className="mt-12">
        <h2 id="report" className="font-serif text-3xl">How to report a concern</h2>
        <p className="mt-3 leading-relaxed text-ink2">
          If something ZenAI said looks wrong, missed a sign it should have caught, or a student was put at risk, open an
          issue on <a href="https://github.com/Chinonsocheq21/Zenai/issues" className="underline">GitHub</a>, or use the{" "}
          <Link href="/contact/" className="underline">contact page</Link> for the pilot request form and a private way to
          reach the team on a security matter. Please leave out anything personal, and never paste what a student wrote to
          ZenAI.
        </p>
        <p className="mt-3 leading-relaxed text-ink2">
          If a student needs help right now, this is not that: call or text{" "}
          <a href="tel:988" className="font-semibold text-crisis underline">988</a> any time, or see{" "}
          <Link href="/help/" className="font-semibold text-crisis underline">Get help now</Link>.
        </p>
      </section>
    </div>
  );
}
