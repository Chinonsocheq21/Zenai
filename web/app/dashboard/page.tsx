import { Suspense } from "react";
import { pageMeta } from "@/components/meta";
import Dashboard from "./Dashboard";
import "./print.css";

export const metadata = pageMeta(
  "/dashboard/",
  "Pilot dashboard",
  "Anonymous weekly counts for a campus in a ZenAI pilot: conversations, messages, crisis hand-offs, the safety check, and how students are using ZenAI.",
);

export default function DashboardPage() {
  return (
    <div className="mx-auto max-w-5xl px-5 pb-10 pt-12 print:max-w-none print:px-6 print:pt-6">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-orange print:hidden">For pilot partners</p>
      <h1 className="mt-3 font-serif text-4xl md:text-5xl print:mt-0 print:text-2xl">Campus dashboard</h1>
      <p className="mt-4 max-w-2xl text-lg text-ink2 print:hidden">
        How students on your campus are using ZenAI, week by week. These are counts, never conversations: ZenAI
        doesn&apos;t store what students write, or who they are.
      </p>
      <div className="mt-8 print:mt-4">
        <Suspense fallback={<p className="text-ink2">Loading...</p>}>
          <Dashboard />
        </Suspense>
      </div>
    </div>
  );
}
