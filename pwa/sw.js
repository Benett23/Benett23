/**
 * Service Worker — PTP App
 * Cache offline, background sync, push notifications
 */

const CACHE_NAME = 'ptp-v2';
const OFFLINE_PAGE = '/offline.html';

const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/ecoles.html',
  '/documents.html',
  '/ptp.css',
  '/offline.html',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
];

// ── Installation ─────────────────────────────────────────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS.filter(url => !url.includes('supabase')));
    }).catch(() => {
      // Ignore cache errors during install
    })
  );
  self.skipWaiting();
});

// ── Activation ────────────────────────────────────────────────────────────────
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// ── Fetch : network-first, fallback cache ─────────────────────────────────────
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Supabase / OneSignal : toujours réseau
  if (url.hostname.includes('supabase.co') || url.hostname.includes('onesignal.com')) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response.ok && event.request.method === 'GET') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() =>
        caches.match(event.request).then((cached) => {
          if (cached) return cached;
          if (event.request.mode === 'navigate') {
            return caches.match(OFFLINE_PAGE);
          }
          return new Response('Offline', { status: 503 });
        })
      )
  );
});

// ── Push notifications ────────────────────────────────────────────────────────
self.addEventListener('push', (event) => {
  if (!event.data) return;

  let data = {};
  try {
    data = event.data.json();
  } catch {
    data = { title: 'PTP', body: event.data.text() };
  }

  const title = data.headings?.fr || data.title || '☀️ PTP Brief';
  const body = data.contents?.fr || data.body || 'Nouveaux éléments dans votre tableau de bord.';
  const icon = '/icons/icon-192.png';
  const badge = '/icons/icon-192.png';
  const url = data.url || '/';

  event.waitUntil(
    self.registration.showNotification(title, {
      body,
      icon,
      badge,
      data: { url },
      vibrate: [200, 100, 200],
      actions: data.buttons
        ? data.buttons.map((b) => ({ action: b.id, title: b.text }))
        : [{ action: 'open', title: 'Ouvrir' }],
      requireInteraction: false,
      tag: 'ptp-brief',
      renotify: true,
    })
  );
});

// ── Clic sur notification ─────────────────────────────────────────────────────
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = event.notification.data?.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.navigate(url);
          return client.focus();
        }
      }
      return clients.openWindow(url);
    })
  );
});
