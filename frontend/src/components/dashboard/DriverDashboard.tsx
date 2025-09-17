"use client";

import Image from 'next/image';
import { useCallback, useMemo, useState } from 'react';

import {
  CalendarCheck,
  CarFront,
  CheckCircle,
  Clock4,
  LogIn,
  LogOut,
  MapPinned,
  Route,
  Trash2,
  UserCheck,
} from 'lucide-react';

import { LocationTrackerWidget, MobileCameraCapture, type CapturedImage } from '@/components/mobile';
import { AuthUser } from '@/context/AuthContext';
import { useLocationTracking, type LocationPoint } from '@/hooks/useLocationTracking';

import { CardGrid, EmptyState, QuickActionButton, SectionCard, StatCard, TimelineItem } from './shared';

interface DriverDashboardProps {
  user: AuthUser;
}

interface JobAssignmentItem {
  id: string;
  destination: string;
  schedule: string;
  requester: string;
  status: string;
}

type CameraLocation = NonNullable<CapturedImage['location']>;
type LocationLike = LocationPoint | CameraLocation;

interface CheckEvent {
  id: string;
  type: 'check-in' | 'check-out';
  timestamp: number;
  location?: LocationPoint;
}

interface SavedPhoto extends CapturedImage {
  id: string;
  capturedAt: number;
}

