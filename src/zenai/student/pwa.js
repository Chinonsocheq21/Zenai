/* Registers the service worker that keeps the app shell and offline help
   available without a connection. Only on https or localhost, and never throws. */
(function () {
  try {
    if (!("serviceWorker" in navigator)) return;
    var h = location.hostname;
    var local = h === "localhost" || h === "127.0.0.1" || h === "[::1]";
    if (location.protocol !== "https:" && !local) return;
    var go = function () {
      try {
        navigator.serviceWorker.register("sw.js", { scope: "./" }).catch(function () {});
      } catch (e) {}
    };
    if (document.readyState === "complete") go();
    else window.addEventListener("load", go);
  } catch (e) {}
})();
