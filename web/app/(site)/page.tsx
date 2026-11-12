import Link from "next/link";
import { pageMeta } from "@/components/meta";
import Orb from "@/components/Orb";

export const metadata = {
  ...pageMeta(
    "/",
    "ZenAI",
    "A support chat for Morgan State students, grounded in Acceptance and Commitment Therapy. Every reply is checked before a student sees it, and a crisis is handed to a person.",
    "ZenAI · A place to slow down for a minute",
  ),
  title: { absolute: "ZenAI · A place to slow down for a minute" },
};

const MOVES = [
  { name: "Advice", bad: "Try breaking your notes into 25-minute blocks.", good: "What would a small step look like, for you?" },
  { name: "Reassurance", bad: "Don't worry, you'll do great!", good: "It makes sense you'd feel that way." },
  { name: "Diagnosis", bad: "Sounds like test anxiety.", good: "Anxious is the word you used. What does it feel like right now?" },
];

const STAGES = [
  ["Privacy", "Names, emails, phone numbers and student IDs are removed before anything reads the message."],
  ["Crisis check", "Reads the whole conversation and today's check-in. If there is risk, the turn stops and 988 and the Counseling Center take over."],
  ["Mood", "A distress classifier reads how the message lands."],
  ["Route", "Picks a focus: Academic Stress, Stress-Relief, Wellness Schedule, or Resource and Referral."],
  ["Memory", "Only notes the student chose to keep, stored on their own device and sent with the message."],
  ["Draft", "The reply is written on the ACT protocol: reflect, notice, values, one open question."],
  ["Fidelity Monitor", "A trained detector, a second opinion, and phrases that can never be sent. A drifting draft is rewritten."],
  ["Send", "Only a reply that passed. If every rewrite drifts, a fixed protocol-safe line goes instead."],
];

const RESULTS = [
  { big: "0 of 79", what: "replies flagged as breaking the protocol with the Fidelity Monitor on", how: "Experiment E1: two independent AI raters marked the replies blind against the written protocol. With the monitor off, one rater flagged 6 of 79 and the other 0 of 79, so this test does not yet show how much the monitor adds. Human review is in progress." },
  { big: "10/10", what: "hidden crises caught on a held-out test set", how: "Indirect and multi-message risk. Keyword rules alone caught 1 of 12 before the conversation-aware check." },
  { big: "0/100", what: "false alarms on everyday student messages", how: "Plus 0 of 11 on hyperbole like \"this exam is killing me\"." },
  { big: "38/40", what: "attacks handled on a held-out red-team set", how: "Jailbreaks, \"just tell me I'll pass\", \"do I have ADHD?\", prompt injection, privacy." },
  { big: "100%", what: "of messages routed to the right focus", how: "100 held-out messages. Keyword rules alone: 69%." },
  { big: "2.4 s", what: "median reply time, checks included", how: "Down from 8.4 s after moving drafts to a faster model, with no rise in drift." },
];

const PROOF = [
  ["10 of 10", "hidden crises caught on the held-out set"],
  ["Nothing", "kept unless the student turns it on"],
  ["2.4 s", "median reply, every one checked first"],
] as const;

const SCREENS = [
  ["checkin-first.webp", "It starts by asking how heavy today is.", 856],
  ["02-chat.webp", "Then it listens and reflects back what it heard.", 844],
  ["03-resources.webp", "Ask where to get help: verified Morgan offices, never invented.", 844],
  ["07-crisis.webp", "When it matters most, it stops and hands you to a person.", 844],
] as const;

function Eyebrow({ children }: { children: React.ReactNode }) {
  return <p className="text-xs font-semibold uppercase tracking-[0.18em] text-orange">{children}</p>;
}

