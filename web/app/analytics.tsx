"use client";

import { Analytics, type BeforeSendEvent } from "@vercel/analytics/next";

// Page views only, with no cookies (Vercel Web Analytics). Every address is cut
// down to its path before it leaves the browser: no query string, no fragment.
export function stripToPath(event: BeforeSendEvent): BeforeSendEvent {
  const url = new URL(event.url);
  return { ...event, url: url.origin + url.pathname };
}

export default function SiteAnalytics() {
  return <Analytics beforeSend={stripToPath} />;
}
