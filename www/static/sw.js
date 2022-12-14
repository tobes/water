
const addResourcesToCache = async (resources) => {
  const cache = await caches.open("v1");
  await cache.addAll(resources);
};

const cacheFirst = async (request) => {
  const responseFromCache = await caches.match(request);
  if (responseFromCache) {
    return responseFromCache;
  }
  return fetch(request);
};

self.addEventListener("install", (event) => {
  event.waitUntil(
    addResourcesToCache([
      "/",
      "/static/styles.css",
      "/static/water.js",
      "/static/chart.js",
      "/static/chart-date.js",
      "/static/img/01d.png",
      "/static/img/01n.png",
      "/static/img/02d.png",
      "/static/img/02n.png",
      "/static/img/03d.png",
      "/static/img/03n.png",
      "/static/img/04d.png",
      "/static/img/04n.png",
      "/static/img/09d.png",
      "/static/img/09n.png",
      "/static/img/10d.png",
      "/static/img/10n.png",
      "/static/img/11d.png",
      "/static/img/11n.png",
      "/static/img/13d.png",
      "/static/img/13n.png",
      "/static/img/50d.png",
      "/static/img/50n.png",
      "/static/img/unknown.png",
      "/static/img/up.svg",
      "/static/img/favicon-16x16.png",
      "/static/img/favicon-32x32.png",
      "/static/img/android-chrome-192x192.png",
      "/static/site.webmanifest",
      "/status?fast",
      "/stats",
    ])
  );
});

self.addEventListener("fetch", (event) => {
  event.respondWith(cacheFirst(event.request));
});

self.addEventListener('activate', function(event) {
  return self.clients.claim();
});
