import Link from "next/link";
import { pageMeta } from "@/components/meta";

export const metadata = pageMeta(
  "/get-the-app/",
  "Get the app",
  "Add ZenAI to your home screen on iPhone or Android. It opens full screen, like any other app, free and in seconds.",
);

const IPHONE_STEPS = [
  ["Open ZenAI in Safari.", "It has to be Safari. Chrome and other browsers on iPhone can't add it to your home screen."],
  ["Tap the Share icon.", "The square with an arrow pointing up, in the bar at the bottom of the screen."],
  ["Tap \"Add to Home Screen.\"", "Scroll down the share sheet if you don't see it right away."],
  ["Tap \"Add.\"", "The ZenAI icon lands on your home screen, ready to open like any other app."],
];

const ANDROID_STEPS = [
  ["Open ZenAI in Chrome.", "Most Android phones come with Chrome already installed."],
  ["Tap the menu (⋮) in the top right.", "Three dots in the top corner of the browser."],
  ["Tap \"Install app\" or \"Add to Home screen.\"", "The exact wording depends on your phone and Chrome version."],
  ["Tap \"Install\" to confirm.", "The ZenAI icon lands on your home screen and in your app drawer."],
];

function Steps({ title, steps }: { title: string; steps: string[][] }) {
  return (
    <section aria-labelledby={title} className="rounded-[32px] border border-line bg-card p-6 md:p-8">
      <h2 id={title} className="font-serif text-2xl">{title}</h2>
      <ol className="mt-6 space-y-5">
        {steps.map(([step, detail], i) => (
          <li key={step} className="flex gap-4">
            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-navy text-sm font-bold text-white">{i + 1}</span>
            <div>
              <p className="font-semibold">{step}</p>
              <p className="mt-1 text-[15px] text-ink2">{detail}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}

export default function GetTheApp() {
  return (
    <div className="mx-auto max-w-4xl px-5 pb-10 pt-12">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-orange">Get the app</p>
      <div className="mt-3 flex items-center gap-4">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/icons/icon-192.png" alt="" width={64} height={64} className="rounded-2xl" />
        <h1 className="font-serif text-4xl leading-tight md:text-5xl">Add ZenAI to your home screen.</h1>
      </div>
      <p className="mt-5 max-w-2xl text-lg text-ink2">
        ZenAI installs straight from the browser, free, with no app store. Once it's on your home screen it opens full
        screen, like any other app, and your Light, Dark or Match my phone choice carries over.
      </p>

      <div className="mt-10 grid gap-6 md:grid-cols-2">
        <Steps title="iPhone" steps={IPHONE_STEPS} />
        <Steps title="Android" steps={ANDROID_STEPS} />
      </div>

      <p className="mt-10 rounded-3xl bg-paper2 p-6 text-[15px] leading-relaxed text-ink2">
        Already on a laptop? Open{" "}
        <a href="/app/" className="font-semibold text-navy underline">zenai-app.vercel.app/app/</a> and bookmark it, or use the
        install icon in your browser's address bar.
      </p>

      <div className="mt-8 flex flex-wrap gap-3">
        <a href="/app/" className="rounded-full bg-navy px-6 py-3.5 font-semibold text-white hover:bg-navy2">Open ZenAI</a>
        <Link href="/help/" className="rounded-full border border-line bg-card px-6 py-3.5 font-semibold hover:border-navy/40">Get help now</Link>
      </div>
      <p className="mt-3 text-sm text-ink2">Sign in with your Morgan email or an invite code.</p>
    </div>
  );
}
