import type { Metadata } from "next";
import Link from "next/link";
import SiteFooter from "@/components/SiteFooter";
import SiteHeader from "@/components/SiteHeader";

export const metadata: Metadata = {
  title: "Page not found",
  description: "This page doesn't exist. Head home, or reach a person now.",
  robots: { index: false },
};

export default function NotFound() {
  // The root 404 renders under the root layout only, so it brings the site frame itself.
  return (
    <>
    <SiteHeader />
    <main id="main">
    <div className="mx-auto max-w-2xl px-5 pb-16 pt-16 text-center md:pt-24">
      <div
        aria-hidden="true"
        className="mx-auto h-16 w-16 rounded-full"
        style={{ background: "radial-gradient(circle at 35% 30%, #FFD9B0 0, #F08A4B 45%, #1B3D6F 100%)" }}
      />
      <p className="mt-6 text-xs font-semibold uppercase tracking-[0.18em] text-orange">404</p>
      <h1 className="mt-3 font-serif text-4xl leading-tight md:text-5xl">This page took a different path.</h1>
      <p className="mx-auto mt-4 max-w-lg text-lg text-ink2">
        We couldn't find what you were looking for. It may have moved, or the link may be off by a letter.
      </p>
      <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
        <Link href="/" className="rounded-full bg-navy px-6 py-3 font-semibold text-white hover:bg-navy2">
          Home
        </Link>
        <Link href="/help/" className="rounded-full bg-crisis px-6 py-3 font-semibold text-white hover:brightness-110">
          Get help now
        </Link>
      </div>
      <p className="mt-8 text-sm text-muted">
        If you might not be safe, call or text <a href="tel:988" className="font-semibold text-crisis underline">988</a>, any time.
      </p>
    </div>
    </main>
    <SiteFooter />
    </>
  );
}
