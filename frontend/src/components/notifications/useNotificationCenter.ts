"use client";

import { useCallback, useEffect, useMemo, useState } from 'react';

import { useAuth } from '@/context/AuthContext';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? '';

interface NotificationResponse {
  id: number;
  title: string;
  message: string;
  category: string;
  data?: Record<string, unknown> | null;
  created_at: string;
  read_at?: string | null;
  delivered_channels?: string[] | null;
  delivery_errors?: Record<string, string> | null;
}

interface NotificationPreferencesResponse {
  in_app_enabled: boolean;
  email_enabled: boolean;
  line_enabled: boolean;
  line_token_registered: boolean;
  updated_at: string;
}

export interface NotificationItem {
  id: number;
  title: string;
  message: string;
  category: string;
  data: Record<string, unknown>;
  createdAt: string;
  readAt: string | null;
  deliveredChannels: string[];
  deliveryErrors: Record<string, string>;
}

export interface NotificationPreferences {
  inAppEnabled: boolean;
  emailEnabled: boolean;
  lineEnabled: boolean;
  lineTokenRegistered: boolean;
  updatedAt: string;
}

export interface PreferencesUpdatePayload {
  in_app_enabled?: boolean;
  email_enabled?: boolean;
  line_enabled?: boolean;
  line_access_token?: string | null;
}

export interface UseNotificationCenterResult {
  notifications: NotificationItem[];
  preferences: NotificationPreferences | null;
  unreadCount: number;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  markAsRead: (id: number) => Promise<void>;
  markAllRead: () => Promise<void>;
  updatePreferences: (payload: PreferencesUpdatePayload) => Promise<void>;
  sendTestNotification: (title: string, message: string) => Promise<void>;
}

function normaliseNotification(payload: NotificationResponse): NotificationItem {
  return {
    id: payload.id,
    title: payload.title,
    message: payload.message,
    category: payload.category,
    data: payload.data ?? {},
    createdAt: payload.created_at,
    readAt: payload.read_at ?? null,
    deliveredChannels: payload.delivered_channels ?? [],
    deliveryErrors: payload.delivery_errors ?? {},
  };
}

function normalisePreferences(payload: NotificationPreferencesResponse): NotificationPreferences {
  return {
    inAppEnabled: payload.in_app_enabled,
    emailEnabled: payload.email_enabled,
    lineEnabled: payload.line_enabled,
    lineTokenRegistered: payload.line_token_registered,
    updatedAt: payload.updated_at,
  };
}

