import type { MetadataRoute } from "next";
import { SITE } from "@/components/meta";

export const dynamic = "force-static";

// Public pages only. The pilot dashboard and sign-in are left out on purpose.
const PAGES = [
  "/", "/how-it-works/", "/safety/", "/universities/", "/help/", "/privacy/", "/terms/",
  "/security/", "/accessibility/", "/contact/", "/status/", "/app/",
];

export default function sitemap(): MetadataRoute.Sitemap {
  return PAGES.map((p) => ({ url: `${SITE}${p}`, changeFrequency: "monthly", priority: p === "/" ? 1 : 0.6 }));
}
