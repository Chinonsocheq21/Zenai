import Link from "next/link";
import { pageMeta } from "@/components/meta";
import PilotForm from "./PilotForm";

export const metadata = pageMeta(
  "/universities/",
  "For counseling centers",
  "A between-appointments support chat that hands students to your counseling center, with a safety rail you can audit. Pilots are free while ZenAI is in development.",
  "ZenAI for counseling centers",
);

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

const FAQ: [string, React.ReactNode][] = [
  ["What does it cost?", "Nothing. Pilots are free while ZenAI is in development."],
  ["What does our center actually see?", "Anonymous weekly counts only: conversations, how heavy check-ins felt, and hand-offs. Never a student's words or identity, and never a number under 10, so a small group can't be picked out."],
  ["Who runs ZenAI after the capstone ends?", "ZenAI is built by three Morgan State computer science students as a senior capstone. Who hosts and maintains it after the semester is not yet decided; the code, protocol and tests stay public on GitHub either way."],
  ["How long does a pilot take?", "A small, opt-in group of students uses ZenAI for a set number of weeks, agreed with your team during Set up, then we look at the trends and the safety record together."],
  ["What happens in a crisis?", "ZenAI stops talking and shows the student 988 and your Counseling Center. This still works if the language model, the database or the usage-limit store is down. See Safety for the full design."],
];

export default function Universities() {
  return (
    <div>
      <section className="mx-auto max-w-5xl px-5 pb-12 pt-14">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-orange">For counseling centers</p>
        <h1 className="mt-3 max-w-3xl font-serif text-4xl leading-tight md:text-6xl">Support between appointments, with a safety rail you can audit.</h1>
        <p className="mt-6 max-w-2xl text-lg leading-relaxed text-ink2">
          ZenAI gives students somewhere calm to turn when the counseling center is closed or booked, and it knows when to
          stop and send them to you. It was built by Morgan State computer science students as a senior capstone, and
          tested with Morgan's verified resources.
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
            In a blind test, two independent AI raters found no protocol breaks in 79 replies with the Fidelity Monitor
            on. With it off, one rater flagged 6 of 79 and the other none, so the test does not yet show how much the
            monitor adds. Human review of the same replies is in progress, and we will publish it whatever it shows. 10
            of 10 hidden crises were caught on a held-out set, with 0 false alarms on 100 everyday messages.
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
        <p className="mt-3 text-ink2">
          For your IT and accessibility reviewers: <Link href="/security/" className="font-semibold text-navy underline">Security and subprocessors</Link>,{" "}
          <Link href="/privacy/" className="font-semibold text-navy underline">Privacy</Link> and the{" "}
          <Link href="/accessibility/" className="font-semibold text-navy underline">Accessibility statement</Link>.
        </p>
      </section>

      <section aria-labelledby="dashboard" className="bg-paper2/60 py-14">
        <div className="mx-auto max-w-5xl px-5">
          <h2 id="dashboard" className="font-serif text-3xl md:text-4xl">What your team actually sees</h2>
          <p className="mt-3 max-w-2xl text-ink2">
            A campus dashboard of anonymous weekly counts, behind your pilot's own access code. Never a student's words
            or identity, and never a number under 10.
          </p>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/media/dashboard-preview.png" alt="The pilot dashboard's sign-in screen, asking for a pilot access code"
            loading="lazy" className="mt-6 w-full max-w-2xl rounded-3xl border border-line shadow-xl shadow-ink/10" />
        </div>
      </section>

      <section aria-labelledby="faq" className="mx-auto max-w-5xl px-5 py-14">
        <h2 id="faq" className="font-serif text-3xl md:text-4xl">Questions directors ask</h2>
        <dl className="mt-6 grid gap-4 sm:grid-cols-2">
          {FAQ.map(([q, a]) => (
            <div key={q} className="rounded-3xl border border-line bg-card p-6">
              <dt className="font-semibold">{q}</dt>
              <dd className="mt-2 leading-relaxed text-ink2">{a}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section aria-labelledby="built" className="mx-auto max-w-5xl px-5 pb-6">
        <h2 id="built" className="font-serif text-2xl md:text-3xl">Who built it</h2>
        <p className="mt-3 max-w-2xl text-ink2">
          ZenAI is a senior capstone project by three Morgan State computer science students: Abraham Irabor, Fnu Soh Tah
          Fon and Chinonso Egeolu.
        </p>
      </section>

      <section id="pilot" className="mx-auto max-w-3xl scroll-mt-24 px-5 pt-8">
        <h2 className="font-serif text-3xl md:text-4xl">Request a pilot</h2>
        <p className="mt-3 text-ink2">Tell us about your campus and we'll reply by email.</p>
        <div className="mt-6"><PilotForm /></div>
      </section>

      <section className="mx-auto max-w-5xl px-5 py-16">
        <div className="flex flex-col items-center gap-5 rounded-[40px] bg-navy px-6 py-12 text-center text-white">
          <h2 className="font-serif text-3xl">See the safety design before you ask your clinicians to.</h2>
          <Link href="/safety/" className="rounded-full bg-orangefill px-7 py-3.5 font-semibold text-ink hover:brightness-110">Read the safety design</Link>
        </div>
      </section>
    </div>
  );
}
