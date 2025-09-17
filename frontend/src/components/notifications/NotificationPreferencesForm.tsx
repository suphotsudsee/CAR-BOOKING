"use client";

import { FormEvent, useState } from 'react';

import {
  NotificationPreferences,
  PreferencesUpdatePayload,
} from './useNotificationCenter';

interface NotificationPreferencesFormProps {
  preferences: NotificationPreferences;
  onUpdate: (payload: PreferencesUpdatePayload) => Promise<void>;
}

export function NotificationPreferencesForm({
  preferences,
  onUpdate,
}: NotificationPreferencesFormProps) {
  const [lineToken, setLineToken] = useState('');
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  const handleToggle = async (field: keyof PreferencesUpdatePayload, value: boolean) => {
    setSaving(true);
    setStatus(null);
    try {
      await onUpdate({ [field]: value } as PreferencesUpdatePayload);
      setStatus('บันทึกการตั้งค่าเรียบร้อยแล้ว');
    } catch (err: any) {
      setStatus(err.message ?? 'เกิดข้อผิดพลาดในการบันทึก');
    } finally {
      setSaving(false);
    }
  };

  const handleLineTokenSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setStatus(null);
    try {
      await onUpdate({ line_access_token: lineToken || null });
      setLineToken('');
      setStatus('อัปเดต LINE Notify token สำเร็จ');
    } catch (err: any) {
      setStatus(err.message ?? 'ไม่สามารถอัปเดต LINE token');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">การตั้งค่าการแจ้งเตือน</h3>
        {saving && <span className="text-sm text-primary-500">กำลังบันทึก...</span>}
      </div>
      <p className="mt-2 text-sm text-gray-500">
        เปิดหรือปิดช่องทางการแจ้งเตือนที่คุณต้องการใช้งานได้จากที่นี่
      </p>

      <div className="mt-4 space-y-4">
        <label className="flex items-start gap-3">
          <input
            type="checkbox"
            className="mt-1 h-4 w-4 rounded border-gray-300"
            checked={preferences.inAppEnabled}
            onChange={(event) => handleToggle('in_app_enabled', event.target.checked)}
          />
          <div>
            <span className="font-medium text-gray-900">แจ้งเตือนในระบบ</span>
            <p className="text-sm text-gray-500">
              แสดงประกาศในศูนย์แจ้งเตือนของระบบและเครื่องมือแบบเรียลไทม์
            </p>
          </div>
        </label>

        <label className="flex items-start gap-3">
          <input
            type="checkbox"
            className="mt-1 h-4 w-4 rounded border-gray-300"
            checked={preferences.emailEnabled}
            onChange={(event) => handleToggle('email_enabled', event.target.checked)}
          />
          <div>
            <span className="font-medium text-gray-900">อีเมล</span>
            <p className="text-sm text-gray-500">
              รับสำเนาอีเมลเมื่อมีการอัปเดตสำคัญของคำขอจองรถ
            </p>
          </div>
        </label>

        <div className="rounded-lg border border-gray-100 p-4">
          <div className="flex items-start gap-3">
            <input
              type="checkbox"
              className="mt-1 h-4 w-4 rounded border-gray-300"
              checked={preferences.lineEnabled}
              onChange={(event) => handleToggle('line_enabled', event.target.checked)}
            />
            <div className="flex-1">
              <span className="font-medium text-gray-900">LINE Notify</span>
              <p className="text-sm text-gray-500">
                ส่งข้อความแจ้งเตือนไปยังแอป LINE แบบทันทีเมื่อมีการอนุมัติหรือปฏิเสธคำขอ
              </p>

              <form className="mt-3 flex flex-col gap-3 md:flex-row" onSubmit={handleLineTokenSubmit}>
                <input
                  type="text"
                  placeholder="ใส่ LINE Notify token"
                  value={lineToken}
                  onChange={(event) => setLineToken(event.target.value)}
                  className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-200"
                  disabled={saving}
                />
                <button
                  type="submit"
                  className="rounded-lg bg-primary-500 px-4 py-2 text-sm font-medium text-white hover:bg-primary-600 disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={saving}
                >
                  บันทึก Token
                </button>
              </form>

              <p className="mt-2 text-sm text-gray-500">
                สถานะ: {preferences.lineTokenRegistered ? 'เชื่อมต่อแล้ว' : 'ยังไม่ได้เชื่อมต่อ'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {status && <p className="mt-4 text-sm text-green-600">{status}</p>}
    </div>
  );
}

