import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Terms",
  description: "The terms for using ZenAI, in plain words.",
};

const UPDATED = "November 6, 2026";

const TERMS: [string, React.ReactNode][] = [
  ["What ZenAI is", "ZenAI is a support chat built as a student capstone project at Morgan State University. It helps you put what you're carrying into words, using ideas from Acceptance and Commitment Therapy. It is free to use."],
  ["What ZenAI is not", "ZenAI is not a counselor, therapist, doctor or emergency service. It does not diagnose, treat or give advice, and it is not a substitute for professional care. Nothing it says is medical or psychological advice."],
  ["In a crisis", <>If you might hurt yourself or someone else, contact a person right away: call or text 988, or call 911. ZenAI will stop and show you these numbers if it notices you might be in crisis, but it can miss things and it cannot send help. <Link key="h" href="/help/" className="font-semibold text-crisis underline">Get help now</Link>.</>],
  ["Who it's for", "ZenAI is intended for college students who are 18 or older."],
  ["Using it fairly", "Please don't try to make ZenAI produce harmful content, overload it, or get around its usage limits or safety checks. ZenAI may pause or limit access to keep it working for everyone."],
  ["Replies can be wrong", "Replies are written by an AI model and checked automatically, but they can still be wrong, unhelpful or off the mark. Use your own judgment, and talk to a person about anything important."],
  ["Your privacy", <>How ZenAI handles what you type is described in the <Link key="p" href="/privacy/" className="font-semibold text-navy underline">privacy policy</Link>.</>],
  ["No guarantee", "ZenAI is provided as it is, while it is being developed. It may change, have downtime or stop being offered."],
  ["Changes", "These terms may change as ZenAI develops. The date at the top shows when they last changed."],
];

export default function Terms() {
  return (
    <article className="mx-auto max-w-3xl px-5 pb-10 pt-12">
      <p className="inline-block rounded-full bg-orange/15 px-3 py-1 text-xs font-semibold text-orange">Draft for review · last updated {UPDATED}</p>
      <h1 className="mt-4 font-serif text-4xl leading-tight md:text-5xl">Terms</h1>
      <p className="mt-4 text-lg text-ink2">By using ZenAI you agree to these terms. They are written to be read.</p>
      <ol className="mt-8 space-y-4">
        {TERMS.map(([t, b], i) => (
          <li key={t} className="rounded-3xl border border-line bg-card p-6">
            <h2 className="font-semibold"><span className="mr-2 text-orange">{i + 1}.</span>{t}</h2>
            <p className="mt-2 leading-relaxed text-ink2">{b}</p>
          </li>
        ))}
      </ol>
    </article>
  );
}
