const CACHE_NAME = "microgrid-pwa-v1";

const URLS_TO_CACHE = [
  "/",
  "/forecast",
  "/reports",
  "/agent",
  "/about",
  "/static/style.css",
  "/static/script.js",
  "/static/manifest.json"
];

// Install
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(URLS_TO_CACHE);
    })
  );
});

// Fetch
self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});
