/* eslint-disable no-restricted-globals */
const APP_VERSION = 'v1.0.0';
const STATIC_CACHE = `ovbs-static-${APP_VERSION}`;
const API_CACHE = `ovbs-api-${APP_VERSION}`;
const OFFLINE_URL = '/offline.html';
const SYNC_TAG = 'ovbs-sync';
const STATIC_ASSETS = [
  '/',
  OFFLINE_URL,
  '/manifest.json',
  '/icons/app-icon.svg',
  '/icons/app-icon-maskable.svg',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(STATIC_CACHE)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key !== STATIC_CACHE && key !== API_CACHE)
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

function cacheFirst(request) {
  return caches.match(request).then((cached) => {
    if (cached) {
      return cached;
    }
    return fetch(request)
      .then((response) => {
        if (!response || response.status !== 200 || response.type !== 'basic') {
          return response;
        }
        const cloned = response.clone();
        caches.open(STATIC_CACHE).then((cache) => cache.put(request, cloned));
        return response;
      })
      .catch(() => caches.match(OFFLINE_URL));
  });
}

function networkFirst(request) {
  return fetch(request)
    .then((response) => {
      if (response && response.status === 200) {
        const cloned = response.clone();
        caches.open(API_CACHE).then((cache) => cache.put(request, cloned));
      }
      return response;
    })
    .catch(() => caches.match(request).then((cached) => cached || caches.match(OFFLINE_URL)));
}

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') {
    return;
  }

  const url = new URL(request.url);

  if (url.origin === self.location.origin) {
    if (STATIC_ASSETS.includes(url.pathname) || url.pathname.startsWith('/_next/')) {
      event.respondWith(cacheFirst(request));
      return;
    }
  }

  if (request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const cloned = response.clone();
          caches.open(STATIC_CACHE).then((cache) => cache.put(request, cloned));
          return response;
        })
        .catch(() => caches.match(request).then((cached) => cached || caches.match(OFFLINE_URL)))
    );
    return;
  }

  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(request));
    return;
  }

  event.respondWith(cacheFirst(request));
});

function openQueueDb() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('ovbs-offline', 1);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains('request-queue')) {
        db.createObjectStore('request-queue', { keyPath: 'id', autoIncrement: true });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function enqueueRequest(payload) {
  const db = await openQueueDb();
  const tx = db.transaction('request-queue', 'readwrite');
  tx.objectStore('request-queue').add({
    createdAt: Date.now(),
    ...payload,
  });
  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve(true);
    tx.onabort = () => reject(tx.error);
    tx.onerror = () => reject(tx.error);
  });
}

async function processQueue() {
  const db = await openQueueDb();
  const tx = db.transaction('request-queue', 'readwrite');
  const store = tx.objectStore('request-queue');
  const items = await new Promise((resolve, reject) => {
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });

  for (const item of items) {
    try {
      const { url, options } = item;
      await fetch(url, options);
      await new Promise((resolve, reject) => {
        const deleteRequest = store.delete(item.id);
        deleteRequest.onsuccess = () => resolve(true);
        deleteRequest.onerror = () => reject(deleteRequest.error);
      });
    } catch (error) {
      console.error('Failed to replay request', error);
    }
  }

  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve(true);
    tx.onabort = () => reject(tx.error);
    tx.onerror = () => reject(tx.error);
  });
}

self.addEventListener('message', (event) => {
  const data = event.data || {};
  if (data.type === 'QUEUE_REQUEST') {
    event.waitUntil(
      enqueueRequest(data.payload).then(() => self.registration.sync.register(SYNC_TAG))
    );
  }
});

self.addEventListener('sync', (event) => {
  if (event.tag === SYNC_TAG) {
    event.waitUntil(processQueue());
  }
});

self.addEventListener('push', (event) => {
  let payload = {};
  try {
    payload = event.data?.json() ?? {};
  } catch (error) {
    payload = { title: 'การแจ้งเตือนใหม่', body: event.data?.text() };
  }

  const title = payload.title || 'ระบบจองรถสำนักงาน';
  const body = payload.body || 'คุณมีการอัปเดตใหม่ในคำขอจองรถของคุณ';

  const options = {
    body,
    icon: '/icons/app-icon-maskable.svg',
    badge: '/icons/app-icon.svg',
    data: payload.data || {},
    vibrate: [100, 50, 100],
    actions: [
      { action: 'open', title: 'เปิดรายละเอียด' },
      { action: 'dismiss', title: 'ปิด' },
    ],
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const action = event.action;
  if (action === 'dismiss') {
    return;
  }

  const targetUrl = event.notification.data?.url || '/notifications';
  event.waitUntil(
    clients
      .matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        for (const client of clientList) {
          if ('focus' in client) {
            client.navigate(targetUrl);
            return client.focus();
          }
        }
        if (clients.openWindow) {
          return clients.openWindow(targetUrl);
        }
        return null;
      })
  );
});
