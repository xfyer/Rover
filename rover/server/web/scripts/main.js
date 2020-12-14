// Cache Names
const staticCacheName = 'pages-cache-v1';
const tweetCacheName = 'tweets-cache-v1';

// Sync Events
const tweetSyncName = 'tweets-sync';

// Sync URLs
const tweetAPIURL = '/api/latest'

// Load Functions
registerServiceWorker();
installEruda();

function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js')
        .then(function(registration) {
          console.debug('Registration Successful, Scope Is:', registration.scope);
          setupBackgroundSync()
        })
        .catch(function(error) {
          console.error('Service Worker Registration Failed, Error:', error);
        });
  }
}

function setupBackgroundSync() {
    if ('serviceWorker' in navigator) {
        console.debug("Checking For Background Sync Capabilities and Registering")
        checkAndRegisterBackgroundSync().then(verifyBackgroundSyncRegistration)
    } else {
        console.error("Service Worker Missing From Navigator!!!")
    }
}

// Only Execute When DOM Is Loaded
function updateTweets() {
    downloadNewTweets().then(() => {
        // TODO: Populate Page Here
        console.log("Downloaded Latest Tweets!!!")

        // Populate DOM With Tweets
        populateTweets()
    })
}

// This Is A Separate Function So I Can Load Tweets To DOM From Cache Without Waiting To Download New Tweets
function populateTweets() {
    caches.open(tweetCacheName).then(tweetsCache => {
        tweetsCache.match(tweetAPIURL).then(tweets => {
            if (tweets === undefined) {
                console.error("Failed To Find Key, '", tweetAPIURL, "', From '", tweetCacheName, "'!!!")
                return
            }

            let reader = tweets.body.getReader()

            reader.read().then(result => {
                generateTableFromTweets(uintToString(result.value))
            })
        })
    })
}

// Download Tweets (No Matter If Background Or DOM Loaded)
async function downloadNewTweets() {
    console.log("Downloading New Tweets!!!")

    const tweetsCache = await caches.open(tweetCacheName);

    // Delete The Cache, Then Re-add
    // await tweetsCache.delete(tweetAPIURL).then()
    await tweetsCache.add(tweetAPIURL);
}

async function checkAndRegisterBackgroundSync() {
    const status = await navigator.permissions.query({
        name: 'periodic-background-sync',
    });

    if (status.state === 'granted') {
        // Periodic background sync can be used.
        console.debug("Background Sync Access Granted!!!")
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
            console.debug("Trying To Register Sync Handler: ", tweetSyncName)
            await registration.periodicSync.register(tweetSyncName, {
                // Once A Day Is: 24 * 60 * 60 * 1000
                // Every Minute Is: 60 * 1000
                minInterval: 60 * 1000,
            }).then(() => {
                console.debug("Registered Sync Handler: ", tweetSyncName)
            });
        } catch (error) {
            // Periodic background sync cannot be used.
            console.error("Failed To Register Sync Handler!!! Error: ", error)
        }
    }
}

async function verifyBackgroundSyncRegistration() {
    const registration = await navigator.serviceWorker.ready;

    if ('periodicSync' in registration) {
        const tags = await registration.periodicSync.getTags();

        // Only update content if sync isn't set up.
        console.debug("Tweet Sync Name: ", tweetSyncName)
        if (tags.includes(tweetSyncName)) {
            console.debug("Background Sync Registration Verified!!!")
        } else {
            console.warn("Background Sync Registration Failed!!!")
            updateTweets()
        }
    } else {
        // If periodic background sync isn't supported, always update.
        console.warn("Background Sync Not Supported!!!")
        updateTweets()
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

// Mobile DevTools Console - Activate With /?eruda=true
function installEruda() {
    // If True, Running From Service Worker (Or Web Worker)
    if (self.document === undefined) {
        return;
    }

    let src = 'https://cdn.jsdelivr.net/npm/eruda';
    if (!/eruda=true/.test(window.location) && localStorage.getItem('active-eruda') !== 'true') {
        return;
    }

    import(src).then(() => {
        caches.open(staticCacheName)
            .then(cache => {
                cache.add(src).then(() => {
                    eruda.init();
                    console.debug("Eruda Saved To Cache!!!")
                })
            })
    });
}