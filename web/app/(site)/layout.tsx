import SiteFooter from "@/components/SiteFooter";
import SiteHeader from "@/components/SiteHeader";

// The public site's frame. The route group adds nothing to the URL.
export default function SiteLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <SiteHeader />
      <main id="main">{children}</main>
      <SiteFooter />
    </>
  );
}
