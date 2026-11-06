// Serves the site the way the Vercel build lays it out: the Next export at /,
// the student app at /app/. Static files only (the API is not needed here).
import { createServer } from "node:http";
import { existsSync, readFileSync, statSync } from "node:fs";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";

const here = fileURLToPath(new URL(".", import.meta.url));
const SITE = join(here, "..", "out");
const APP = join(here, "..", "..", "src", "zenai", "student");
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".png": "image/png",
  ".jpg": "image/jpeg", ".svg": "image/svg+xml", ".mp4": "video/mp4", ".json": "application/json",
  ".webmanifest": "application/manifest+json", ".txt": "text/plain", ".ico": "image/x-icon" };

function resolve(urlPath) {
  const p = decodeURIComponent(urlPath.split("?")[0]);
  const [root, rest] = p.startsWith("/app/") || p === "/app" ? [APP, p.slice(4)] : [SITE, p];
  const f = normalize(join(root, rest));
  if (!f.startsWith(root)) return null;
  if (existsSync(f) && statSync(f).isFile()) return f;
  if (existsSync(join(f, "index.html"))) return join(f, "index.html");   // /help and /help/ both, as Vercel does
  return null;
}

const port = Number(process.env.PORT || 4321);
createServer((req, res) => {
  const f = resolve(req.url || "/");
  if (!f) {
    res.writeHead(404, { "content-type": "text/html" });
    return res.end(existsSync(join(SITE, "404.html")) ? readFileSync(join(SITE, "404.html")) : "not found");
  }
  res.writeHead(200, { "content-type": TYPES[extname(f)] || "application/octet-stream" });
  res.end(readFileSync(f));
}).listen(port, "127.0.0.1", () => console.log(`site on http://127.0.0.1:${port}`));
