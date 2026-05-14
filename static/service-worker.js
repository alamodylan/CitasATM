const CACHE_VERSION = "v1";
const CACHE_NAME = `atm-citas-static-${CACHE_VERSION}`;

const STATIC_ASSETS = [
    "/static/css/styles.css",
    "/static/js/app.js",
    "/static/img/LogoAlamo.png",
    "/static/img/BASC.png",
    "/static/img/icon-192.png",
    "/static/img/icon-512.png",
    "/static/img/maskable-icon-512.png",
    "/static/manifest.json"
];

self.addEventListener("install", function (event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function (cache) {
                return cache.addAll(STATIC_ASSETS);
            })
    );

    self.skipWaiting();
});

self.addEventListener("activate", function (event) {
    event.waitUntil(
        caches.keys()
            .then(function (cacheNames) {
                return Promise.all(
                    cacheNames
                        .filter(function (cacheName) {
                            return cacheName !== CACHE_NAME;
                        })
                        .map(function (cacheName) {
                            return caches.delete(cacheName);
                        })
                );
            })
    );

    self.clients.claim();
});

self.addEventListener("fetch", function (event) {
    const request = event.request;

    if (request.method !== "GET") {
        return;
    }

    const url = new URL(request.url);

    if (url.pathname.startsWith("/static/")) {
        event.respondWith(
            caches.match(request)
                .then(function (cachedResponse) {
                    return cachedResponse || fetch(request);
                })
        );

        return;
    }

    event.respondWith(
        fetch(request)
            .catch(function () {
                return new Response(
                    "Sin conexión. Esta pantalla requiere internet para cargar datos actualizados.",
                    {
                        status: 503,
                        statusText: "Offline",
                        headers: {
                            "Content-Type": "text/plain; charset=utf-8"
                        }
                    }
                );
            })
    );
});