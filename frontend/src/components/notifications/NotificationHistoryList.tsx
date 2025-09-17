"use client";

import { useMemo } from 'react';

import { SwipeableListItem } from '@/components/ui/SwipeableListItem';

import { NotificationItem } from './useNotificationCenter';

interface NotificationHistoryListProps {
  notifications: NotificationItem[];
  onMarkAsRead: (id: number) => Promise<void>;
  onMarkAll: () => Promise<void>;
  unreadCount: number;
  loading: boolean;
}

const dateFormatter = new Intl.DateTimeFormat('th-TH', {
  dateStyle: 'medium',
  timeStyle: 'short',
});

export function NotificationHistoryList({
  notifications,
  onMarkAsRead,
  onMarkAll,
  unreadCount,
  loading,
}: NotificationHistoryListProps) {
  const sortedNotifications = useMemo(
    () => [...notifications].sort((a, b) => b.id - a.id),
    [notifications]
  );

  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">ประวัติการแจ้งเตือน</h3>
          <p className="text-sm text-gray-500">แจ้งเตือนล่าสุดจะแสดงอยู่ด้านบนสุด</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="rounded-full bg-primary-50 px-3 py-1 text-sm text-primary-600">
            ยังไม่ได้อ่าน {unreadCount} รายการ
          </span>
          <button
            type="button"
            onClick={() => {
              void onMarkAll().catch((err) => console.error(err));
            }}
            disabled={loading || unreadCount === 0}
            className="rounded-lg border border-primary-200 px-4 py-2 text-sm font-medium text-primary-600 transition hover:bg-primary-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            ทำเครื่องหมายว่าอ่านทั้งหมด
          </button>
        </div>
      </div>

      <ul className="divide-y divide-gray-100">
        {sortedNotifications.length === 0 && (
          <li className="px-6 py-8 text-center text-sm text-gray-500">
            ยังไม่มีการแจ้งเตือนในระบบ ลองส่งข้อความทดสอบเพื่อเริ่มใช้งาน
          </li>
        )}

        {sortedNotifications.map((notification) => {
          const createdLabel = notification.createdAt
            ? dateFormatter.format(new Date(notification.createdAt))
            : '-';

          return (
            <li key={notification.id} className="px-3 py-3 sm:px-6">
              <SwipeableListItem
                onSwipeLeft={() => {
                  if (!notification.readAt) {
                    void onMarkAsRead(notification.id).catch((err) => console.error(err));
                  }
                }}
                actionContent={!notification.readAt ? 'อ่านแล้ว' : 'เสร็จสิ้น'}
              >
                <div className="flex flex-col gap-4 px-3 py-4 md:flex-row md:items-center md:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-semibold uppercase tracking-wide text-primary-500">
                        {notification.category}
                      </span>
                      {notification.deliveredChannels.map((channel) => (
                        <span
                          key={channel}
                          className="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] font-medium text-gray-600"
                        >
                          {channel.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                    <p className="mt-2 text-base font-semibold text-gray-900">{notification.title}</p>
                    <p className="mt-2 text-sm leading-relaxed text-gray-600">{notification.message}</p>
                    <p className="mt-3 text-xs text-gray-400">สร้างเมื่อ {createdLabel}</p>

                    {Object.keys(notification.deliveryErrors ?? {}).length > 0 && (
                      <p className="mt-2 text-xs text-red-500">
                        ไม่สามารถส่งบางช่องทาง: {Object.values(notification.deliveryErrors).join(', ')}
                      </p>
                    )}
                  </div>

                  <div className="flex flex-row items-center gap-3 self-start md:flex-col md:items-end">
                    {notification.readAt ? (
                      <span className="rounded-full bg-green-50 px-3 py-1 text-xs font-medium text-green-600">
                        อ่านแล้ว
                      </span>
                    ) : (
                      <button
                        type="button"
                        onClick={() => {
                          void onMarkAsRead(notification.id).catch((err) => console.error(err));
                        }}
                        className="rounded-full bg-primary-500 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-primary-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500"
                      >
                        แตะหรือปัดเพื่่ออ่านแล้ว
                      </button>
                    )}
                  </div>
                </div>
              </SwipeableListItem>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

