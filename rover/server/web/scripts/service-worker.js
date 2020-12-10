// Push And Notifications - https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Re-engageable_Notifications_Push
const filesToCache = [
    '/css/stylesheet.css',
    '/images/rover.png',
    '/images/rover.svg',
    '/offline',
    '/404'
];

const staticCacheName = 'pages-cache-v1';

// Install Pages To Cache
self.addEventListener('install', event => {
    console.log('Attempting to install service worker and cache static assets');
    event.waitUntil(
        caches.open(staticCacheName)
        .then(cache => {
            return cache.addAll(filesToCache);
        })
    );
});

// Fetch Cached Pages When Offline
self.addEventListener('fetch', event => {
    console.log('Fetch event for ', event.request.url);
    event.respondWith(
        caches.match(event.request)
        .then(response => {
            if (response) {
                console.log('Found ', event.request.url, ' in cache');
                return response;
            }

            console.log('Network request for ', event.request.url);
            return fetch(event.request).then(response => {
                return caches.open(staticCacheName).then(cache => {
                    // Return Cached Page
                    return response;
                }).catch(error => {
                    // Return 404 Page (And Associate URL With 404 Page)
                    if (response.status === 404) {
                        cache.put('/404', response.clone());
                        return response;
                    }
                });
            });
        }).catch(error => {
            // Return Cached Offline Page
            const offline_page = caches.match("/offline").then(cache => {
                const init = {"status": 503, "statusText": "Offline"};  // 503 Means Service Unavailable
                // const blob = new Blob([offline_page], {type : 'text/html'});
                return new Response(cache.body, init);
            });

            return offline_page;
        })
    );
});

// Activate New Service Worker To Replace Caches (Replace staticCacheName to upgrade service worker cache)
self.addEventListener('activate', event => {
    console.log('Activating new service worker...');

    const cacheAllowlist = [staticCacheName];

    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheAllowlist.indexOf(cacheName) === -1) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});