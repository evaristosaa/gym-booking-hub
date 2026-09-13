const CACHE = "gym-booking-hub-v2";
const ASSETS = ["./", "./index.html", "./styles.css", "./app.js", "./firebase-config.js", "./manifest.webmanifest", "./icon.svg", "./assets/real-betis-crest.png"];

self.addEventListener("install", event => event.waitUntil(
  caches.open(CACHE).then(cache => cache.addAll(ASSETS)).then(() => self.skipWaiting()),
));
self.addEventListener("activate", event => event.waitUntil(
  caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim()),
));
self.addEventListener("fetch", event => {
  if (event.request.method !== "GET") return;
  const requestUrl = new URL(event.request.url);
  const refreshable = event.request.mode === "navigate" || (requestUrl.origin === self.location.origin && /\.(?:html|js|css)$/.test(requestUrl.pathname));
  if (!refreshable) {
    event.respondWith(caches.match(event.request).then(hit => hit || fetch(event.request)));
    return;
  }
  event.respondWith(fetch(event.request).then(response => {
    const copy = response.clone();
    caches.open(CACHE).then(cache => cache.put(event.request, copy));
    return response;
  }).catch(() => caches.match(event.request)));
});