export function DriverDashboard({ user }: DriverDashboardProps) {
  const [checkedIn, setCheckedIn] = useState(false);
  const [checkEvents, setCheckEvents] = useState<CheckEvent[]>([]);
  const [checkProcessing, setCheckProcessing] = useState(false);
  const [checkError, setCheckError] = useState<string | null>(null);
  const [vehiclePhotos, setVehiclePhotos] = useState<SavedPhoto[]>([]);

  const {
    isSupported: locationSupported,
    tracking,
    trackingSince,
    currentPosition,
    locationHistory,
    totalDistanceKm,
    suggestions,
    accuracyStatus,
    lastError: locationError,
    startTracking,
    stopTracking,
    captureSnapshot,
  } = useLocationTracking({ historyLimit: 60, accuracyThreshold: 70 });

  const jobAssignments = useMemo<JobAssignmentItem[]>(
    () => [
      {
        id: 'JOB-2024-117',
        destination: 'สำนักงานใหญ่บางนา',
        schedule: '12 ก.พ. 2567 · 08:00 - 11:30 น.',
        requester: 'สุกัญญา ชาญชัย',
        status: 'Scheduled',
      },
      {
        id: 'JOB-2024-118',
        destination: 'โรงงานผลิต จ.ระยอง',
        schedule: '12 ก.พ. 2567 · 13:30 - 18:00 น.',
        requester: 'ธีรเดช พงษ์ไพบูลย์',
        status: 'Scheduled',
      },
      {
        id: 'JOB-2024-110',
        destination: 'สนามบินสุวรรณภูมิ',
        schedule: '11 ก.พ. 2567 · 05:30 - 09:00 น.',
        requester: 'ณัฐพงศ์ เกตุแก้ว',
        status: 'Completed',
      },
    ],
    [],
  );

  const handleCheckIn = useCallback(async () => {
    if (checkProcessing) return;
    setCheckProcessing(true);
    setCheckError(null);

    try {
      const snapshot = await captureSnapshot('เช็กอิน');
      if (!snapshot) {
        setCheckError('ไม่สามารถบันทึกตำแหน่งขณะเช็กอิน กรุณาตรวจสอบสัญญาณ GPS');
      }

      if (!tracking) {
        await startTracking();
      }

      setCheckEvents((previous) => {
        const next: CheckEvent = {
          id: `check-in-${Date.now()}`,
          type: 'check-in',
          timestamp: Date.now(),
          location: snapshot ?? undefined,
        };
        return [next, ...previous].slice(0, 6);
      });

      setCheckedIn(true);
    } finally {
      setCheckProcessing(false);
    }
  }, [captureSnapshot, checkProcessing, startTracking, tracking]);

  const handleCheckOut = useCallback(async () => {
    if (checkProcessing) return;
    setCheckProcessing(true);
    setCheckError(null);

    try {
      const snapshot = await captureSnapshot('เช็กเอาต์');
      if (!snapshot) {
        setCheckError('ไม่สามารถบันทึกตำแหน่งขณะเช็กเอาต์ กรุณาตรวจสอบสัญญาณ GPS');
      }

      if (tracking) {
        stopTracking();
      }

      setCheckEvents((previous) => {
        const next: CheckEvent = {
          id: `check-out-${Date.now()}`,
          type: 'check-out',
          timestamp: Date.now(),
          location: snapshot ?? undefined,
        };
        return [next, ...previous].slice(0, 6);
      });

      setCheckedIn(false);
    } finally {
      setCheckProcessing(false);
    }
  }, [captureSnapshot, checkProcessing, stopTracking, tracking]);

  const handlePhotoCaptured = useCallback((image: CapturedImage) => {
    setVehiclePhotos((previous) => [{ ...image, id: `photo-${Date.now()}`, capturedAt: Date.now() }, ...previous].slice(0, 6));
  }, []);

  const handleRemovePhoto = useCallback((id: string) => {
    setVehiclePhotos((previous) => previous.filter((item) => item.id !== id));
  }, []);

  const latestCheckIn = useMemo(() => checkEvents.find((event) => event.type === 'check-in'), [checkEvents]);
  const latestCheckOut = useMemo(() => checkEvents.find((event) => event.type === 'check-out'), [checkEvents]);

  const formatLocation = useCallback((location?: LocationLike | null) => {
    if (!location) return 'ไม่พบข้อมูลตำแหน่ง';
    const accuracyText =
      typeof location.accuracy === 'number' ? `±${Math.round(location.accuracy)} ม.` : 'ความแม่นยำไม่ทราบ';
    return `ละติจูด ${location.latitude.toFixed(5)}, ลองจิจูด ${location.longitude.toFixed(5)} (${accuracyText})`;
  }, []);

  return (
    <div className="space-y-6">
      <CardGrid>
        <StatCard
          label="งานวันนี้"
          value="2 งาน"
          icon={CarFront}
          accent="primary"
          trend={{ value: '+1', description: 'งานเพิ่มเติม', direction: 'up' }}
        />
        <StatCard
          label="งานที่เสร็จสิ้น"
          value="18 งาน"
          icon={CheckCircle}
          accent="emerald"
          trend={{ value: '95%', description: 'ตรงเวลา', direction: 'steady' }}
        />
        <StatCard
          label="เวลาว่าง"
          value="4 ชม."
          icon={Clock4}
          accent="sky"
          trend={{ value: '-1 ชม.', description: 'จากแผน', direction: 'down' }}
        />
        <StatCard
          label="ระยะทางเดือนนี้"
          value="1,240 กม."
          icon={Route}
          accent="violet"
          trend={{ value: '+8%', description: 'เทียบกับเดือนก่อน', direction: 'up' }}
        />
      </CardGrid>

      <SectionCard
        title="สถานะการปฏิบัติงาน"
        description={`บันทึกการเช็กอิน/เช็กเอาต์ของ ${user.fullName}`}
        actions={
          checkedIn ? (
            <button
              type="button"
              onClick={() => {
                void handleCheckOut();
              }}
              disabled={checkProcessing}
              className="inline-flex items-center gap-2 rounded-lg border border-rose-200 px-4 py-2 text-sm font-medium text-rose-600 hover:bg-rose-50 disabled:cursor-not-allowed disabled:border-gray-200 disabled:text-gray-400"
            >
              <LogOut className="h-4 w-4" />
              เช็กเอาต์
            </button>
          ) : (
            <button
              type="button"
              onClick={() => {
                void handleCheckIn();
              }}
              disabled={checkProcessing}
              className="inline-flex items-center gap-2 rounded-lg border border-emerald-200 px-4 py-2 text-sm font-medium text-emerald-600 hover:bg-emerald-50 disabled:cursor-not-allowed disabled:border-gray-200 disabled:text-gray-400"
            >
              <LogIn className="h-4 w-4" />
              เช็กอิน
            </button>
          )
        }
      >
        <div className="space-y-4 rounded-xl border border-dashed border-gray-300 bg-white/70 p-6 text-sm text-gray-600">
          <div>
            <p>
              สถานะปัจจุบัน{' '}
              <span className={checkedIn ? 'font-semibold text-emerald-600' : 'font-semibold text-gray-500'}>
                {checkedIn ? 'กำลังปฏิบัติงาน' : 'ยังไม่เริ่มงาน'}
              </span>
            </p>
            <p className="mt-2 text-xs text-gray-500">
              ระบบจะบันทึกเวลา ตำแหน่ง และความแม่นยำของสัญญาณทุกครั้งที่มีการเช็กอิน/เช็กเอาต์ เพื่อให้ผู้จัดการติดตามสถานะได้แบบเรียลไทม์
            </p>
          </div>

          {accuracyStatus && (
            <p
              className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ${
                accuracyStatus.level === 'excellent'
                  ? 'bg-emerald-50 text-emerald-600'
                  : accuracyStatus.level === 'good'
                    ? 'bg-amber-50 text-amber-600'
                    : 'bg-rose-50 text-rose-600'
              }`}
            >
              <MapPinned className="h-3.5 w-3.5" /> {accuracyStatus.message}
            </p>
          )}

          {suggestions.length > 0 && (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-700">
              <p className="flex items-start gap-2">
                <Route className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-500" />
                <span>{suggestions[0].message}</span>
              </p>
            </div>
          )}

          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-lg border border-gray-200 bg-white/80 p-3 text-xs text-gray-600">
              <p className="text-sm font-semibold text-gray-800">เช็กอินล่าสุด</p>
              {latestCheckIn ? (
                <>
                  <p className="mt-1 font-medium text-gray-700">{formatLocation(latestCheckIn.location)}</p>
                  <p className="text-[11px] text-gray-400">
                    เมื่อ {new Date(latestCheckIn.timestamp).toLocaleString('th-TH')}
                  </p>
                </>
              ) : (
                <p className="mt-1 text-[11px] text-gray-400">ยังไม่เคยเช็กอินในวันนี้</p>
              )}
            </div>
            <div className="rounded-lg border border-gray-200 bg-white/80 p-3 text-xs text-gray-600">
              <p className="text-sm font-semibold text-gray-800">เช็กเอาต์ล่าสุด</p>
              {latestCheckOut ? (
                <>
                  <p className="mt-1 font-medium text-gray-700">{formatLocation(latestCheckOut.location)}</p>
                  <p className="text-[11px] text-gray-400">
                    เมื่อ {new Date(latestCheckOut.timestamp).toLocaleString('th-TH')}
                  </p>
                </>
              ) : (
                <p className="mt-1 text-[11px] text-gray-400">ยังไม่เคยเช็กเอาต์ในวันนี้</p>
              )}
            </div>
          </div>

          {checkError && (
            <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-600">{checkError}</p>
          )}
          {locationError && (
            <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-600">{locationError}</p>
          )}
          {!locationSupported && (
            <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-600">
              อุปกรณ์นี้ไม่รองรับการระบุตำแหน่งแบบเรียลไทม์ ระบบจะบันทึกเวลาเท่านั้นเมื่อเช็กอิน/เช็กเอาต์
            </p>
          )}
        </div>
      </SectionCard>

      <SectionCard
        title="บันทึกภาพสภาพรถ"
        description="ถ่ายภาพสภาพรถพร้อมพิกัด GPS เพื่อใช้เป็นหลักฐานการส่งมอบ"
      >
        <MobileCameraCapture onCapture={handlePhotoCaptured} />
        {vehiclePhotos.length > 0 && (
          <div className="mt-4 space-y-3 rounded-xl border border-gray-200 bg-white/80 p-4 text-xs text-gray-600">
            <p className="text-sm font-semibold text-gray-800">ภาพที่บันทึกแล้ว ({vehiclePhotos.length})</p>
            <div className="grid gap-3 md:grid-cols-2">
              {vehiclePhotos.map((photo) => (
                <div key={photo.id} className="overflow-hidden rounded-lg border border-gray-200 bg-gray-50">
                  <Image
                    src={photo.dataUrl}
                    alt="ภาพสภาพรถ"
                    width={1280}
                    height={720}
                    className="h-40 w-full object-cover"
                    unoptimized
                  />
                  <div className="space-y-2 p-3">
                    <p className="font-medium text-gray-700">{formatLocation(photo.location)}</p>
                    <p className="text-[11px] text-gray-400">
                      บันทึกเมื่อ {new Date(photo.capturedAt).toLocaleString('th-TH')} · ขนาด {photo.fileSizeKb} KB
                    </p>
                    <button
                      type="button"
                      onClick={() => handleRemovePhoto(photo.id)}
                      className="inline-flex items-center gap-2 rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-100"
                    >
                      <Trash2 className="h-3.5 w-3.5" /> ลบภาพ
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </SectionCard>

      <SectionCard
        title="งานที่ได้รับมอบหมาย"
        description="เช็กเส้นทางและผู้โดยสารก่อนออกเดินทาง"
      >
        {jobAssignments.length === 0 ? (
          <EmptyState
            icon={CalendarCheck}
            title="ยังไม่มีงานในวันนี้"
            description="เมื่อมีงานมอบหมายใหม่ ระบบจะแจ้งเตือนให้ทราบทันที"
          />
        ) : (
          <div className="space-y-4">
            {jobAssignments.map((item, index) => (
              <TimelineItem
                key={item.id}
                title={`${item.destination} · ${item.requester}`}
                description={item.id}
                timestamp={item.schedule}
                status={item.status}
                accent={index % 2 === 0 ? 'sky' : 'violet'}
              />
            ))}
          </div>
        )}
      </SectionCard>

      <SectionCard title="ตัวช่วยสำหรับคนขับ" description="รวมลิงก์ที่ใช้บ่อยสำหรับการปฏิบัติงานประจำวัน">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <QuickActionButton
            label="เริ่มนำทาง"
            description="เปิดแผนที่พร้อมเส้นทางที่ได้รับ"
            icon={MapPinned}
            href="/driver/navigation"
          />
          <QuickActionButton
            label="เช็กลิสต์ก่อนออกเดินทาง"
            description="ตรวจสอบรถและอุปกรณ์ก่อนใช้งาน"
            icon={UserCheck}
            href="/driver/checklist"
            tone="emerald"
          />
          <QuickActionButton
            label="รายงานเหตุการณ์"
            description="แจ้งเหตุขัดข้องหรืออุบัติเหตุ"
            icon={Route}
            href="/driver/incidents"
            tone="amber"
          />
          <QuickActionButton
            label="สรุปการปฏิบัติงาน"
            description="กรอกข้อมูลหลังเสร็จงาน"
            icon={CalendarCheck}
            href="/driver/daily-report"
            tone="primary"
          />
        </div>
      </SectionCard>

      <SectionCard
        title="บริการระบุตำแหน่งสำหรับเช็กอิน"
        description="ติดตามเส้นทางและตรวจสอบความแม่นยำของสัญญาณ GPS แบบเรียลไทม์"
      >
        <LocationTrackerWidget
          isSupported={locationSupported}
          tracking={tracking}
          trackingSince={trackingSince}
          currentPosition={currentPosition}
          totalDistanceKm={totalDistanceKm}
          locationHistory={locationHistory}
          suggestions={suggestions}
          accuracyStatus={accuracyStatus}
          lastError={locationError}
          onStartTracking={() => {
            void startTracking();
          }}
          onStopTracking={stopTracking}
        />
      </SectionCard>
    </div>
  );
}
