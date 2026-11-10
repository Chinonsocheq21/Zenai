import Link from "next/link";
import { pageMeta } from "@/components/meta";

export const metadata = pageMeta(
  "/accessibility/",
  "Accessibility",
  "ZenAI's accessibility status: what we aim for, what we have checked, the gaps we know about, and how to report a problem.",
  "ZenAI accessibility statement",
);

const UPDATED = "November 9, 2026";

const WORKS = [
  "A skip link to the main content on every site page, and a visible focus outline on every link, button and form field.",
  "Real labels on every form field, with errors announced to screen readers.",
  "The site and the app respect your device's reduce-motion setting, so the breathing orb stops moving.",
  "The site works at phone, tablet and laptop widths without sideways scrolling.",
  "You can talk instead of type, and ZenAI can read its replies aloud.",
];

const GAPS = [
  "When the app's crisis screen opens, keyboard focus does not yet move into it, and screen readers may not announce it. This is the most important gap and is first to fix.",
  "On a laptop, the crisis screen's Call and Text 988 links depend on the device having a phone app, and there is not yet a link to the 988 online chat. The site's Get help now page lists the Counseling Center's numbers and offices.",
  "In the app, the Account panel does not yet close with the Escape key, and focus stays on the button that opened it.",
  "The app's message box has a faint focus outline that is hard to see.",
  "The app's conversation is not yet marked as a live log for screen readers, and one part of the app's sidebar sits outside a page landmark.",
  "The film on the home page has no captions or transcript yet.",
  "Some pages may still have small text with lower contrast than WCAG 2.1 AA requires. We fixed the colors we found and are rechecking every page.",
];

export default function Accessibility() {
  return (
    <article className="mx-auto max-w-3xl px-5 pb-10 pt-12">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-orange">Accessibility · last updated {UPDATED}</p>
      <h1 className="mt-3 font-serif text-4xl leading-tight md:text-5xl">Accessibility</h1>
      <p className="mt-5 text-lg leading-relaxed text-ink2">
        ZenAI should work for every student, including students who use a screen reader, a keyboard, voice, zoom or high
        contrast. We are aiming for WCAG 2.1 level AA on the website and the app. We do not meet it fully yet, and this page
        says where we fall short.
      </p>

      <section aria-labelledby="checked" className="mt-10">
        <h2 id="checked" className="font-serif text-2xl md:text-3xl">What we have checked</h2>
        <div className="mt-3 space-y-3 leading-relaxed text-ink2">
          <p>
            Every page of the site and the main screens of the app were checked with an automated accessibility checker
            (axe) and by keyboard, at phone and laptop sizes, in November 2026. The site's only automated failures were
            color contrast, and we have since darkened the orange and grey used for text. Automated checks catch only part
            of what matters, and ZenAI has not yet had an outside accessibility audit or testing with assistive technology
            users.
          </p>
        </div>
      </section>

      <section aria-labelledby="works" className="mt-10">
        <h2 id="works" className="font-serif text-2xl md:text-3xl">What works today</h2>
        <ul className="mt-3 list-disc space-y-2 pl-5 leading-relaxed text-ink2">
          {WORKS.map((w) => <li key={w}>{w}</li>)}
        </ul>
      </section>

      <section aria-labelledby="gaps" className="mt-10">
        <h2 id="gaps" className="font-serif text-2xl md:text-3xl">Known gaps</h2>
        <ul className="mt-3 list-disc space-y-2 pl-5 leading-relaxed text-ink2">
          {GAPS.map((g) => <li key={g}>{g}</li>)}
        </ul>
      </section>

      <section aria-labelledby="report" className="mt-10">
        <h2 id="report" className="font-serif text-2xl md:text-3xl">Report a problem</h2>
        <div className="mt-3 space-y-3 leading-relaxed text-ink2">
          <p>
            If something on ZenAI is hard or impossible for you to use, please tell us through the{" "}
            <Link href="/contact/" className="font-semibold text-navy underline">contact page</Link>. Say which page or
            screen, what you were trying to do, and the device, browser and any assistive technology you use. Please don't
            include anything personal you wrote to ZenAI.
          </p>
          <p>
            If you need support right now, you don't need ZenAI to get it.{" "}
            <Link href="/help/" className="font-semibold text-crisis underline">Get help now</Link> lists 988 and Morgan's
            offices, with no sign-in.
          </p>
        </div>
      </section>
    </article>
  );
}
