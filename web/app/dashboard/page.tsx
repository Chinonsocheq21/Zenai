import type { Metadata } from "next";
import Trends from "./Trends";

export const metadata: Metadata = {
  title: "Pilot dashboard",
  description: "Anonymous weekly trends for a campus in a ZenAI pilot.",
  robots: { index: false, follow: false },
};

export default function Dashboard() {
  return (
    <div className="mx-auto max-w-4xl px-5 pb-10 pt-12">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-orange">For pilot partners</p>
      <h1 className="mt-3 font-serif text-4xl md:text-5xl">Campus trends</h1>
      <p className="mt-4 max-w-2xl text-lg text-ink2">
        How students on your campus are using ZenAI, week by week. These are counts, never conversations: ZenAI doesn't
        store what students write, or who they are.
      </p>
      <div className="mt-8"><Trends /></div>
    </div>
  );
}
