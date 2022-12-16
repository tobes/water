RESOURCES = [
  "/",
  "/static/styles.css",
  "/static/water.js",
  "/static/chart.js",
  "/static/chart-date.js",
  "/static/img/up.svg",
  "/static/img/favicon-16x16.png",
  "/static/img/favicon-32x32.png",
  "/static/img/android-chrome-192x192.png",
  "/static/site.webmanifest",
]

const addResourcesToCache = async (resources) => {
  const cache = await caches.open("v1");
  await cache.addAll(resources);
};


self.addEventListener("install", (event) => {
  console.log('install');
  event.waitUntil(
    addResourcesToCache(RESOURCES)
  );
});

const cache = async (request) => {
  let resp;
  let url = new URL(request.url);

  resp = await fetch(request)
  // handle network err/success
  .then((response) => {
  let resp = response.clone();
  if (response.ok) {
    console.log('LIVE', response);
    caches.open("v1").then((cache) => cache.put(response.url, response));
    return resp;
  }
  })
  .catch(() => undefined);

  if (resp !== undefined) {
    return resp;
  }

  const responseFromCache = await caches.match(request);

  if (responseFromCache) {
    console.log('FROM CACHE', request.url);
    return responseFromCache;
  }

  console.log('***fetch***', request.url);
  return fetch(request);
}


self.addEventListener("fetch", (event) => {
  event.respondWith(cache(event.request));
});


self.addEventListener('activate', function(event) {
  console.log('Claiming control');
  return self.clients.claim();
});
