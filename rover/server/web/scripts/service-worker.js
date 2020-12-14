// Push And Notifications - https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Re-engageable_Notifications_Push
const filesToCache = [
    '/css/stylesheet.css',
    '/images/rover.png',
    '/images/rover.svg',
    '/offline',
    '/404'
];

// Cache Names
const staticCacheName = 'pages-cache-v1';
const tweetCacheName = 'tweets-cache-v1';

// Sync Events
const tweetSyncName = 'tweets-sync';

// Sync URLs
const tweetAPIURL = '/api?text='

// Install Pages To Cache
self.addEventListener('install', event => {
    console.log('Attempting To Install Service Worker And Cache Static Assets!!!');
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
    console.log('Activating New Service Worker!!!');

    // Hmmmmmmm...
    setupBackgroundSync()

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

self.addEventListener('periodicSync', (event) => {
    if (event.tag === tweetSyncName) {
        // See the "Think before you sync" section for
        // checks you could perform before syncing.
        event.waitUntil(updateTweets());
    }
});

async function updateTweets() {
    console.log("Downloading New Tweets!!!")

    const tweetsCache = await caches.open(tweetCacheName);
    await tweetsCache.add(tweetAPIURL);
}

// setupBackgroundSync()
async function setupBackgroundSync() {
    if ('serviceWorker' in navigator) {
        console.log("Checking For Background Sync Capabilities and Registering")
        await checkAndRegisterBackgroundSync().then(await verifyBackgroundSyncRegistration)
    } else {
        console.warn("Service Worker Missing From Navigator!!!")
    }
}

async function checkAndRegisterBackgroundSync() {
    const status = await navigator.permissions.query({
        name: 'periodic-background-sync',
    });

    if (status.state === 'granted') {
        // Periodic background sync can be used.
        console.log("Background Sync Access Granted!!!")
        await registerBackgroundSync()
    } else {
        // Periodic background sync cannot be used.
        console.warn("Background Sync Access Denied!!!")
    }
}

async function registerBackgroundSync() {
    const registration = await navigator.serviceWorker.ready;

    if ('periodicSync' in registration) {
        try {
            console.debug("Trying To Register Sync Handler!!!")
            await registration.periodicSync.register(tweetSyncName, {
                // An interval of one day.
                minInterval: 24 * 60 * 60 * 1000,
            }).then(() => {
                console.debug("Registered Sync Handler!!!")
            });
        } catch (error) {
            // Periodic background sync cannot be used.
            console.error("Failed To Register Sync Handler!!! Error: ${error}")
        }
    }
}

async function verifyBackgroundSyncRegistration() {
    const registration = await navigator.serviceWorker.ready;

    if ('periodicSync' in registration) {
        const tags = await registration.periodicSync.getTags();

        // Only update content if sync isn't set up.
        if (tags.includes(tweetSyncName)) {
            console.debug("Background Sync Registration Failed!!!")
            // updateContentOnPageLoad();
        } else {
            console.debug("Background Sync Registration Verified!!!")
            await updateTweets()
        }
    } else {
        // If periodic background sync isn't supported, always update.
        // updateContentOnPageLoad();
        console.debug("Background Sync Not Supported!!!")
    }
}

async function unregisterBackgroundSync() {
    const registration = await navigator.serviceWorker.ready;

    if ('periodicSync' in registration) {
        await registration.periodicSync.unregister(tweetSyncName).then(() => {
            console.debug("Unregistered Background Sync!!!")
        })
    }
}