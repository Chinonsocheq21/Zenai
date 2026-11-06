// Page views only, with no cookies (Vercel Web Analytics), and only on the hosted
// site. Each address is cut down to its path first: no query, no fragment, so
// nothing like ?signin= ever leaves the device. Nothing a student types is sent.
(function () {
  if (/^(localhost|127\.0\.0\.1|\[::1\]|192\.168\.|10\.)/.test(location.hostname)) return;
  window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
  window.va("beforeSend", function (event) {
    try { const u = new URL(event.url); return Object.assign({}, event, {url: u.origin + u.pathname}); }
    catch (e) { return null; }
  });
  const s = document.createElement("script");
  s.defer = true; s.src = "/_vercel/insights/script.js";
  document.head.appendChild(s);
})();
