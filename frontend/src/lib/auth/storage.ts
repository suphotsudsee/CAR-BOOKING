const STORAGE_KEY = 'ovbs.session';

export type SessionPersistence = 'local' | 'session';

export interface StoredSession {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
  persist: SessionPersistence;
}

function isBrowser(): boolean {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
}

function getStorage(persist: SessionPersistence): Storage {
  return persist === 'local' ? window.localStorage : window.sessionStorage;
}

export function loadStoredSession(): StoredSession | null {
  if (!isBrowser()) {
    return null;
  }

  const fromLocal = window.localStorage.getItem(STORAGE_KEY);
  if (fromLocal) {
    try {
      const parsed = JSON.parse(fromLocal) as Omit<StoredSession, 'persist'>;
      return { ...parsed, persist: 'local' };
    } catch (error) {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  }

  const fromSession = window.sessionStorage.getItem(STORAGE_KEY);
  if (fromSession) {
    try {
      const parsed = JSON.parse(fromSession) as Omit<StoredSession, 'persist'>;
      return { ...parsed, persist: 'session' };
    } catch (error) {
      window.sessionStorage.removeItem(STORAGE_KEY);
    }
  }

  return null;
}

export function saveStoredSession(
  session: Omit<StoredSession, 'persist'>,
  persist: SessionPersistence,
): void {
  if (!isBrowser()) {
    return;
  }

  const target = getStorage(persist);
  const payload = JSON.stringify(session);
  target.setItem(STORAGE_KEY, payload);

  const alternate = persist === 'local' ? window.sessionStorage : window.localStorage;
  alternate.removeItem(STORAGE_KEY);
}

export function clearStoredSession(): void {
  if (!isBrowser()) {
    return;
  }
  window.localStorage.removeItem(STORAGE_KEY);
  window.sessionStorage.removeItem(STORAGE_KEY);
}
