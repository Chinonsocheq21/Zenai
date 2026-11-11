import type { Metadata, Viewport } from "next";
import SiteFooter from "@/components/SiteFooter";
import SiteHeader from "@/components/SiteHeader";
import SiteAnalytics from "./analytics";
import { OG_IMAGE, SITE } from "@/components/meta";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(SITE),
  title: { default: "ZenAI · A place to slow down for a minute", template: "%s · ZenAI" },
  description:
    "A support chat for Morgan State students, grounded in Acceptance and Commitment Therapy. Every reply is checked before a student sees it, and a crisis is handed to a person.",
  icons: { icon: "/icon.png", apple: "/icons/apple-touch-icon.png" },
  manifest: "/manifest.webmanifest",
  appleWebApp: { capable: true, title: "ZenAI", statusBarStyle: "default" },
  // "./" resolves to each page's own path, so pages that set nothing still get their own canonical.
  alternates: { canonical: "./" },
  openGraph: {
    title: "ZenAI · A place to slow down for a minute",
    description: "A support chat for Morgan State students. Every reply is checked before a student sees it, and a crisis is handed to a person.",
    url: "./",
    siteName: "ZenAI",
    type: "website",
    images: [OG_IMAGE],
  },
};

export const viewport: Viewport = { themeColor: "#f7f3ec", width: "device-width", initialScale: 1 };

// Reads the choice saved under the key the app shares (see ThemeSwitch), and sets it
// on <html> before the first paint so there is no flash from the Light default to a
// saved Dark or Match-my-phone choice. Light needs no script: it is the static default.
const THEME_SCRIPT = `(function(){try{var t=localStorage.getItem('zenai-theme');if(t==='dark'||t==='system')document.documentElement.setAttribute('data-theme',t);}catch(e){}})();`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="light">
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
      </head>
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
