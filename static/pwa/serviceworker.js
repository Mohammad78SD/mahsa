console.log('Service Worker Loaded...');
var staticCacheName = "django-pwa-v" + new Date().getTime();
var filesToCache = [
    '/',
    '/offline',
    '/static/images/metafan-logo.webp',
];
if ("serviceWorker" in navigator) {
    navigator.serviceWorker
      .register("/serviceworker.js", { scope: "/" })
      .then((registration) => {
        registration.unregister().then((boolean) => {
        });
      })
      .catch((error) => {
        
      });
      // Befor install prompt start
      window.addEventListener('beforeinstallprompt', event => {
      event.preventDefault();
      var installDiv = document.getElementById('divInstallApp');
      installDiv.innerHTML = '<button id="installApp" class="btn btn-outline-secondary ms-1">Install App</button>';
      installDiv.addEventListener('click', () => {
        event.prompt();
        installDiv.innerHTML = ""
      });
    });
    // Befor install prompt end
  }

// Cache on install
self.addEventListener("install", event => {
    this.skipWaiting();
    event.waitUntil(
        caches.open(staticCacheName)
            .then(cache => {
                return Promise.all(
                    filesToCache.map(url => {
                        return cache.add(url).catch(error => {
                            console.error('Failed to cache:', url, error);
                        });
                    })
                );
            })
    )
});

// Rest of your service worker code...

// Clear cache on activate
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames
                    .filter(cacheName => (cacheName.startsWith("django-pwa-")))
                    .filter(cacheName => (cacheName !== staticCacheName))
                    .map(cacheName => caches.delete(cacheName))
            );
        })
    );
});

// Serve from Cache
self.addEventListener("fetch", event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                return response || fetch(event.request);
            })
            .catch(() => {
                return caches.match('offline');
            })
    )
});

// Push event listener
self.addEventListener('push', function(event) {
    if (event.data) {
        const data = event.data.json();
        const options = {
            body: data.description,
            icon: '/static/images/icon.png',
            badge: '/static/images/badge.png'
        };
        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );
    }
});

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', () => self.clients.claim());