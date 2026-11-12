// The staff console has its own full-height app frame (see Console.tsx), with no
// marketing header or footer. Dark-first: with no saved theme it starts dark. This
// inline script does that before paint on a direct load; Console.tsx does the same
// after a client-side navigation, and puts light back when you leave.
const CONSOLE_THEME = `(function(){try{if(!localStorage.getItem('zenai-theme'))document.documentElement.setAttribute('data-theme','dark');}catch(e){}})();`;

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <script dangerouslySetInnerHTML={{ __html: CONSOLE_THEME }} />
      {children}
    </>
  );
}
