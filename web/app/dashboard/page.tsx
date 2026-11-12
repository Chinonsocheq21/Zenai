import { Suspense } from "react";
import { pageMeta } from "@/components/meta";
import Dashboard from "./Dashboard";
import "./print.css";

export const metadata = pageMeta(
  "/dashboard/",
  "Campus console",
  "Anonymous weekly counts for a campus in a ZenAI pilot: conversations, messages, crisis hand-offs, the safety check, and how students are using ZenAI.",
);

export default function DashboardPage() {
  return (
    <Suspense fallback={<p className="p-8 text-ink2">Loading...</p>}>
      <Dashboard />
    </Suspense>
  );
}
