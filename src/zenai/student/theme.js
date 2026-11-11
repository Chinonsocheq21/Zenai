// Theme: light, dark or system (match the phone). The <html> element already has
// the right data-theme before paint, from the inline script in <head>; this file
// is the API everything else uses to read and change it, and it keeps the
// theme-color meta and the system listener in step. localStorage key 'zenai-theme'.
(function () {
  const KEY = "zenai-theme";
  const LIGHT = "#F5F1EA", DARK = "#0A1426";
  const mq = window.matchMedia ? matchMedia("(prefers-color-scheme: dark)") : null;

  function get() {
    try {
      const t = localStorage.getItem(KEY);
      return t === "dark" || t === "system" ? t : "light";
    } catch (e) { return "light"; }
  }

  function apply(t) {
    document.documentElement.setAttribute("data-theme", t);
    const dark = t === "dark" || (t === "system" && mq && mq.matches);
    const tc = document.getElementById("themeColor"), cs = document.getElementById("colorScheme");
    if (tc) tc.setAttribute("content", dark ? DARK : LIGHT);
    if (cs) cs.setAttribute("content", t === "system" ? "light dark" : t);
  }

  function set(t) {
    if (t !== "light" && t !== "dark" && t !== "system") t = "light";
    try { localStorage.setItem(KEY, t); } catch (e) {}
    apply(t);
    document.dispatchEvent(new CustomEvent("zenai:theme", {detail: t}));
  }

  if (mq) mq.addEventListener ? mq.addEventListener("change", () => { if (get() === "system") apply("system"); })
    : mq.addListener(() => { if (get() === "system") apply("system"); });

  apply(get());
  window.zenaiTheme = {get, set, apply};
})();
