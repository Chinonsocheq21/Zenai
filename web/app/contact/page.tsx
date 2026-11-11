import Link from "next/link";
import { pageMeta } from "@/components/meta";
import NextStep from "@/components/NextStep";

export const metadata = pageMeta(
  "/contact/",
  "Contact",
  "How to reach the ZenAI team: the pilot form for universities, GitHub for everything else.",
  "Contact ZenAI",
);

const ISSUES = "https://github.com/Chinonsocheq21/Zenai/issues";

const WAYS: { who: string; how: React.ReactNode }[] = [
  {
    who: "Counseling centers and universities",
    how: (
      <>
        Use the <Link href="/universities/#pilot" className="font-semibold text-navy underline">pilot request form</Link>.
        It comes straight to the team, and we reply by email.
      </>
    ),
  },
  {
    who: "Questions, feedback, privacy and accessibility",
    how: (
      <>
        Open an issue on <a href={ISSUES} className="font-semibold text-navy underline">GitHub</a>. Issues are public, so
        please leave out anything personal, and never paste what you wrote to ZenAI.
      </>
    ),
  },
  {
    who: "A security problem",
    how: (
      <>
        Don't post the details in public. Open a <a href={ISSUES} className="font-semibold text-navy underline">GitHub issue</a>{" "}
        titled "Security contact" with no details, and we will reply there to set up a private way to talk. See{" "}
        <Link href="/security/" className="font-semibold text-navy underline">Security</Link> for how ZenAI is run.
      </>
    ),
  },
];

export default function Contact() {
  return (
    <article className="mx-auto max-w-3xl px-5 pb-10 pt-12">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-orange">Contact</p>
      <h1 className="mt-3 font-serif text-4xl leading-tight md:text-5xl">Reach the ZenAI team</h1>

      <p className="mt-6 rounded-2xl border border-crisis/20 bg-crisisbg px-5 py-4 leading-relaxed text-crisis">
        If you need support right now, this is not the way to get it: nobody watches these channels around the clock. Call
        or text <a href="tel:988" className="font-bold underline">988</a> any time, or see{" "}
        <Link href="/help/" className="font-bold underline">Get help now</Link>.
      </p>

      <p className="mt-6 text-lg leading-relaxed text-ink2">
        ZenAI is a small team, and there is no contact form or public email address yet. These are the ways to reach us
        today.
      </p>

      <dl className="mt-8 space-y-3">
        {WAYS.map((w) => (
          <div key={w.who} className="rounded-3xl border border-line bg-card p-6">
            <dt className="font-semibold">{w.who}</dt>
            <dd className="mt-2 leading-relaxed text-ink2">{w.how}</dd>
          </div>
        ))}
      </dl>
      <NextStep href="/help/" label="Get help now" />
    </article>
  );
}
