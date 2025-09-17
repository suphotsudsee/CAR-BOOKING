'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';

import {
  SessionPersistence,
  StoredSession,
  clearStoredSession,
  loadStoredSession,
  saveStoredSession,
} from '@/lib/auth/storage';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? '';
const REFRESH_MARGIN_MS = 60_000; // refresh 60 seconds before expiry

export const USER_ROLES = {
  REQUESTER: 'requester',
  MANAGER: 'manager',
  FLEET_ADMIN: 'fleet_admin',
  DRIVER: 'driver',
  AUDITOR: 'auditor',
} as const;

export type UserRole = (typeof USER_ROLES)[keyof typeof USER_ROLES];

export interface AuthUser {
  id: number;
  username: string;
  email: string;
  fullName: string;
  department: string | null;
  role: UserRole;
  isActive: boolean;
  twoFactorEnabled: boolean;
}

interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  expiresAt: number | null;
  persist: SessionPersistence | null;
  initializing: boolean;
}

interface LoginPayload {
  username: string;
  password: string;
  remember?: boolean;
}

interface ProfileUpdatePayload {
  fullName?: string;
  email?: string;
  department?: string | null;
  twoFactorEnabled?: boolean;
}

interface AuthContextValue {
  user: AuthUser | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  initializing: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  logout: () => void;
  refreshAccessToken: () => Promise<string | null>;
  updateProfile: (payload: ProfileUpdatePayload) => Promise<AuthUser>;
  authenticatedFetch: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function normaliseUser(payload: UserResponse): AuthUser {
  return {
    id: payload.id,
    username: payload.username,
    email: payload.email,
    fullName: payload.full_name,
    department: payload.department ?? null,
    role: payload.role,
    isActive: payload.is_active,
    twoFactorEnabled: payload.two_fa_enabled,
  };
}

async function requestLogin(username: string, password: string) {
  const response = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const message = typeof data?.detail === 'string' ? data.detail : 'ไม่สามารถเข้าสู่ระบบได้';
    throw new Error(message);
  }

  return response.json() as Promise<{
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
  }>;
}

async function requestProfile(token: string): Promise<UserResponse> {
  const response = await fetch(`${API_URL}/api/v1/users/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    throw new Error('ไม่สามารถโหลดข้อมูลผู้ใช้');
  }
  return response.json();
}

async function requestRefresh(refreshToken: string) {
  const response = await fetch(`${API_URL}/api/v1/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const message = typeof data?.detail === 'string' ? data.detail : 'ไม่สามารถต่ออายุเซสชันได้';
    throw new Error(message);
  }
  return response.json() as Promise<{
    access_token: string;
    expires_in: number;
    token_type: string;
    issued_at?: string;
  }>;
}

const initialState: AuthState = {
  user: null,
  accessToken: null,
  refreshToken: null,
  expiresAt: null,
  persist: null,
  initializing: true,
};

interface UserResponse {
  id: number;
  username: string;
  email: string;
  full_name: string;
  department?: string | null;
  role: UserRole;
  is_active: boolean;
  two_fa_enabled: boolean;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>(initialState);
  const refreshPromiseRef = useRef<Promise<string | null> | null>(null);

  const logout = useCallback(() => {
    clearStoredSession();
    setState({
      user: null,
      accessToken: null,
      refreshToken: null,
      expiresAt: null,
      persist: null,
      initializing: false,
    });
  }, []);

  const refreshAccessToken = useCallback(async () => {
    if (!state.refreshToken) {
      logout();
      return null;
    }

    if (refreshPromiseRef.current) {
      return refreshPromiseRef.current;
    }

    refreshPromiseRef.current = (async () => {
      try {
        const data = await requestRefresh(state.refreshToken as string);
        const expiresAt = Date.now() + data.expires_in * 1000;
        const persist = state.persist ?? 'local';
        saveStoredSession(
          {
            accessToken: data.access_token,
            refreshToken: state.refreshToken as string,
            expiresAt,
          },
          persist,
        );
        setState((prev) => ({
          ...prev,
          accessToken: data.access_token,
          expiresAt,
          persist,
        }));
        return data.access_token;
      } catch (error) {
        logout();
        throw error;
      } finally {
        refreshPromiseRef.current = null;
      }
    })();

    return refreshPromiseRef.current;
  }, [logout, state.persist, state.refreshToken]);

  const authenticatedFetch = useCallback(
    async (input: RequestInfo | URL, init: RequestInit = {}) => {
      if (!state.accessToken) {
        throw new Error('ต้องเข้าสู่ระบบก่อนใช้งาน');
      }

      const headers = new Headers(init.headers ?? undefined);
      if (!headers.has('Authorization')) {
        headers.set('Authorization', `Bearer ${state.accessToken}`);
      }

      const body = init.body;
      const shouldSetJson =
        body !== undefined &&
        !(body instanceof FormData) &&
        !headers.has('Content-Type');
      if (shouldSetJson) {
        headers.set('Content-Type', 'application/json');
      }

      let response = await fetch(input, { ...init, headers });
      if (response.status !== 401) {
        return response;
      }

      try {
        const newToken = await refreshAccessToken();
        if (!newToken) {
          return response;
        }
        headers.set('Authorization', `Bearer ${newToken}`);
        response = await fetch(input, { ...init, headers });
        if (response.status === 401) {
          logout();
        }
        return response;
      } catch (error) {
        logout();
        throw error;
      }
    },
    [logout, refreshAccessToken, state.accessToken],
  );

