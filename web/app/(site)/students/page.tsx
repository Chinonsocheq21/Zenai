import Link from "next/link";
import { pageMeta } from "@/components/meta";

export const metadata = pageMeta(
  "/students/",
  "For students",
  "What ZenAI gives Morgan State students: a calm place to talk, a check-in, verified campus resources and a real crisis hand-off, shown in the real app.",
  "ZenAI for students",
);

const SCREENS = [
  ["app-chat.png", "Talk", "Say what's on your mind, in your own words. ZenAI listens, reflects it back, and asks one open question, never advice."],
  ["app-checkin.png", "Check in", "Tell it how heavy today is in one tap. No streaks, no score, just a shape for a few weeks."],
  ["app-findhelp.png", "Find help", "Every verified Morgan State office in one place, with a way to call or visit its website."],
  ["app-crisis.png", "Get help now", "The moment a conversation needs a person, ZenAI stops talking and shows 988 and the Counseling Center. This works even when ZenAI itself is down."],
] as const;

const PRIVACY = [
  "Nothing you type is stored unless you turn that on. ZenAI uses a message to write a reply, then lets it go.",
  "No message text ever appears in logs, analytics or error reports, in a crisis hand-off or otherwise.",
  "Your university never sees what you write or who you are. If your campus runs a pilot, it sees weekly totals only, and any number under 10 is hidden.",
];

export default function Students() {
  return (
    <div>
      <section className="mx-auto max-w-5xl px-5 pb-10 pt-14">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-orange">For students</p>
        <h1 className="mt-3 max-w-3xl font-serif text-4xl leading-tight md:text-6xl">A place to slow down, built for the hard weeks.</h1>
        <p className="mt-6 max-w-2xl text-lg leading-relaxed text-ink2">
          ZenAI is a support chat grounded in Acceptance and Commitment Therapy. Every reply is checked against the
          protocol before you see it, and the moment a conversation needs a person, ZenAI stops and hands you to one.
          Free for Morgan students.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <a href="/app/" className="rounded-full bg-navy px-6 py-3.5 font-semibold text-white shadow-lg shadow-navy/20 hover:bg-navy2">Open ZenAI</a>
          <Link href="/safety/" className="rounded-full border border-line bg-card px-6 py-3.5 font-semibold text-ink hover:border-navy/40">How it keeps you safe</Link>
        </div>
      </section>

      <section aria-labelledby="screens" className="bg-paper2/60 py-14">
        <div className="mx-auto max-w-5xl px-5">
          <h2 id="screens" className="font-serif text-3xl md:text-4xl">What you get</h2>
          <p className="mt-3 max-w-2xl text-ink2">The real app, not a mockup.</p>
          <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {SCREENS.map(([img, title, body]) => (
              <figure key={img} className="rounded-3xl border border-line bg-card p-4">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={`/media/app/${img}`} alt={`The ${title} screen in the ZenAI app`} width={390} height={844}
                  loading="lazy" decoding="async" className="h-auto w-full rounded-2xl border border-line" />
                <figcaption className="mt-3">
                  <p className="font-semibold">{title}</p>
                  <p className="mt-1 text-[14.5px] leading-relaxed text-ink2">{body}</p>
                </figcaption>
              </figure>
            ))}
          </div>
        </div>
      </section>

      <section aria-labelledby="signin" className="mx-auto max-w-5xl px-5 py-14">
        <h2 id="signin" className="font-serif text-3xl md:text-4xl">How sign-in works</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <div className="rounded-3xl border border-line bg-card p-6">
            <h3 className="font-semibold">With your Morgan email</h3>
            <p className="mt-2 leading-relaxed text-ink2">
              No password. We email a link that works once, for 15 minutes. ZenAI never stores your email address, only a
              scrambled code that recognizes it.
            </p>
          </div>
          <div className="rounded-3xl border border-line bg-card p-6">
            <h3 className="font-semibold">With an invite code</h3>
            <p className="mt-2 leading-relaxed text-ink2">
              If you were given an invite code instead, enter it in the same sign-in screen. Your check-ins follow you
              between your phone and laptop either way.
            </p>
          </div>
        </div>
        <p className="mt-4 text-ink2">
          You can delete your account any time from the app. <Link href="/signin/" className="font-semibold text-navy underline">Sign in</Link>.
        </p>
      </section>

      <section aria-labelledby="privacy" className="mx-auto max-w-5xl px-5 py-14">
        <h2 id="privacy" className="font-serif text-3xl md:text-4xl">Privacy, in three lines</h2>
        <ul className="mt-6 space-y-3">
          {PRIVACY.map((p) => (
            <li key={p} className="flex gap-3 rounded-3xl border border-line bg-card p-5 leading-relaxed text-ink2">
              <span aria-hidden className="mt-2 h-2 w-2 shrink-0 rounded-full bg-navy" />{p}
            </li>
          ))}
        </ul>
        <p className="mt-4 text-sm text-ink2">
          The full detail, including how long each thing is kept, is in <Link href="/privacy/" className="underline">Privacy</Link>.
        </p>
      </section>

      <section aria-labelledby="install" className="mx-auto max-w-5xl px-5 py-14">
        <h2 id="install" className="font-serif text-3xl md:text-4xl">How to install it</h2>
        <p className="mt-3 max-w-2xl text-ink2">
          ZenAI installs straight from the browser, free, with no app store. Once it is on your home screen it opens full
          screen, like any other app.
        </p>
        <Link href="/get-the-app/" className="mt-5 inline-block font-semibold text-navy hover:underline">See the steps for iPhone and Android →</Link>
      </section>

      <section className="mx-auto max-w-5xl px-5 py-10">
        <div className="flex flex-col items-center gap-5 rounded-[40px] bg-navy px-6 py-14 text-center text-white">
          <h2 className="font-serif text-3xl md:text-5xl">Take a minute for yourself.</h2>
          <p className="max-w-xl text-white/75">Free, private by default, and on any phone or laptop.</p>
          <a href="/app/" className="rounded-full bg-orangefill px-7 py-3.5 font-semibold text-ink hover:brightness-110">Open ZenAI</a>
          <p className="text-sm text-white/75">Sign in with your Morgan email or an invite code.</p>
        </div>
      </section>
    </div>
  );
}
