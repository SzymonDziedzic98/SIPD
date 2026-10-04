// Pamięć podręczna strony i Pyodide (ten sam plik w psm-web i SIPD, web/sw.js).
// Pliki strony: najpierw sieć, bez sieci kopia z pamięci (zmiany na serwerze widać od razu).
// Pyodide, Chart.js i fonty mają wersję w adresie, więc idą z pamięci od drugiej wizyty i działają bez internetu.
"use strict";
const CACHE = "model-web-v1:" + self.registration.scope;
const FIXED = /^https:\/\/(cdn\.jsdelivr\.net\/(pyodide|npm)\/|cdnjs\.cloudflare\.com\/ajax\/libs\/|fonts\.gstatic\.com\/|fonts\.googleapis\.com\/)/;
// pliki, których strona może potrzebować dopiero później (obliczenia w tle, poprawki sieci), od razu do pamięci
const LATER = ["bg.js", "psm.py", "modele.html"];
self.addEventListener("install", (ev) => {
  self.skipWaiting();
  ev.waitUntil(caches.open(CACHE).then((c) => Promise.all(LATER.map((f) => c.add(new URL(f, self.registration.scope)).catch(() => {})))));
});
self.addEventListener("activate", (ev) => ev.waitUntil((async () => {
  for (const k of await caches.keys()) if (k.endsWith(":" + self.registration.scope) && k !== CACHE) await caches.delete(k);
  await self.clients.claim();
})()));
async function put(req, res) {
  if (res && ((res.ok && res.status !== 206) || res.type === "opaque")) {
    const c = await caches.open(CACHE);
    await c.put(req, res.clone());
  }
  return res;
}
self.addEventListener("fetch", (ev) => {
  const req = ev.request;
  if (req.method !== "GET") return;
  const url = req.url;
  if (FIXED.test(url)) {
    ev.respondWith((async () => (await caches.match(req)) || put(req, await fetch(req)))());
  } else if (url.startsWith(self.registration.scope)) {
    ev.respondWith((async () => {
      try { return await put(req, await fetch(req)); }
      catch (e) {
        const hit = await caches.match(req, { ignoreSearch: req.mode === "navigate" });
        if (hit) return hit;
        throw e;
      }
    })());
  }
});
