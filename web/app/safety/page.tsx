import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Safety",
  description: "How ZenAI notices a crisis and hands the student to a person, even when the AI is down.",
};

const LAYERS = [
  { n: "1", title: "Clear crisis language", body: "Phrases that name suicide, self-harm or wanting to die are caught by fixed rules before any language model sees the message. The turn stops there." },
  { n: "2", title: "The whole conversation", body: "Quieter signs (\"what's the point\", \"I just want it to stop\") count more when they follow earlier ones or a heavy check-in. A crisis earlier in the conversation keeps it in crisis, even if the next message sounds calm." },
  { n: "3", title: "A second look by a model", body: "A fast model screens for indirect language the rules can't list. It can only raise the risk, never lower it." },
];

const PROMISES = [
  "If the AI is down, or ZenAI is busy, the crisis check still runs on the rules and still hands off. A student in crisis is never told to come back later.",
  "Checking in as \"I'm not okay\" goes straight to the hand-off, before any chat.",
  "During a hand-off there is no text box. ZenAI doesn't try to talk anyone down; it shows people who can help.",
  "After \"I'm safe, take me back\", 988 and the Counseling Center stay pinned for the rest of the conversation.",
  "Every Morgan phone number comes from a verified list, never from the model.",
];

const NUMBERS = [
  ["10 of 10", "hidden crises caught on a held-out test set the system was never tuned on"],
  ["0 of 100", "false alarms on everyday student messages"],
  ["0 of 11", "false alarms on hyperbole like \"this exam is killing me\""],
];

export default function Safety() {
  return (
    <div className="mx-auto max-w-4xl px-5 pb-10 pt-12">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-crisis">Safety</p>
      <h1 className="mt-3 font-serif text-4xl leading-tight md:text-5xl">When it matters most, ZenAI stops talking.</h1>
      <p className="mt-5 max-w-2xl text-lg text-ink2">
        A false alarm costs a student one awkward moment. A miss costs something we will not risk. So the crisis check is
        built to catch too much, it runs before anything else, and it keeps working when the rest of the system doesn't.
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

      <section aria-labelledby="tested" className="mt-12">
        <h2 id="tested" className="font-serif text-3xl">How it was tested</h2>
        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          {NUMBERS.map(([big, what]) => (
            <div key={what} className="rounded-3xl border border-line bg-card p-5">
              <p className="font-serif text-4xl text-crisis">{big}</p>
              <p className="mt-2 text-sm leading-snug text-ink2">{what}</p>
            </div>
          ))}
        </div>
        <p className="mt-4 text-sm text-muted">
          Test messages were written by other AI models, not by us, and the held-out set was kept aside until the end.
          Results and the misses are in the <a href="https://github.com/Chinonsocheq21/Zenai/tree/main/results/redteam" className="underline">repository</a>.
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
    </div>
  );
}
