import type { MetadataRoute } from "next";
import { SITE } from "@/components/meta";

export const dynamic = "force-static";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/", disallow: ["/api/", "/dashboard/"] },
    sitemap: `${SITE}/sitemap.xml`,
  };
}
