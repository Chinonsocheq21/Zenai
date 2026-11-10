import type { Metadata } from "next";

// The production address, hard-coded so a build anywhere shares the right links.
export const SITE = "https://zenai-app.vercel.app";
export const OG_IMAGE = "/media/film-poster.jpg";

// Every page's own title, description, canonical address and sharing card.
// A page's openGraph replaces the layout's whole openGraph, so the image and
// site name are repeated here.
export function pageMeta(path: string, title: string, description: string, shareTitle?: string): Metadata {
  return {
    title,
    description,
    alternates: { canonical: path },
    openGraph: {
      title: shareTitle ?? `${title} · ZenAI`,
      description,
      url: path,
      siteName: "ZenAI",
      type: "website",
      images: [OG_IMAGE],
    },
  };
}
