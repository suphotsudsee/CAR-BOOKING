'use client';

import { useEffect, useMemo, useState } from 'react';
import { format } from 'date-fns';
import { AlertTriangle, Clock, MapPin, StickyNote, User } from 'lucide-react';

import {
  CalendarDriverResource,
  CalendarEvent,
  CalendarStatus,
  CalendarVehicleResource,
} from './sampleData';

interface CalendarEventDialogProps {
  open: boolean;
  event?: CalendarEvent | null;
  initialRange?: {
    start: Date;
    end: Date;
    vehicleId?: string;
    driverId?: string;
  };
  onClose: () => void;
  onSave: (event: CalendarEvent) => void;
  onDelete?: (eventId: string) => void;
  vehicles: CalendarVehicleResource[];
  drivers: CalendarDriverResource[];
}

interface EventFormState {
  id?: string;
  title: string;
  requester: string;
  department: string;
  start: string;
  end: string;
  vehicleId: string;
  driverId: string;
  status: CalendarStatus;
  location: string;
  passengers: number;
  notes: string;
  allowSharing: boolean;
}

const statusLabels: Record<CalendarStatus, string> = {
  planned: 'วางแผน',
  pending: 'รออนุมัติ',
  confirmed: 'ยืนยันแล้ว',
  inProgress: 'กำลังดำเนินการ',
  completed: 'เสร็จสิ้น',
  cancelled: 'ยกเลิก',
};

function toDateTimeLocal(value: Date) {
  return format(value, "yyyy-MM-dd'T'HH:mm");
}

const emptyFormState: EventFormState = {
  title: '',
  requester: '',
  department: '',
  start: toDateTimeLocal(new Date()),
  end: toDateTimeLocal(new Date(Date.now() + 60 * 60 * 1000)),
  vehicleId: '',
  driverId: '',
  status: 'planned',
  location: '',
  passengers: 1,
  notes: '',
  allowSharing: false,
};

function normalizeEvent(state: EventFormState): CalendarEvent {
  const start = new Date(state.start);
  const end = new Date(state.end);
  return {
    id: state.id ?? (typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `CAL-${Date.now()}`),
    title: state.title.trim() || 'ภารกิจใหม่',
    requester: state.requester.trim() || 'ไม่ระบุ',
    department: state.department.trim() || 'ไม่ระบุ',
    start,
    end,
    vehicleId: state.vehicleId,
    driverId: state.driverId,
    status: state.status,
    location: state.location.trim() || 'ไม่ระบุ',
    passengers: Number.isFinite(state.passengers) ? Math.max(1, Math.round(state.passengers)) : 1,
    notes: state.notes.trim() || undefined,
    allowSharing: state.allowSharing,
  };
}

function validateTimeRange(start: string, end: string) {
  if (!start || !end) return false;
  return new Date(start).getTime() < new Date(end).getTime();
}

