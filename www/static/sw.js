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
    ])
  );
});

self.addEventListener("fetch", (event) => {
  console.log('fetch', event.request);
  event.respondWith(cacheFirst(event.request));
});
