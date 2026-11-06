import type { Metadata } from "next";
import Link from "next/link";
import PilotForm from "./PilotForm";

export const metadata: Metadata = {
  title: "For universities",
  description: "A between-appointments support chat that hands students to your counseling center, with a safety rail you can audit.",
};

const GIVES = [
  ["A first step at 2 a.m.", "Students can put what they're carrying into words any time, in a calm voice that never diagnoses, advises or promises it will be fine."],
  ["A hand-off to your people", "When a conversation needs a person, ZenAI stops and shows 988 and your counseling center. Your offices, your numbers, verified by your staff."],
  ["Replies you can audit", "Every reply is checked against a written protocol before a student sees it. The protocol, the tests and the results are public."],
  ["Trends, never transcripts", "In a pilot, your center sees anonymous weekly counts: conversations, how heavy check-ins felt, hand-offs. Never a student's words or identity, and nothing for groups under 10."],
];

const NEVER = [
  "Share any student's words, identity, or whether they use ZenAI with the university",
  "Sell, rent or advertise with anyone's data",
  "Present itself as a counselor or replace one",
  "Diagnose, give advice, or promise outcomes",
];

const PILOT = [
  ["Review", "Your clinicians read the protocol and the crisis rules, and tell us what to change."],
  ["Set up", "We load your verified offices and hours, and your campus email domain for sign-in."],
  ["Run", "A small, opt-in group of students uses ZenAI for a set number of weeks."],
  ["Look together", "We review the anonymous trends and the safety record with your team, and decide on next steps."],
];

export default function Universities() {
  return (
    <div>
      <section className="mx-auto max-w-5xl px-5 pb-12 pt-14">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-orange">For universities</p>
        <h1 className="mt-3 max-w-3xl font-serif text-4xl leading-tight md:text-6xl">Support between appointments, with a safety rail you can audit.</h1>
        <p className="mt-6 max-w-2xl text-lg leading-relaxed text-ink2">
          ZenAI gives students somewhere calm to turn when the counseling center is closed or booked, and it knows when to
          stop and send them to you. It was built and tested at Morgan State University.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <a href="#pilot" className="rounded-full bg-navy px-6 py-3.5 font-semibold text-white hover:bg-navy2">Request a pilot</a>
          <Link href="/safety/" className="rounded-full border border-line bg-card px-6 py-3.5 font-semibold hover:border-navy/40">See the safety design</Link>
        </div>
      </section>

      <section className="bg-paper2/60 py-14">
        <div className="mx-auto grid max-w-5xl gap-4 px-5 sm:grid-cols-2">
          {GIVES.map(([t, b]) => (
            <div key={t} className="rounded-3xl border border-line bg-card p-6">
              <h2 className="font-semibold">{t}</h2>
              <p className="mt-2 leading-relaxed text-ink2">{b}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto grid max-w-5xl gap-8 px-5 py-14 md:grid-cols-2">
        <div>
          <h2 className="font-serif text-3xl">What ZenAI never does</h2>
          <ul className="mt-5 space-y-3">
            {NEVER.map((n) => (
              <li key={n} className="flex gap-3 leading-relaxed text-ink2"><span aria-hidden className="mt-2.5 h-2 w-2 shrink-0 rounded-full bg-crisis" />{n}</li>
            ))}
          </ul>
        </div>
        <div className="rounded-3xl bg-ink p-7 text-white">
          <h2 className="font-serif text-3xl">The evidence, in the open</h2>
          <p className="mt-3 text-white/75">
            0 of 79 replies broke the protocol with the checks on, rated blind by two independent AI models. 10 of 10
            hidden crises caught on a held-out set, with 0 false alarms on 100 everyday messages. Human review is in
            progress.
          </p>
          <a href="https://github.com/Chinonsocheq21/Zenai/tree/main/results" className="mt-5 inline-block font-semibold text-[#f6b48a] hover:underline">Read the results and the misses →</a>
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-5 py-6">
        <h2 className="font-serif text-3xl md:text-4xl">What a pilot looks like</h2>
        <ol className="mt-6 grid gap-3 md:grid-cols-4">
          {PILOT.map(([t, b], i) => (
            <li key={t} className="rounded-3xl border border-line bg-card p-5">
              <span className="grid h-8 w-8 place-items-center rounded-full bg-orange text-sm font-bold text-white">{i + 1}</span>
              <h3 className="mt-3 font-semibold">{t}</h3>
              <p className="mt-1.5 text-[15px] leading-relaxed text-ink2">{b}</p>
            </li>
          ))}
        </ol>
        <p className="mt-5 text-ink2">Pilots are free while ZenAI is in development. ZenAI is not a clinical service, and a pilot runs alongside your center, never instead of it.</p>
      </section>

      <section id="pilot" className="mx-auto max-w-3xl scroll-mt-24 px-5 pt-14">
        <h2 className="font-serif text-3xl md:text-4xl">Request a pilot</h2>
        <p className="mt-3 text-ink2">Tell us about your campus and we'll reply by email.</p>
        <div className="mt-6"><PilotForm /></div>
      </section>
    </div>
  );
}
