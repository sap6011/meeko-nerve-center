// SolarPunk Service Worker — makes the app installable + works offline
const CACHE = 'solarpunk-v1';
const OFFLINE_URLS = [
  '/meeko-nerve-center/mobile.html',
  '/meeko-nerve-center/manifest.json',
  '/meeko-nerve-center/logo.svg',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(OFFLINE_URLS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  // Network first for feed.json (live data), cache fallback for everything else
  if (e.request.url.includes('feed.json') || e.request.url.includes('pool_state')) {
    e.respondWith(
      fetch(e.request).catch(() => caches.match(e.request))
    );
    return;
  }
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request).then(resp => {
      if (resp.ok) {
        const clone = resp.clone();
        caches.open(CACHE).then(c => c.put(e.request, clone));
      }
      return resp;
    }))
  );
});

// Push notification handler (for future Telegram WebPush integration)
self.addEventListener('push', e => {
  const data = e.data ? e.data.json() : { title: 'SolarPunk', body: 'Update available' };
  e.waitUntil(
    self.registration.showNotification(data.title || 'SolarPunk', {
      body: data.body || '',
      icon: '/meeko-nerve-center/logo.svg',
      badge: '/meeko-nerve-center/logo.svg',
      tag: 'solarpunk',
      renotify: true,
    })
  );
});
