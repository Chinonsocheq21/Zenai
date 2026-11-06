import type { Metadata, Viewport } from "next";
import SiteFooter from "@/components/SiteFooter";
import SiteHeader from "@/components/SiteHeader";
import SiteAnalytics from "./analytics";
import "./globals.css";

const SITE = process.env.VERCEL_PROJECT_PRODUCTION_URL
  ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`
  : "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(SITE),
  title: { default: "ZenAI · A place to slow down for a minute", template: "%s · ZenAI" },
  description:
    "A support chat for Morgan State students, grounded in Acceptance and Commitment Therapy. Every reply is checked before a student sees it, and a crisis is handed to a person.",
  icons: { icon: "/icon.png", apple: "/icon.png" },
  openGraph: { title: "ZenAI", description: "A place to slow down for a minute.", images: ["/media/film-poster.jpg"] },
};

export const viewport: Viewport = { themeColor: "#f7f3ec", width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans">
        <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-full focus:bg-navy focus:px-4 focus:py-2 focus:text-white">
          Skip to content
        </a>
        <SiteHeader />
        <main id="main">{children}</main>
        <SiteFooter />
        <SiteAnalytics />
      </body>
    </html>
  );
}
