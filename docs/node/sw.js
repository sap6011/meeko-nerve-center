// SolarPunk Service Worker — makes the node work offline
const CACHE_NAME = 'solarpunk-node-v1';
const ASSETS = [
  '/meeko-nerve-center/node/',
  '/meeko-nerve-center/node/index.html',
  '/meeko-nerve-center/node/manifest.json',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  // Network first, cache fallback
  e.respondWith(
    fetch(e.request)
      .then(r => {
        const clone = r.clone();
        caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
        return r;
      })
      .catch(() => caches.match(e.request))
  );
});

// Background sync for when connectivity returns
self.addEventListener('sync', e => {
  if (e.tag === 'solarpunk-sync') {
    e.waitUntil(syncWithDesktop());
  }
});

async function syncWithDesktop() {
  try {
    const r = await fetch('https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main/data/live_wire_report.json');
    const data = await r.json();
    const clients = await self.clients.matchAll();
    clients.forEach(c => c.postMessage({ type: 'sync', data }));
  } catch(e) { /* offline, will retry */ }
}