export default function Home() {
  return (
    <>
      {/* hero */}
      <section className="relative overflow-hidden">
        <div aria-hidden className="pointer-events-none absolute inset-0 bg-[radial-gradient(60%_50%_at_85%_0%,rgba(232,116,46,.18),transparent_70%)]" />
        <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-5 pb-16 pt-14 md:grid-cols-[1.1fr_1fr] md:pt-20">
          <div>
            <Eyebrow>For Morgan State students</Eyebrow>
            <h1 className="mt-4 font-serif text-[44px] leading-[1.03] tracking-tight md:text-[68px]">A place to slow down for a minute.</h1>
            <p className="mt-6 max-w-xl text-xl leading-relaxed text-ink2">
              A private support chat for the hard weeks: it listens, asks one good question, and hands you to a person the
              moment you need one.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <a href="/app/" className="rounded-full bg-navy px-6 py-3.5 font-semibold text-white shadow-lg shadow-navy/20 hover:bg-navy2">Open ZenAI</a>
              <Link href="/universities/" className="rounded-full border border-line bg-card px-6 py-3.5 font-semibold text-ink hover:border-navy/40">I run a counseling center</Link>
            </div>
            <p className="mt-5 text-sm text-muted">
              Free for Morgan students. Not a counselor. In crisis, call or text{" "}
              <a href="tel:988" className="font-semibold text-crisis underline">988</a>.
            </p>
            <div className="mt-8 grid max-w-xl grid-cols-3 gap-3">
              {PROOF.map(([big, what]) => (
                <div key={what} className="rounded-2xl border border-line bg-card/70 px-4 py-3">
                  <p className="font-serif text-2xl text-navy">{big}</p>
                  <p className="mt-1 text-[13px] leading-snug text-ink2">{what}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="relative hidden md:block">
            <div className="relative mx-auto aspect-[4/3] max-w-lg">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/media/app/app-laptop-talk.png" alt="ZenAI's Talk screen, open on a laptop" width={700} height={437}
                className="absolute right-0 top-2 w-[82%] rounded-xl border-[8px] border-ink shadow-2xl shadow-ink/25" />
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/media/app/app-chat.png" alt="ZenAI's Talk screen, open on a phone" width={390} height={844}
                className="absolute bottom-0 left-0 w-[34%] rounded-[22px] border-[6px] border-ink shadow-2xl shadow-ink/30" />
            </div>
          </div>
          <div className="md:hidden">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/media/app/app-chat.png" alt="ZenAI's Talk screen, open on a phone" width={390} height={844}
              className="mx-auto w-48 rounded-[22px] border-[6px] border-ink shadow-xl shadow-ink/20" />
          </div>
        </div>
      </section>

      {/* the problem */}
      <section className="mx-auto max-w-6xl px-5 py-16">
        <Eyebrow>The problem</Eyebrow>
        <h2 className="mt-3 max-w-3xl font-serif text-3xl leading-tight md:text-[42px]">Chatbots are trained to help. Here, "helping" is often the wrong move.</h2>
        <p className="mt-5 max-w-2xl text-lg text-ink2">
          Counselors are taught not to give advice, not to promise it will be fine, and not to label what someone is going
          through. General chatbots do all three by default. ZenAI is built so that it can't send a reply that does.
        </p>
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {MOVES.map((m) => (
            <div key={m.name} className="rounded-3xl border border-line bg-card p-6">
              <h3 className="font-semibold">{m.name}</h3>
              <p className="mt-4 rounded-2xl bg-crisisbg px-4 py-3 text-[15px] text-crisis line-through decoration-crisis/50">"{m.bad}"</p>
              <p className="mt-3 rounded-2xl bg-[#e6f3ec] px-4 py-3 text-[15px] text-calm">"{m.good}"</p>
            </div>
          ))}
        </div>
      </section>

      {/* the app */}
      <section className="bg-paper2/60 py-16">
        <div className="mx-auto max-w-6xl px-5">
          <Eyebrow>The app</Eyebrow>
          <h2 className="mt-3 font-serif text-3xl md:text-[42px]">On your phone or your laptop.</h2>
          <div className="mt-10 grid grid-cols-2 gap-5 md:grid-cols-4">
            {SCREENS.map(([img, cap, h]) => (
              <figure key={img}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={`/media/${img}`} alt={cap} width={390} height={h} loading="lazy" decoding="async" className="h-auto w-full rounded-[28px] border-[6px] border-ink shadow-xl shadow-ink/15" />
                <figcaption className="mt-3 text-sm leading-snug text-ink2">{cap}</figcaption>
              </figure>
            ))}
          </div>
        </div>
      </section>

      {/* how a message moves */}
      <section className="mx-auto max-w-6xl px-5 py-16">
        <Eyebrow>How a message moves</Eyebrow>
        <h2 className="mt-3 font-serif text-3xl md:text-[42px]">Eight stages, in the order that keeps students safe.</h2>
        <p className="mt-5 max-w-2xl text-lg text-ink2">Privacy and the crisis check run before a language model writes a word. The Fidelity Monitor runs after it, on every draft.</p>
        <ol className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {STAGES.map(([name, what], i) => (
            <li key={name} className={`rounded-3xl border p-5 ${name === "Crisis check" || name === "Fidelity Monitor" ? "border-navy bg-navy text-white" : "border-line bg-card"}`}>
              <span className="grid h-8 w-8 place-items-center rounded-full bg-orange text-sm font-bold text-white">{i + 1}</span>
              <h3 className="mt-3 font-semibold">{name}</h3>
              <p className={`mt-1.5 text-[14.5px] leading-relaxed ${name === "Crisis check" || name === "Fidelity Monitor" ? "text-white/80" : "text-ink2"}`}>{what}</p>
            </li>
          ))}
        </ol>
        <Link href="/how-it-works/" className="mt-8 inline-block font-semibold text-navy hover:underline">More on how it works →</Link>
      </section>

      {/* results */}
      <section className="bg-ink py-16 text-white">
        <div className="mx-auto max-w-6xl px-5">
          <Eyebrow>What we measured</Eyebrow>
          <h2 className="mt-3 font-serif text-3xl md:text-[42px]">Numbers from the running system.</h2>
          <p className="mt-5 max-w-2xl text-white/70">
            Test messages were written by other AI models so ZenAI was never graded on examples shaped to fit it, and replies were judged by models that did not write them.
          </p>
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {RESULTS.map((r) => (
              <div key={r.what} className="rounded-3xl border border-white/10 bg-white/5 p-6">
                <p className="font-serif text-5xl text-[#f6b48a]">{r.big}</p>
                <p className="mt-3 font-semibold">{r.what}</p>
                <p className="mt-2 text-sm leading-relaxed text-white/60">{r.how}</p>
              </div>
            ))}
          </div>
          <p className="mt-8 text-sm text-white/60">
            Every number links to code and data in the{" "}
            <a href="https://github.com/Chinonsocheq21/Zenai/tree/main/results" className="underline hover:text-white">repository</a>, misses included.
          </p>
        </div>
      </section>

      {/* safety + privacy */}
      <section className="mx-auto grid max-w-6xl gap-6 px-5 py-16 md:grid-cols-2">
        <div className="rounded-3xl border border-crisis/20 bg-crisisbg p-8">
          <Eyebrow>Safety</Eyebrow>
          <h2 className="mt-3 font-serif text-3xl">When it matters most, ZenAI stops talking.</h2>
          <p className="mt-4 text-ink2">A false alarm costs one awkward moment. A miss costs something we will not risk, so the crisis check is built to catch too much, and it still works when the AI is down.</p>
          <Link href="/safety/" className="mt-6 inline-block font-semibold text-crisis hover:underline">How the crisis check works →</Link>
        </div>
        <div className="rounded-3xl border border-line bg-card p-8">
          <Eyebrow>Privacy</Eyebrow>
          <h2 className="mt-3 font-serif text-3xl">Nothing is kept unless you say so.</h2>
          <p className="mt-4 text-ink2">Memory, check-in history and the conversation are all off by default. What you choose to keep stays on your device, and one tap deletes it. Your university never sees what you write or who you are. If your campus runs a pilot, it sees weekly totals only, and any number under 10 is hidden.</p>
          <Link href="/privacy/" className="mt-6 inline-block font-semibold text-navy hover:underline">Read the privacy policy →</Link>
        </div>
      </section>

      {/* for counseling centers */}
      <section aria-labelledby="centers" className="mx-auto max-w-6xl px-5 pb-6">
        <div className="flex flex-col gap-5 rounded-3xl border border-navy/20 bg-card p-8 md:flex-row md:items-center md:justify-between">
          <div className="max-w-2xl">
            <Eyebrow>For counseling centers</Eyebrow>
            <h2 id="centers" className="mt-3 font-serif text-3xl">Support between appointments, handed back to your staff.</h2>
            <p className="mt-3 text-ink2">
              ZenAI runs alongside your center, never instead of it. Pilots are free while ZenAI is in development, and your
              team sees anonymous weekly trends, never a student's words.
            </p>
          </div>
          <Link href="/universities/" className="shrink-0 self-start rounded-full bg-navy px-6 py-3.5 font-semibold text-white hover:bg-navy2 md:self-center">
            For counseling centers
          </Link>
        </div>
      </section>

      {/* film */}
      <section id="film" className="mx-auto max-w-4xl px-5 py-10 text-center">
        <Eyebrow>The film</Eyebrow>
        <h2 className="mt-3 font-serif text-3xl md:text-[42px]">ZenAI in a minute.</h2>
        <video className="mt-8 h-auto w-full rounded-3xl border border-line shadow-2xl shadow-ink/20" src="/media/zenai-film.mp4"
          poster="/media/film-poster.webp" width={1280} height={720} controls preload="none" playsInline>
          <track kind="captions" srcLang="en" label="English" src="/media/zenai-film.en.vtt" default />
        </video>
        <p className="mt-4 text-sm text-ink2">
          Captions are on by default.{" "}
          <a href="/media/zenai-film-transcript.txt" className="font-semibold text-navy underline underline-offset-4 hover:text-orange">
            Read the transcript
          </a>
        </p>
      </section>

      {/* closing call */}
      <section className="mx-auto max-w-6xl px-5 pt-16">
        <div className="flex flex-col items-center gap-6 rounded-[40px] bg-navy px-6 py-14 text-center text-white">
          <Orb size={72} />
          <h2 className="font-serif text-3xl md:text-5xl">Take a minute for yourself.</h2>
          <p className="max-w-xl text-white/75">Free, private by default, and on any phone or laptop. Add it to your home screen and it opens like an app.</p>
          <a href="/app/" className="rounded-full bg-orangefill px-7 py-3.5 font-semibold text-ink hover:brightness-110">Open ZenAI</a>
          <p className="text-sm text-white/75">Sign in with your Morgan email or an invite code.</p>
        </div>
      </section>
    </>
  );
}
