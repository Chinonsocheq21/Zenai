import Link from "next/link";
import Orb from "./Orb";

export default function SiteFooter() {
  return (
    <footer className="mt-24 border-t border-line bg-paper2/60">
      <div className="mx-auto grid max-w-6xl gap-10 px-5 py-12 md:grid-cols-[1.4fr_1fr_1fr]">
        <div>
          <div className="flex items-center gap-2.5"><Orb size={26} /><span className="font-serif text-xl">ZenAI</span></div>
          <p className="mt-3 max-w-sm text-sm leading-relaxed text-ink2">
            A place to slow down for a minute. ZenAI is not a counselor and does not replace one.
          </p>
          <p className="mt-4 rounded-2xl border border-crisis/20 bg-crisisbg px-4 py-3 text-sm text-crisis">
            In crisis? Call or text <a href="tel:988" className="font-bold underline">988</a>, any time.
            Morgan Counseling Center: <a href="tel:4438853130" className="font-bold underline">443-885-3130</a>.
          </p>
        </div>
        <nav aria-label="Product" className="text-sm">
          <h2 className="mb-3 font-semibold text-ink">ZenAI</h2>
          <ul className="space-y-2 text-ink2">
            <li><a href="/app/" className="hover:text-navy">Try ZenAI</a></li>
            <li><Link href="/signin/" className="hover:text-navy">Sign in</Link></li>
            <li><Link href="/how-it-works/" className="hover:text-navy">How it works</Link></li>
            <li><Link href="/safety/" className="hover:text-navy">Safety</Link></li>
            <li><Link href="/help/" className="hover:text-navy">Get help now</Link></li>
          </ul>
        </nav>
        <nav aria-label="About" className="text-sm">
          <h2 className="mb-3 font-semibold text-ink">About</h2>
          <ul className="space-y-2 text-ink2">
            <li><Link href="/universities/" className="hover:text-navy">For universities</Link></li>
            <li><Link href="/privacy/" className="hover:text-navy">Privacy</Link></li>
            <li><Link href="/terms/" className="hover:text-navy">Terms</Link></li>
            <li><a href="https://github.com/Chinonsocheq21/Zenai" className="hover:text-navy">Source on GitHub</a></li>
          </ul>
        </nav>
      </div>
      <p className="border-t border-line px-5 py-5 text-center text-xs text-muted">
        ZenAI · COSC 490 Capstone · Morgan State University · {new Date().getFullYear()}
      </p>
    </footer>
  );
}