export function useNotificationCenter(): UseNotificationCenterResult {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { accessToken, authenticatedFetch, isAuthenticated } = useAuth();

  const fetchNotifications = useCallback(async () => {
    if (!isAuthenticated) return;
    const response = await authenticatedFetch(`${API_URL}/api/v1/notifications/`);
    if (!response.ok) {
      throw new Error('ไม่สามารถโหลดการแจ้งเตือน');
    }
    const data = await response.json();
    const parsed = Array.isArray(data) ? data.map(normaliseNotification) : [];
    setNotifications(parsed);
    setUnreadCount(parsed.filter((item) => !item.readAt).length);
  }, [authenticatedFetch, isAuthenticated]);

  const fetchPreferences = useCallback(async () => {
    if (!isAuthenticated) return;
    const response = await authenticatedFetch(`${API_URL}/api/v1/notifications/preferences`);
    if (!response.ok) {
      throw new Error('ไม่สามารถโหลดการตั้งค่าการแจ้งเตือน');
    }
    const data = await response.json();
    setPreferences(normalisePreferences(data));
  }, [authenticatedFetch, isAuthenticated]);

  const fetchUnread = useCallback(async () => {
    if (!isAuthenticated) return;
    const response = await authenticatedFetch(`${API_URL}/api/v1/notifications/unread-count`);
    if (!response.ok) return;
    const data = await response.json();
    if (typeof data?.unread === 'number') {
      setUnreadCount(data.unread);
    }
  }, [authenticatedFetch, isAuthenticated]);

  const refresh = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    setError(null);
    try {
      await Promise.all([fetchNotifications(), fetchPreferences(), fetchUnread()]);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'เกิดข้อผิดพลาด';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [fetchNotifications, fetchPreferences, fetchUnread, isAuthenticated]);

  const markAsRead = useCallback(
    async (id: number) => {
      if (!isAuthenticated) return;
      const response = await authenticatedFetch(`${API_URL}/api/v1/notifications/${id}/read`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('ไม่สามารถอัปเดตสถานะการอ่าน');
      }
      const data = await response.json();
      const updated = normaliseNotification(data.notification);
      setNotifications((items) => {
        let shouldDecrement = false;
        const nextItems = items.map((item) => {
          if (item.id !== updated.id) {
            return item;
          }
          if (!item.readAt && updated.readAt) {
            shouldDecrement = true;
          }
          return { ...item, readAt: updated.readAt };
        });
        if (shouldDecrement) {
          setUnreadCount((count) => Math.max(count - 1, 0));
        }
        return nextItems;
      });
    },
    [authenticatedFetch, isAuthenticated]
  );

  const markAllRead = useCallback(async () => {
    if (!isAuthenticated) return;
    const response = await authenticatedFetch(`${API_URL}/api/v1/notifications/read-all`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error('ไม่สามารถอัปเดตสถานะการอ่านทั้งหมด');
    }
    setNotifications((items) => items.map((item) => ({ ...item, readAt: new Date().toISOString() })));
    setUnreadCount(0);
  }, [authenticatedFetch, isAuthenticated]);

  const updatePreferences = useCallback(
    async (payload: PreferencesUpdatePayload) => {
      if (!isAuthenticated) return;
      const response = await authenticatedFetch(`${API_URL}/api/v1/notifications/preferences`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error('ไม่สามารถอัปเดตการตั้งค่า');
      }
      const data = await response.json();
      setPreferences(normalisePreferences(data));
    },
    [authenticatedFetch, isAuthenticated]
  );

  const sendTestNotification = useCallback(
    async (title: string, message: string) => {
      if (!isAuthenticated) return;
      const response = await authenticatedFetch(`${API_URL}/api/v1/notifications/dispatch-test`, {
        method: 'POST',
        body: JSON.stringify({ title, message, category: 'test' }),
      });
      if (!response.ok) {
        throw new Error('ไม่สามารถส่งข้อความทดสอบ');
      }
      const data = await response.json();
      const created = normaliseNotification(data);
      setNotifications((items) => [created, ...items.filter((item) => item.id !== created.id)]);
      setUnreadCount((count) => count + 1);
    },
    [authenticatedFetch, isAuthenticated]
  );

  useEffect(() => {
    if (!isAuthenticated) {
      setNotifications([]);
      setPreferences(null);
      setUnreadCount(0);
      return;
    }
    refresh();
  }, [isAuthenticated, refresh]);

  const websocketUrl = useMemo(() => {
    if (!accessToken || !API_URL) return null;
    try {
      const url = new URL('/ws/notifications', API_URL);
      url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
      url.searchParams.set('token', accessToken);
      return url.toString();
    } catch (err) {
      console.error('Unable to construct notification websocket URL', err);
      return null;
    }
  }, [accessToken]);

  useEffect(() => {
    if (!websocketUrl) return;

    const socket = new WebSocket(websocketUrl);

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === 'notification.created') {
          const created = normaliseNotification(payload.payload);
          setNotifications((items) => [created, ...items.filter((item) => item.id !== created.id)]);
          setUnreadCount((count) => count + 1);
        }
        if (payload.type === 'notification.read') {
          setNotifications((items) => {
            let shouldDecrement = false;
            const nextItems = items.map((item) => {
              if (item.id !== payload.payload?.id) {
                return item;
              }
              const readAt = payload.payload?.read_at ?? item.readAt;
              if (!item.readAt && payload.payload?.read_at) {
                shouldDecrement = true;
              }
              return { ...item, readAt };
            });
            if (shouldDecrement) {
              setUnreadCount((count) => Math.max(count - 1, 0));
            }
            return nextItems;
          });
        }
      } catch (err) {
        console.error('Failed to parse notification payload', err);
      }
    };

    socket.onerror = () => {
      setError('การเชื่อมต่อการแจ้งเตือนแบบเรียลไทม์ขัดข้อง');
    };

    return () => {
      socket.close();
    };
  }, [websocketUrl]);

  return {
    notifications,
    preferences,
    unreadCount,
    loading,
    error,
    refresh,
    markAsRead,
    markAllRead,
    updatePreferences,
    sendTestNotification,
  };
}

