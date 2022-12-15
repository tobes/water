RESOURCES = [
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
  "/stats"
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
  let live = ['/status', '/stats'].indexOf(url.pathname) !== -1;

  if (live) {
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
  }

  if (resp !== undefined) {
    return resp;
  }

  const responseFromCache = await caches.match(request);

  if (responseFromCache) {
    console.log('FROM CACHE', request.url);
    return responseFromCache;
  }

  console.log('***fetch***');
  return fetch(request);
}


self.addEventListener("fetch", (event) => {
  event.respondWith(cache(event.request));
});
