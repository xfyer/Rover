// Import Main Script To Avoid Duplicating Functions and Variables
importScripts("/scripts/main.js")

// Push And Notifications - https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Re-engageable_Notifications_Push
const filesToCache = [
    '/manifest.webmanifest',
    '/scripts/main.js',
    '/scripts/helper.js',
    '/css/stylesheet.css',
    '/images/rover.png',
    '/images/rover.svg',
    '/offline',
    '/404',
    '/',
    '/?pwa=true',
    'https://code.jquery.com/jquery-3.5.1.min.js'
];

// Cache Names
const staticCacheName = 'pages-cache-v1';

// Install Pages To Cache
self.addEventListener('install', event => {
    console.debug('Attempting To Install Service Worker And Cache Static Assets!!!');
    event.waitUntil(
        caches.open(staticCacheName)
        .then(cache => {
            return cache.addAll(filesToCache);
        })
    );
});

// Fetch Cached Pages When Offline
self.addEventListener('fetch', event => {
    console.debug('Fetch Event For ', event.request.url);
    event.respondWith(
        caches.match(event.request)
        .then(response => {
            if (response) {
                console.debug('Found, ', event.request.url, ', In Cache');
                return response;
            }

            console.debug('Network Request For ', event.request.url);
            return fetch(event.request).then(response => {
                return caches.open(staticCacheName).then(() => {
                    // Return Cached Page
                    return response;
                }).catch(() => {
                    // Return 404 Page (And Associate URL With 404 Page)
                    if (response.status === 404) {
                        caches.put('/404', response.clone());
                        return response;
                    }
                });
            });
        }).catch(() => {
            // Return Cached Offline Page
            return caches.match("/offline").then(cache => {
                const init = {"status": 503, "statusText": "Offline"};  // 503 Means Service Unavailable
                // const blob = new Blob([offline_page], {type : 'text/html'});
                return new Response(cache.body, init);
            });
        })
    );
});

// Activate New Service Worker To Replace Caches (Replace staticCacheName to upgrade service worker cache)
self.addEventListener('activate', event => {
    console.debug('Activating New Service Worker!!!');

    const cacheAllowList = [staticCacheName];

    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheAllowList.indexOf(cacheName) === -1) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Must Be All Lowercase For Reasons...
self.addEventListener('periodicsync', (event) => {
    if (event.tag === tweetSyncName) {
        // TODO: Check If Needing To Sync

        console.debug("Periodic Sync Triggered For: ", tweetSyncName)
        event.waitUntil(downloadNewTweets());
    }
});