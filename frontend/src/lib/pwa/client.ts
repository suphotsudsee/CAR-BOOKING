/* eslint-disable no-console */
const SW_PATH = '/sw.js';

function isBrowser(): boolean {
  return typeof window !== 'undefined';
}

function base64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');

  const rawData = window.atob(base64);
  const buffer = new ArrayBuffer(rawData.length);
  const outputArray = new Uint8Array(buffer);

  for (let i = 0; i < rawData.length; i += 1) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (!isBrowser() || !('serviceWorker' in navigator)) {
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.register(SW_PATH, { scope: '/' });
    await navigator.serviceWorker.ready;
    return registration;
  } catch (error) {
    console.error('Failed to register service worker', error);
    return null;
  }
}

export async function getServiceWorkerRegistration(): Promise<ServiceWorkerRegistration | null> {
  if (!isBrowser() || !('serviceWorker' in navigator)) {
    return null;
  }
  const registration = await navigator.serviceWorker.ready.catch(() => null);
  return registration ?? null;
}

export async function requestNotificationPermission(): Promise<NotificationPermission> {
  if (!isBrowser() || !('Notification' in window)) {
    return 'denied';
  }
  if (Notification.permission === 'default') {
    return Notification.requestPermission();
  }
  return Notification.permission;
}

export interface PushSubscriptionPayload {
  subscription: PushSubscription;
  endpoint: string;
}

export async function subscribeUserToPush(publicKey?: string): Promise<PushSubscriptionPayload | null> {
  if (!isBrowser() || !('serviceWorker' in navigator) || !('PushManager' in window)) {
    return null;
  }

  const registration = await getServiceWorkerRegistration();
  if (!registration) {
    return null;
  }

  const permission = await requestNotificationPermission();
  if (permission !== 'granted') {
    throw new Error('จำเป็นต้องเปิดสิทธิ์การแจ้งเตือนของเบราว์เซอร์');
  }

  const existingSubscription = await registration.pushManager.getSubscription();
  if (existingSubscription) {
    return { subscription: existingSubscription, endpoint: existingSubscription.endpoint };
  }

  if (!publicKey) {
    throw new Error('ยังไม่ได้กำหนด public VAPID key สำหรับ Push Service');
  }

  const applicationServerKey = base64ToUint8Array(publicKey) as unknown as BufferSource;
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey,
  });

  return { subscription, endpoint: subscription.endpoint };
}

export interface QueueRequestPayload {
  url: string;
  options: RequestInit;
}

export async function queueBackgroundRequest(payload: QueueRequestPayload): Promise<void> {
  if (!isBrowser() || !('serviceWorker' in navigator)) {
    throw new Error('Service worker controller is not available');
  }

  const sendMessage = (target: ServiceWorker | null | undefined) => {
    if (!target) {
      throw new Error('Service worker controller is not available');
    }
    target.postMessage({
      type: 'QUEUE_REQUEST',
      payload,
    });
  };

  if (navigator.serviceWorker.controller) {
    sendMessage(navigator.serviceWorker.controller);
    return;
  }

  const registration = await getServiceWorkerRegistration();
  if (registration?.active) {
    sendMessage(registration.active);
    return;
  }

  await new Promise<void>((resolve, reject) => {
    const handleControllerChange = () => {
      window.clearTimeout(timeout);
      window.removeEventListener('controllerchange', handleControllerChange);
      if (navigator.serviceWorker.controller) {
        sendMessage(navigator.serviceWorker.controller);
        resolve();
      } else {
        reject(new Error('Service worker controller is not available'));
      }
    };

    const timeout = window.setTimeout(() => {
      window.removeEventListener('controllerchange', handleControllerChange);
      reject(new Error('Service worker controller was not ready in time'));
    }, 3000);

    window.addEventListener('controllerchange', handleControllerChange);
  });
}

export async function registerBackgroundSync(tag = 'ovbs-sync'): Promise<void> {
  const registration = await getServiceWorkerRegistration();
  if (!registration || !('sync' in registration)) {
    return;
  }
  try {
    const syncRegistration = registration as ServiceWorkerRegistration & {
      sync: { register: (syncTag: string) => Promise<void> };
    };
    await syncRegistration.sync.register(tag);
  } catch (error) {
    console.error('Failed to register background sync', error);
  }
}

export function onServiceWorkerMessage(callback: (data: unknown) => void): () => void {
  if (!isBrowser() || !navigator.serviceWorker) {
    return () => undefined;
  }

  const handler = (event: MessageEvent) => {
    callback(event.data);
  };

  navigator.serviceWorker.addEventListener('message', handler);

  return () => {
    navigator.serviceWorker.removeEventListener('message', handler);
  };
}
