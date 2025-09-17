"use client";

import { useMemo } from 'react';

import { AlertTriangle, Compass, Footprints, Loader2, MapPin, PauseCircle, PlayCircle } from 'lucide-react';

import type { AccuracyStatus, LocationPoint, LocationSuggestion } from '@/hooks/useLocationTracking';

interface LocationTrackerWidgetProps {
  isSupported: boolean;
  tracking: boolean;
  trackingSince: number | null;
  currentPosition: LocationPoint | null;
  totalDistanceKm: number;
  locationHistory: LocationPoint[];
  suggestions: LocationSuggestion[];
  accuracyStatus: AccuracyStatus | null;
  lastError: string | null;
  onStartTracking: () => void | Promise<void | boolean>;
  onStopTracking: () => void;
}

export function LocationTrackerWidget({
  isSupported,
  tracking,
  trackingSince,
  currentPosition,
  totalDistanceKm,
  locationHistory,
  suggestions,
  accuracyStatus,
  lastError,
  onStartTracking,
  onStopTracking,
}: LocationTrackerWidgetProps) {
  const trackingDuration = useMemo(() => {
    if (!trackingSince) return null;
    const diff = Date.now() - trackingSince;
    const minutes = Math.floor(diff / 1000 / 60);
    const seconds = Math.floor((diff / 1000) % 60);
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')} นาที`;
  }, [trackingSince]);

  const latestHistory = useMemo(() => locationHistory.slice(0, 5), [locationHistory]);

  const accuracyBadge = useMemo(() => {
    if (!accuracyStatus) return null;
    const tone =
      accuracyStatus.level === 'excellent'
        ? 'bg-emerald-50 text-emerald-600 border-emerald-200'
        : accuracyStatus.level === 'good'
          ? 'bg-amber-50 text-amber-600 border-amber-200'
          : 'bg-rose-50 text-rose-600 border-rose-200';
    return (
      <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-1 text-[11px] font-medium ${tone}`}>
        <Compass className="h-3.5 w-3.5" />
        {accuracyStatus.message}
      </span>
    );
  }, [accuracyStatus]);

  if (!isSupported) {
    return (
      <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-600">
        <p className="font-semibold">อุปกรณ์ไม่รองรับบริการระบุตำแหน่ง</p>
        <p className="mt-1 text-xs text-rose-500">
          กรุณาใช้งานผ่านอุปกรณ์พกพาที่รองรับ GPS และอนุญาตสิทธิ์การเข้าถึงตำแหน่งเพื่อใช้งานฟังก์ชันนี้
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4 rounded-xl border border-gray-200 bg-white/90 p-4 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-gray-900">ติดตามตำแหน่งแบบเรียลไทม์</p>
          <p className="text-xs text-gray-500">
            ระบบจะบันทึกเส้นทางการเดินทางพร้อมเวลา เพื่อตรวจสอบการเช็กอิน/เช็กเอาต์และเส้นทางย้อนหลัง
          </p>
        </div>
        {accuracyBadge}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        {tracking ? (
          <button
            type="button"
            onClick={onStopTracking}
            className="inline-flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs font-medium text-rose-600 hover:bg-rose-100"
          >
            <PauseCircle className="h-4 w-4" /> หยุดติดตาม
          </button>
        ) : (
          <button
            type="button"
            onClick={onStartTracking}
            className="inline-flex items-center gap-2 rounded-lg border border-primary-200 bg-primary-50 px-3 py-1.5 text-xs font-medium text-primary-600 hover:bg-primary-100"
          >
            <PlayCircle className="h-4 w-4" /> เริ่มติดตามตำแหน่ง
          </button>
        )}
        {trackingDuration && (
          <span className="inline-flex items-center gap-2 rounded-full bg-gray-100 px-3 py-1 text-[11px] text-gray-600">
            <Loader2 className="h-3.5 w-3.5 animate-spin text-primary-500" />
            ติดตามมาแล้ว {trackingDuration}
          </span>
        )}
      </div>

      {currentPosition ? (
        <div className="rounded-lg border border-dashed border-primary-200 bg-primary-50/70 p-3 text-xs text-primary-700">
          <div className="flex items-start gap-2">
            <MapPin className="mt-0.5 h-4 w-4 flex-shrink-0" />
            <div>
              <p className="font-medium text-primary-800">ตำแหน่งล่าสุด</p>
              <p>
                ละติจูด {currentPosition.latitude.toFixed(6)}, ลองจิจูด {currentPosition.longitude.toFixed(6)}
              </p>
              <p className="text-[11px] text-primary-600">
                บันทึกเมื่อ {new Date(currentPosition.timestamp).toLocaleString('th-TH')}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-gray-200 bg-gray-50 p-3 text-xs text-gray-500">
          <p>ยังไม่มีข้อมูลตำแหน่งที่บันทึก</p>
        </div>
      )}

      {suggestions.length > 0 && (
        <div className="space-y-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-700">
          {suggestions.map((item) => (
            <p key={item.id} className="flex items-start gap-2">
              <Footprints className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-500" />
              <span>{item.message}</span>
            </p>
          ))}
          <p className="text-[11px] text-emerald-600">กดเช็กอินได้ทันทีเมื่อคุณอยู่ภายในพื้นที่ที่กำหนด</p>
        </div>
      )}

      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-lg border border-gray-200 bg-white/80 p-3 text-xs text-gray-600">
          <p className="flex items-center gap-2 text-sm font-semibold text-gray-800">
            <Footprints className="h-4 w-4 text-primary-500" /> ระยะทางที่บันทึกวันนี้
          </p>
          <p className="mt-1 text-lg font-bold text-gray-900">{totalDistanceKm.toFixed(2)} กม.</p>
          <p className="text-[11px] text-gray-400">รวมจากตำแหน่งล่าสุด {locationHistory.length} จุด</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white/80 p-3 text-xs text-gray-600">
          <p className="flex items-center gap-2 text-sm font-semibold text-gray-800">
            <MapPin className="h-4 w-4 text-primary-500" /> ประวัติล่าสุด
          </p>
          <div className="mt-2 space-y-2">
            {latestHistory.length === 0 && <p className="text-[11px] text-gray-400">ยังไม่มีการบันทึกตำแหน่ง</p>}
            {latestHistory.map((item) => (
              <div key={item.id} className="rounded-md border border-dashed border-gray-200 bg-gray-50 p-2">
                <p className="font-medium text-gray-700">
                  {item.label ? `${item.label} · ` : ''}ละติจูด {item.latitude.toFixed(5)}, ลองจิจูด {item.longitude.toFixed(5)}
                </p>
                <p className="text-[11px] text-gray-400">{new Date(item.timestamp).toLocaleTimeString('th-TH')}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {lastError && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-600">
          <p className="flex items-center gap-2 font-medium">
            <AlertTriangle className="h-4 w-4" /> {lastError}
          </p>
          <p className="mt-1 text-[11px] text-rose-500">
            ตรวจสอบว่าได้เปิด GPS และอนุญาตสิทธิ์ตำแหน่งให้กับเบราว์เซอร์แล้ว หรืออยู่ในพื้นที่ที่รับสัญญาณได้ดี
          </p>
        </div>
      )}
    </div>
  );
}

export default LocationTrackerWidget;