  const updateProfile = useCallback(
    async (payload: ProfileUpdatePayload) => {
      const response = await authenticatedFetch(`${API_URL}/api/v1/users/me`, {
        method: 'PATCH',
        body: JSON.stringify({
          full_name: payload.fullName,
          email: payload.email,
          department: payload.department,
          two_fa_enabled: payload.twoFactorEnabled,
        }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        const message = typeof data?.detail === 'string' ? data.detail : 'ไม่สามารถอัปเดตโปรไฟล์ได้';
        throw new Error(message);
      }

      const data = await response.json();
      const user = normaliseUser(data);
      setState((prev) => ({
        ...prev,
        user,
      }));
      return user;
    },
    [authenticatedFetch],
  );

  const initialiseFromStorage = useCallback(async () => {
    const stored = loadStoredSession();
    if (!stored) {
      setState((prev) => ({ ...prev, initializing: false }));
      return;
    }

    setState((prev) => ({
      ...prev,
      accessToken: stored.accessToken,
      refreshToken: stored.refreshToken,
      expiresAt: stored.expiresAt,
      persist: stored.persist,
    }));

    const loadUserWithToken = async (token: string, session: StoredSession) => {
      const profileData = await requestProfile(token);
      const user = normaliseUser(profileData);
      setState({
        user,
        accessToken: token,
        refreshToken: session.refreshToken,
        expiresAt: session.expiresAt,
        persist: session.persist,
        initializing: false,
      });
    };

    try {
      if (stored.expiresAt && stored.expiresAt <= Date.now() + REFRESH_MARGIN_MS) {
        const refreshed = await requestRefresh(stored.refreshToken);
        const expiresAt = Date.now() + refreshed.expires_in * 1000;
        const session: StoredSession = {
          accessToken: refreshed.access_token,
          refreshToken: stored.refreshToken,
          expiresAt,
          persist: stored.persist,
        };
        saveStoredSession(
          {
            accessToken: session.accessToken,
            refreshToken: session.refreshToken,
            expiresAt: session.expiresAt,
          },
          session.persist,
        );
        await loadUserWithToken(session.accessToken, session);
      } else {
        await loadUserWithToken(stored.accessToken, stored);
      }
    } catch (error) {
      try {
        const refreshed = await requestRefresh(stored.refreshToken);
        const expiresAt = Date.now() + refreshed.expires_in * 1000;
        const session: StoredSession = {
          accessToken: refreshed.access_token,
          refreshToken: stored.refreshToken,
          expiresAt,
          persist: stored.persist,
        };
        saveStoredSession(
          {
            accessToken: session.accessToken,
            refreshToken: session.refreshToken,
            expiresAt: session.expiresAt,
          },
          session.persist,
        );
        await loadUserWithToken(session.accessToken, session);
      } catch (refreshError) {
        logout();
      }
    }
  }, [logout]);

  useEffect(() => {
    void initialiseFromStorage();
  }, [initialiseFromStorage]);

  useEffect(() => {
    if (!state.accessToken || !state.refreshToken || !state.expiresAt) {
      return;
    }

    const now = Date.now();
    const refreshDelay = Math.max(state.expiresAt - now - REFRESH_MARGIN_MS, 1_000);
    const expiryDelay = Math.max(state.expiresAt - now, 0);

    const refreshTimer = window.setTimeout(() => {
      void refreshAccessToken();
    }, refreshDelay);

    const expiryTimer = window.setTimeout(() => {
      logout();
    }, expiryDelay);

    return () => {
      window.clearTimeout(refreshTimer);
      window.clearTimeout(expiryTimer);
    };
  }, [logout, refreshAccessToken, state.accessToken, state.expiresAt, state.refreshToken]);

  const login = useCallback(
    async ({ username, password, remember = true }: LoginPayload) => {
      const data = await requestLogin(username, password);
      const expiresAt = Date.now() + data.expires_in * 1000;
      const persist: SessionPersistence = remember ? 'local' : 'session';
      const session: StoredSession = {
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        expiresAt,
        persist,
      };

      saveStoredSession(
        {
          accessToken: session.accessToken,
          refreshToken: session.refreshToken,
          expiresAt: session.expiresAt,
        },
        persist,
      );

      const profile = await requestProfile(session.accessToken);
      const user = normaliseUser(profile);
      setState({
        user,
        accessToken: session.accessToken,
        refreshToken: session.refreshToken,
        expiresAt: session.expiresAt,
        persist,
        initializing: false,
      });
    },
    [],
  );

  const contextValue = useMemo<AuthContextValue>(
    () => ({
      user: state.user,
      accessToken: state.accessToken,
      isAuthenticated: Boolean(state.user && state.accessToken),
      initializing: state.initializing,
      login,
      logout,
      refreshAccessToken,
      updateProfile,
      authenticatedFetch,
    }),
    [authenticatedFetch, login, logout, refreshAccessToken, state.accessToken, state.initializing, state.user, updateProfile],
  );

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
