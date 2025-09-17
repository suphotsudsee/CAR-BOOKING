"use client";

import { FormEvent, useState } from 'react';

import { useAuth } from '@/context/AuthContext';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';

import { NotificationHistoryList } from './NotificationHistoryList';
import { NotificationPreferencesForm } from './NotificationPreferencesForm';
import { UseNotificationCenterResult, useNotificationCenter } from './useNotificationCenter';

interface NotificationCenterProps {
  controller?: UseNotificationCenterResult;
}

export function NotificationCenter({ controller }: NotificationCenterProps) {
  const { isAuthenticated } = useAuth();
  const isOnline = useOnlineStatus();
  const fallbackController = useNotificationCenter();
  const {
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
    registerPushNotifications,
  } = controller ?? fallbackController;

  const [testTitle, setTestTitle] = useState('ทดสอบระบบแจ้งเตือน');
  const [testMessage, setTestMessage] = useState('นี่คือข้อความตัวอย่างสำหรับตรวจสอบการตั้งค่า');
  const [sendingTest, setSendingTest] = useState(false);
  const [testStatus, setTestStatus] = useState<string | null>(null);
  const [pushStatus, setPushStatus] = useState<string | null>(null);
  const [enablingPush, setEnablingPush] = useState(false);

  if (!isAuthenticated) {
    return (
      <div className="rounded-lg border border-dashed border-gray-300 bg-white p-6 text-center shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900">เข้าสู่ระบบเพื่อดูการแจ้งเตือน</h3>
        <p className="mt-2 text-sm text-gray-500">
          เมื่อมีการอนุมัติหรือปฏิเสธคำขอจองรถ ระบบจะแจ้งเตือนแบบเรียลไทม์ที่นี่
        </p>
      </div>
    );
  }

  const handleTestSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSendingTest(true);
    setTestStatus(null);
    try {
      const result = await sendTestNotification(testTitle, testMessage);
      if (result === 'queued') {
        setTestStatus('บันทึกคำขอเรียบร้อย ระบบจะส่งให้อัตโนมัติเมื่อกลับมาออนไลน์');
      } else {
        setTestStatus('ส่งข้อความทดสอบเรียบร้อยแล้ว');
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'ไม่สามารถส่งข้อความทดสอบ';
      setTestStatus(message);
    } finally {
      setSendingTest(false);
    }
  };

  const handleEnablePush = async () => {
    setEnablingPush(true);
    setPushStatus(null);
    try {
      await registerPushNotifications();
      setPushStatus('เปิดใช้งานการแจ้งเตือนผ่านเบราว์เซอร์เรียบร้อยแล้ว');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'ไม่สามารถเปิดใช้งานการแจ้งเตือนแบบพุช';
      setPushStatus(message);
    } finally {
      setEnablingPush(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">ศูนย์การแจ้งเตือน</h2>
          <p className="mt-1 text-sm text-gray-500">
            จัดการการแจ้งเตือนหลายช่องทางและดูสถานะล่าสุดได้ในจุดเดียว
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {!isOnline && (
            <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">โหมดออฟไลน์</span>
          )}
          <button
            type="button"
            onClick={() => {
              void refresh();
            }}
            className="rounded-full border border-primary-200 px-4 py-2 text-sm font-medium text-primary-600 transition hover:bg-primary-50"
          >
            รีเฟรชข้อมูล
          </button>
          {loading && <span className="text-sm text-gray-500">กำลังโหลด...</span>}
        </div>
      </div>

      <div className="rounded-xl border border-primary-100 bg-primary-50 px-4 py-3 text-sm text-primary-700 shadow-sm">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="font-semibold">เปิดใช้งานการแจ้งเตือนผ่านเบราว์เซอร์</p>
            <p className="text-xs text-primary-600">
              ระบบจะส่งการแจ้งเตือนแบบพุชเมื่อมีการอนุมัติคำขอจองรถ แม้ปิดหน้าจอไว้
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              void handleEnablePush();
            }}
            disabled={enablingPush}
            className="inline-flex items-center gap-2 rounded-full bg-primary-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-primary-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {enablingPush ? 'กำลังเปิดใช้งาน...' : 'เปิดใช้งานการแจ้งเตือน'}
          </button>
        </div>
        {pushStatus && <p className="mt-2 text-xs text-primary-700">{pushStatus}</p>}
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {!preferences && !error && (
        <div className="rounded-lg border border-gray-200 bg-white px-4 py-3 text-sm text-gray-500">
          กำลังเตรียมข้อมูลการตั้งค่าการแจ้งเตือน...
        </div>
      )}

      {preferences && <NotificationPreferencesForm preferences={preferences} onUpdate={updatePreferences} />}

      <form onSubmit={handleTestSubmit} className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900">ส่งข้อความทดสอบ</h3>
        <p className="mt-1 text-sm text-gray-500">
          ใช้แบบฟอร์มนี้เพื่อตรวจสอบว่าการตั้งค่าการแจ้งเตือนและ LINE Notify ทำงานถูกต้อง
        </p>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-gray-700">หัวข้อ</label>
            <input
              type="text"
              value={testTitle}
              onChange={(event) => setTestTitle(event.target.value)}
              className="rounded-xl border border-gray-300 px-3 py-2 text-sm focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-200"
              disabled={sendingTest}
            />
          </div>
          <div className="flex flex-col gap-2 md:col-span-2">
            <label className="text-sm font-medium text-gray-700">ข้อความ</label>
            <textarea
              value={testMessage}
              onChange={(event) => setTestMessage(event.target.value)}
              rows={3}
              className="rounded-xl border border-gray-300 px-3 py-2 text-sm focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-200"
              disabled={sendingTest}
            />
          </div>
        </div>
        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
          <button
            type="submit"
            className="inline-flex items-center justify-center rounded-full bg-primary-500 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-primary-600 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={sendingTest}
          >
            ส่งข้อความทดสอบ
          </button>
          {testStatus && <span className="text-sm text-green-600">{testStatus}</span>}
          {!isOnline && (
            <span className="text-xs text-amber-600">
              เราจะบันทึกคำขอนี้และส่งให้อัตโนมัติเมื่อกลับมาออนไลน์
            </span>
          )}
        </div>
      </form>

      <NotificationHistoryList
        notifications={notifications}
        onMarkAsRead={markAsRead}
        onMarkAll={markAllRead}
        unreadCount={unreadCount}
        loading={loading}
      />
    </div>
  );
}
