import Link from "next/link";

// A closing "what next" button for a content page, so no page ends in a dead end.
// `href` starting with "/app/" renders a plain anchor (it leaves the static export),
// everything else a Next Link.
export default function NextStep({ href, label, note }: { href: string; label: string; note?: string }) {
  const isApp = href === "/app/";
  return (
    <section className="mt-14">
      <div className="flex flex-col items-center gap-3 rounded-3xl border border-line bg-card p-8 text-center">
        {isApp ? (
          <a href={href} className="rounded-full bg-navy px-6 py-3.5 font-semibold text-white hover:bg-navy2">{label}</a>
        ) : (
          <Link href={href} className="rounded-full bg-navy px-6 py-3.5 font-semibold text-white hover:bg-navy2">{label}</Link>
        )}
        {note && <p className="text-sm text-ink2">{note}</p>}
      </div>
    </section>
  );
}
