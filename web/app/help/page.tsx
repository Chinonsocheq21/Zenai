import type { Metadata } from "next";
import NextStep from "@/components/NextStep";

export const metadata: Metadata = {
  title: "Get help now",
  description: "988 and Morgan State's verified support offices. No sign-in needed.",
};

// The same verified list the app shows (src/zenai/agents/resources.py), read off
// morgan.edu. Never generated. Re-check each semester.
const VERIFIED = "October 29, 2026";
const OFFICES = [
  { name: "Counseling Center", what: "Counseling for Morgan students, in person or by phone.", phone: "443-885-3130",
    detail: "Weekdays 8:30 to 5 · 24/7 line: 1-800-422-0009", url: "https://www.morgan.edu/counselingcenter" },
  { name: "Student Support and Outreach Services (S.O.S.)", what: "One person who helps you sort out what's getting in the way: money, housing, school or health.",
    phone: "443-885-4670", detail: "McMechen Hall 634 · sos@morgan.edu", url: "https://www.morgan.edu/student-support-and-outreach" },
  { name: "Center for Academic Success and Achievement (CASA)", what: "Tutoring and academic advising. Book through Navigate 360.",
    phone: "443-885-3380", detail: "Tyler Hall, Suite 117 · CASA@morgan.edu", url: "https://www.morgan.edu/tutoring" },
  { name: "Student Disability Support Services", what: "Academic accommodations and disability support.",
    phone: "443-885-4767", detail: "Richardson Library, Room 133-A · SDSS@morgan.edu", url: "https://www.morgan.edu/sdss" },
  { name: "Food Resource Center", what: "Free groceries and toiletries with your BEARcard, and help applying for SNAP.",
    phone: "443-885-2736", detail: "McKeldin Center 208 · foodresourcecenter@morgan.edu", url: "https://www.morgan.edu/foodresourcecenter" },
];

const tel = (p: string) => `tel:${p.replace(/[^0-9]/g, "")}`;

export default function Help() {
  return (
    <div className="mx-auto max-w-3xl px-5 pb-10 pt-12">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-crisis">Get help now</p>
      <h1 className="mt-3 font-serif text-4xl leading-tight md:text-5xl">You don't have to carry this alone.</h1>
      <p className="mt-4 text-lg text-ink2">If you might hurt yourself or someone else, or you're not sure you're safe, reach a person now. It's free and confidential.</p>

      <section aria-labelledby="now" className="mt-8 rounded-[32px] border border-crisis/25 bg-crisisbg p-6 md:p-8">
        <h2 id="now" className="text-xs font-bold uppercase tracking-[0.14em] text-crisis">Right now, 24 hours</h2>
        <p className="mt-2 text-2xl font-semibold">988 Suicide and Crisis Lifeline</p>
        <p className="mt-1 text-ink2">Call or text 988. Free and confidential, any time.</p>
        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          <a href="tel:988" className="rounded-full bg-crisis px-6 py-4 text-center text-lg font-semibold text-white hover:brightness-110">Call 988</a>
          <a href="sms:988" className="rounded-full border border-crisis/30 bg-white px-6 py-4 text-center text-lg font-semibold text-crisis hover:bg-crisis hover:text-white">Text 988</a>
        </div>
        <p className="mt-5 text-sm text-ink2">In immediate danger? Call <a href="tel:911" className="font-semibold text-crisis underline">911</a>.</p>
      </section>

      <section aria-labelledby="morgan" className="mt-12">
        <h2 id="morgan" className="font-serif text-3xl">At Morgan State</h2>
        <p className="mt-2 text-sm text-muted">Verified on morgan.edu on {VERIFIED}. ZenAI never writes these numbers itself.</p>
        <ul className="mt-6 space-y-3">
          {OFFICES.map((o) => (
            <li key={o.name} className="rounded-3xl border border-line bg-card p-5">
              <h3 className="font-semibold">{o.name}</h3>
              <p className="mt-1 text-[15px] text-ink2">{o.what}</p>
              <div className="mt-3 flex flex-wrap items-center gap-3">
                <a href={tel(o.phone)} className="rounded-full bg-navy/10 px-4 py-2 font-semibold text-navy hover:bg-navy hover:text-white">Call {o.phone}</a>
                <a href={o.url} className="text-sm font-medium text-navy underline-offset-2 hover:underline">Website</a>
              </div>
              <p className="mt-3 text-xs text-muted">{o.detail}</p>
            </li>
          ))}
        </ul>
      </section>

      <p className="mt-12 rounded-3xl bg-paper2 p-6 text-[15px] leading-relaxed text-ink2">
        ZenAI is not a counselor and can't respond to an emergency. If something serious comes up while you're talking,
        ZenAI stops and shows you these same numbers. Nothing on this page needs an account.
      </p>
      <NextStep href="/app/" label="Open ZenAI" note="Sign in with your Morgan email or an invite code." />
    </div>
  );
}