export function CalendarEventDialog({
  open,
  event,
  initialRange,
  onClose,
  onSave,
  onDelete,
  vehicles,
  drivers,
}: CalendarEventDialogProps) {
  const [formState, setFormState] = useState<EventFormState>(emptyFormState);

  useEffect(() => {
    if (!open) {
      setFormState(emptyFormState);
      return;
    }

    const fallbackStart = event?.start ?? initialRange?.start ?? new Date();
    const fallbackEnd = event?.end ?? initialRange?.end ?? new Date(Date.now() + 60 * 60 * 1000);

    setFormState({
      id: event?.id,
      title: event?.title ?? '',
      requester: event?.requester ?? '',
      department: event?.department ?? '',
      start: toDateTimeLocal(fallbackStart),
      end: toDateTimeLocal(fallbackEnd),
      vehicleId: event?.vehicleId ?? initialRange?.vehicleId ?? vehicles[0]?.id ?? '',
      driverId: event?.driverId ?? initialRange?.driverId ?? drivers[0]?.id ?? '',
      status: event?.status ?? 'planned',
      location: event?.location ?? '',
      passengers: event?.passengers ?? 1,
      notes: event?.notes ?? '',
      allowSharing: Boolean(event?.allowSharing),
    });
  }, [drivers, event, initialRange, open, vehicles]);

  const isValidTime = useMemo(() => validateTimeRange(formState.start, formState.end), [formState.end, formState.start]);
  const canSave =
    isValidTime &&
    !!formState.vehicleId &&
    !!formState.driverId &&
    formState.title.trim().length > 0 &&
    formState.requester.trim().length > 0;

  const durationHours = useMemo(() => {
    if (!formState.start || !formState.end) return 0;
    const diffMs = new Date(formState.end).getTime() - new Date(formState.start).getTime();
    const hours = diffMs / (1000 * 60 * 60);
    return Math.max(0, Math.round(hours * 2) / 2);
  }, [formState.end, formState.start]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-6">
      <div className="relative w-full max-w-2xl rounded-xl bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              {event ? 'แก้ไขรายละเอียดภารกิจ' : 'สร้างภารกิจใหม่'}
            </h2>
            <p className="text-sm text-gray-500">ระบุข้อมูลการเดินทางเพื่อจัดสรรรถและพนักงานขับรถที่เหมาะสม</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-transparent p-1.5 text-gray-400 transition hover:border-gray-200 hover:text-gray-600"
            aria-label="ปิดหน้าต่าง"
          >
            ✕
          </button>
        </div>

        <div className="grid max-h-[70vh] grid-cols-1 gap-6 overflow-y-auto px-6 py-5 md:grid-cols-2">
          <div className="space-y-5">
            <div>
              <label className="form-label" htmlFor="event-title">
                ชื่อภารกิจ
              </label>
              <input
                id="event-title"
                type="text"
                value={formState.title}
                onChange={(event) => setFormState((prev) => ({ ...prev, title: event.target.value }))}
                className="form-input"
                placeholder="เช่น รับผู้บริหารจากสนามบิน"
                autoFocus
              />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="form-label" htmlFor="event-requester">
                  ผู้ร้องขอ
                </label>
                <div className="relative">
                  <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                  <input
                    id="event-requester"
                    type="text"
                    value={formState.requester}
                    onChange={(event) => setFormState((prev) => ({ ...prev, requester: event.target.value }))}
                    className="form-input pl-9"
                    placeholder="ชื่อผู้ติดต่อ"
                  />
                </div>
              </div>
              <div>
                <label className="form-label" htmlFor="event-department">
                  หน่วยงาน
                </label>
                <input
                  id="event-department"
                  type="text"
                  value={formState.department}
                  onChange={(event) => setFormState((prev) => ({ ...prev, department: event.target.value }))}
                  className="form-input"
                  placeholder="ระบุฝ่ายหรือแผนก"
                />
              </div>
            </div>

            <div className="space-y-3">
              <label className="form-label">ช่วงเวลาการเดินทาง</label>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="relative">
                  <Clock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                  <input
                    type="datetime-local"
                    value={formState.start}
                    onChange={(event) => setFormState((prev) => ({ ...prev, start: event.target.value }))}
                    className="form-input pl-9"
                  />
                </div>
                <div className="relative">
                  <Clock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                  <input
                    type="datetime-local"
                    value={formState.end}
                    onChange={(event) => setFormState((prev) => ({ ...prev, end: event.target.value }))}
                    className="form-input pl-9"
                    min={formState.start}
                  />
                </div>
              </div>
              {!isValidTime && (
                <p className="text-sm text-rose-600">กรุณาตรวจสอบว่าเวลาสิ้นสุดอยู่หลังเวลาเริ่มต้น</p>
              )}
              {durationHours > 0 && (
                <p className="text-xs text-gray-500">ระยะเวลารวมประมาณ {durationHours.toFixed(1)} ชั่วโมง</p>
              )}
            </div>
          </div>

          <div className="space-y-5">
            <div>
              <label className="form-label" htmlFor="event-vehicle">
                รถที่ใช้ในการเดินทาง
              </label>
              <select
                id="event-vehicle"
                className="form-input"
                value={formState.vehicleId}
                onChange={(event) => setFormState((prev) => ({ ...prev, vehicleId: event.target.value }))}
              >
                <option value="" disabled>
                  เลือกรถจากรายการ
                </option>
                {vehicles.map((vehicle) => (
                  <option key={vehicle.id} value={vehicle.id}>
                    {vehicle.name} · {vehicle.type} · {vehicle.capacity} ที่นั่ง
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="form-label" htmlFor="event-driver">
                พนักงานขับรถ
              </label>
              <select
                id="event-driver"
                className="form-input"
                value={formState.driverId}
                onChange={(event) => setFormState((prev) => ({ ...prev, driverId: event.target.value }))}
              >
                <option value="" disabled>
                  เลือกพนักงานขับรถ
                </option>
                {drivers.map((driver) => (
                  <option key={driver.id} value={driver.id}>
                    {driver.name} · {driver.skills.slice(0, 2).join(', ')}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="form-label" htmlFor="event-status">
                  สถานะภารกิจ
                </label>
                <select
                  id="event-status"
                  value={formState.status}
                  onChange={(event) => setFormState((prev) => ({ ...prev, status: event.target.value as CalendarStatus }))}
                  className="form-input"
                >
                  {Object.entries(statusLabels).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="form-label" htmlFor="event-passengers">
                  จำนวนผู้โดยสาร
                </label>
                <input
                  id="event-passengers"
                  type="number"
                  min={1}
                  value={formState.passengers}
                  onChange={(event) =>
                    setFormState((prev) => ({ ...prev, passengers: Number(event.target.value) || prev.passengers }))
                  }
                  className="form-input"
                />
              </div>
            </div>

            <div>
              <label className="form-label" htmlFor="event-location">
                จุดรับ/ส่งหลัก
              </label>
              <div className="relative">
                <MapPin className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                <input
                  id="event-location"
                  type="text"
                  value={formState.location}
                  onChange={(event) => setFormState((prev) => ({ ...prev, location: event.target.value }))}
                  className="form-input pl-9"
                  placeholder="ตัวอย่าง: ท่าอากาศยานสุวรรณภูมิ"
                />
              </div>
            </div>

            <div>
              <label className="form-label" htmlFor="event-notes">
                บันทึกเพิ่มเติม
              </label>
              <div className="relative">
                <StickyNote className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                <textarea
                  id="event-notes"
                  value={formState.notes}
                  onChange={(event) => setFormState((prev) => ({ ...prev, notes: event.target.value }))}
                  className="form-input min-h-[96px] pl-10"
                  placeholder="ระบุข้อควรระวังหรืออุปกรณ์พิเศษที่ต้องเตรียม"
                />
              </div>
            </div>

            <label className="flex items-start gap-3 rounded-lg border border-gray-200 bg-gray-50 p-4">
              <input
                type="checkbox"
                className="mt-1 h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                checked={formState.allowSharing}
                onChange={(event) => setFormState((prev) => ({ ...prev, allowSharing: event.target.checked }))}
              />
              <div>
                <p className="text-sm font-semibold text-gray-800">อนุญาตให้แชร์ที่นั่ง</p>
                <p className="text-xs text-gray-500">
                  หากเลือก ระบบจะแนะนำการรวมภารกิจที่มีเส้นทางใกล้เคียงเพื่อลดจำนวนเที่ยวรถ
                </p>
              </div>
            </label>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-gray-100 bg-gray-50 px-6 py-4">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <AlertTriangle className="h-4 w-4 text-amber-500" />
            ระบบจะตรวจสอบความขัดแย้งของรถและพนักงานขับรถโดยอัตโนมัติ
          </div>
          <div className="flex flex-wrap items-center gap-3">
            {event && onDelete && (
              <button
                type="button"
                onClick={() => onDelete(event.id)}
                className="inline-flex items-center gap-2 rounded-md border border-rose-200 px-4 py-2 text-sm font-medium text-rose-600 transition hover:bg-rose-50"
              >
                ลบภารกิจนี้
              </button>
            )}
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-gray-200 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100"
            >
              ยกเลิก
            </button>
            <button
              type="button"
              onClick={() => {
                const normalized = normalizeEvent(formState);
                onSave(normalized);
              }}
              disabled={!canSave}
              className="rounded-md bg-primary-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary-700 disabled:cursor-not-allowed disabled:bg-primary-300"
            >
              {event ? 'บันทึกการเปลี่ยนแปลง' : 'สร้างภารกิจ'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
