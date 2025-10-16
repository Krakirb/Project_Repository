const assets = [
  "/",
  "/static/css/style.css",
  "/static/js/app.js",
  "/static/images/logo_text.png",
  "/static/images/favicon.png",
  "/static/icons/icon-128x128.png",
  "/static/icons/icon-192x192.png",
  "/static/icons/icon-384x384.png",
  "/static/icons/icon-512x512.png",
  "/static/icons/desktop_screenshot.png",
  "/static/images/listings/Colosseum_Image.jpg",
  "/static/images/listings/Eiffel_Tower.jpg",
  "/static/images/listings/Opera_House_Image.jpg",
  "/index.html",
  "/attractions.html",
  "/restaurants.html",
  "/accommodation.html",
  "/log_in.html",
  "/register.html",
  "/review.html",
  "/listing/1",
  "/listing/2",
];

const CATALOGUE_ASSETS = "catalogue-assets-v2";

/* self.addEventListener("install", (installEvt) => {
  installEvt.waitUntil(
    caches
      .open(CATALOGUE_ASSETS)
      .then((cache) => {
        console.log(cache);
        cache.addAll(assets);
        console.log ("All assets are cached");
      })
      .then(() => self.skipWaiting())
      .catch((e) => {
        console.log(e);
      })
  );
});
*/

self.addEventListener("fetch", (evt) => {
  evt.respondWith(
    fetch(evt.request)
      .then((response) => {
        if (evt.request.method === "GET" && response.status === 200) {
          const clone = response.clone();
          caches.open(CATALOGUE_ASSETS).then((cache) => cache.put(evt.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(evt.request))
  );
});


self.addEventListener("activate", function (evt) {
  evt.waitUntil(
    caches
      .keys()
      .then((keyList) => {
        return Promise.all(
          keyList.map((key) => {
            if (key !== CATALOGUE_ASSETS) {
              console.log("Removed old cache", key);
              return caches.delete(key);}
          })
        );
      })
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", function (evt) {
  evt.respondWith(
    fetch(evt.request).catch(() => {
      return caches.open(CATALOGUE_ASSETS).then((cache) => {
        return cache.match(evt.request);
      });
    })
  );
});
