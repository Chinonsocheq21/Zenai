/* ZenAI app service worker.
   Precaches the app shell and an offline help page. Cache-first for the shell,
   network-first for page loads with the offline page as the fallback.
   Never caches or intercepts API requests: anything not listed below goes
   straight to the network untouched. Bump VERSION to replace the cache. */
var VERSION = "zenai-shell-v10";
var SHELL = [
  "./",
  "index.html",
  "theme.js",
  "crisis-rules.js",
  "account.js",
  "sync.js",
  "analytics.js",
  "install.js",
  "pwa.js",
  "manifest.webmanifest",
  "apple-touch-icon.png",
  "icon-192.png",
  "icon-512.png",
  "offline.html",
  // Only the shortest guided session is precached (65s, the "Listen along"
  // companion on Talk home); the other two guided sessions are bigger and
  // cache themselves the first time they are played (see the fetch handler).
  "audio/breathe-1min.mp3"
];
var BASE = new URL("./", self.location).href;
var SHELL_URLS = SHELL.map(function (p) { return new URL(p, BASE).href; });

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(VERSION).then(function (cache) {
      // One at a time so a single missing file does not lose the rest,
      // but offline.html must make it in.
      return Promise.all(SHELL_URLS.map(function (u) {
        return cache.add(new Request(u, { cache: "reload" })).catch(function () {});
      })).then(function () {
        return cache.match(new URL("offline.html", BASE).href).then(function (hit) {
          if (!hit) return cache.add(new URL("offline.html", BASE).href);
        });
      });
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        if (k.indexOf("zenai-shell-") === 0 && k !== VERSION) return caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

function isApi(url) {
  return url.pathname.indexOf("/api/") === 0 || url.pathname === "/api";
}

function isAudio(url) {
  return /\/audio\/[^/]+\.mp3$/.test(url.pathname);
}

self.addEventListener("fetch", function (event) {
  var req = event.request;
  if (req.method !== "GET") return;
  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (isApi(url)) return;

  // The two longer guided sessions aren't precached (sw.js's own SHELL only
  // lists breathe-1min); the first play caches them here instead, so a
  // second listen works offline too without growing the install footprint.
  if (isAudio(url)) {
    event.respondWith(
      caches.match(req).then(function (hit) {
        if (hit) return hit;
        return fetch(req).then(function (res) {
          if (res && res.ok) {
            var copy = res.clone();
            caches.open(VERSION).then(function (cache) { cache.put(req, copy); });
          }
          return res;
        });
      })
    );
    return;
  }

  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req).catch(function () {
        return caches.open(VERSION).then(function (cache) {
          var clean = url.origin + url.pathname;
          var isShell = clean === BASE || clean === new URL("index.html", BASE).href;
          var shell = isShell ? cache.match(new URL("index.html", BASE).href) : Promise.resolve(null);
          return shell.then(function (hit) {
            return hit || cache.match(new URL("offline.html", BASE).href);
          });
        });
      })
    );
    return;
  }

  var key = url.origin + url.pathname;
  if (SHELL_URLS.indexOf(key) === -1) return;
  event.respondWith(
    caches.match(key).then(function (hit) {
      return hit || fetch(req);
    })
  );
});
