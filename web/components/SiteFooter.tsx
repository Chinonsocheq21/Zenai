import Link from "next/link";
import Orb from "./Orb";
import ThemeSwitch from "./ThemeSwitch";

export default function SiteFooter() {
  return (
    <footer className="mt-24 border-t border-line bg-paper2/60">
      <div className="mx-auto grid max-w-5xl gap-10 px-5 py-12 sm:grid-cols-2">
        <div>
          <div className="flex items-center gap-2.5"><Orb size={26} /><span className="font-serif text-xl">ZenAI</span></div>
          <p className="mt-3 max-w-sm text-sm leading-relaxed text-ink2">
            A place to slow down for a minute. ZenAI is not a counselor and does not replace one.
          </p>
          <p className="mt-4 rounded-2xl border border-crisis/20 bg-crisisbg px-4 py-3 text-sm text-crisis">
            In crisis? Call or text <a href="tel:988" className="font-bold underline">988</a>, any time.
            Morgan Counseling Center: <a href="tel:4438853130" className="font-bold underline">443-885-3130</a>.
          </p>
          <div className="mt-6"><ThemeSwitch /></div>
        </div>
        <div className="grid gap-10 sm:grid-cols-2">
          <nav aria-label="Trust" className="text-sm">
            <h2 className="mb-3 font-semibold text-ink">Trust</h2>
            <ul className="space-y-2 text-ink2">
              <li><Link href="/security/" className="hover:text-navy">Security</Link></li>
              <li><Link href="/accessibility/" className="hover:text-navy">Accessibility</Link></li>
              <li><Link href="/privacy/" className="hover:text-navy">Privacy</Link></li>
              <li><Link href="/terms/" className="hover:text-navy">Terms</Link></li>
              <li><Link href="/status/" className="hover:text-navy">Status</Link></li>
            </ul>
          </nav>
          <nav aria-label="More" className="text-sm">
            <h2 className="mb-3 font-semibold text-ink">More</h2>
            <ul className="space-y-2 text-ink2">
              <li><Link href="/contact/" className="hover:text-navy">Contact</Link></li>
              <li><a href="https://github.com/Chinonsocheq21/Zenai" className="hover:text-navy">Source on GitHub</a></li>
            </ul>
          </nav>
        </div>
      </div>
      <p className="border-t border-line px-5 py-5 text-center text-xs text-muted">
        ZenAI · Built at Morgan State University · {new Date().getFullYear()}
      </p>
    </footer>
  );
}
