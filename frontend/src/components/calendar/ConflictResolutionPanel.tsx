'use client';

import { CalendarCheck2, Car, Clock, Lightbulb, ShieldAlert, User } from 'lucide-react';

import {
  CalendarDriverResource,
  CalendarEvent,
  CalendarVehicleResource,
} from './sampleData';

export interface ConflictSuggestion extends Partial<CalendarEvent> {
  id: string;
  label: string;
  description: string;
}

export interface ConflictContext {
  pendingEvent: CalendarEvent;
  conflicts: CalendarEvent[];
  suggestions: ConflictSuggestion[];
}

interface ConflictResolutionPanelProps {
  context: ConflictContext | null;
  onApply: (event: CalendarEvent) => void;
  onKeep: (event: CalendarEvent) => void;
  onDismiss: () => void;
  vehicles: CalendarVehicleResource[];
  drivers: CalendarDriverResource[];
}

const rangeStartFormatter = new Intl.DateTimeFormat('th-TH', {
  day: '2-digit',
  month: 'short',
  hour: '2-digit',
  minute: '2-digit',
});

const rangeEndFormatter = new Intl.DateTimeFormat('th-TH', {
  hour: '2-digit',
  minute: '2-digit',
});

function formatDateTimeRange(start: Date, end: Date) {
  return `${rangeStartFormatter.format(start)} – ${rangeEndFormatter.format(end)}`;
}

export function ConflictResolutionPanel({
  context,
  onApply,
  onKeep,
  onDismiss,
  vehicles,
  drivers,
}: ConflictResolutionPanelProps) {
  if (!context) return null;

  const { pendingEvent, conflicts, suggestions } = context;

  const resolveVehicleName = (vehicleId: string) => vehicles.find((vehicle) => vehicle.id === vehicleId)?.name ?? vehicleId;
  const resolveDriverName = (driverId: string) => drivers.find((driver) => driver.id === driverId)?.name ?? driverId;

  return (
    <section className="rounded-xl border border-amber-200 bg-amber-50/80 p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-amber-900">พบความขัดแย้งของตารางงาน</h3>
          <p className="text-sm text-amber-800">
            ระบบตรวจพบว่ารถหรือพนักงานขับรถที่เลือกมีภารกิจอื่นซ้อนกัน กรุณาเลือกวิธีแก้ไขจากตัวเลือกด้านล่าง
          </p>
        </div>
        <button
          type="button"
          onClick={onDismiss}
          className="rounded-full border border-transparent p-1.5 text-amber-600 transition hover:border-amber-300 hover:bg-amber-100"
          aria-label="ปิดคำแนะนำ"
        >
          ✕
        </button>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div className="space-y-3 rounded-lg border border-amber-200 bg-white/80 p-4">
          <div className="flex items-center gap-3">
            <ShieldAlert className="h-10 w-10 rounded-full bg-amber-100 p-2 text-amber-600" />
            <div>
              <p className="text-sm font-semibold text-amber-900">รายละเอียดภารกิจที่กำลังบันทึก</p>
              <p className="text-xs text-amber-700">
                {pendingEvent.title} · {formatDateTimeRange(pendingEvent.start, pendingEvent.end)}
              </p>
            </div>
          </div>
          <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
            <div className="rounded-md bg-amber-100/80 p-3">
              <dt className="flex items-center gap-2 text-amber-900">
                <Car className="h-4 w-4" /> รถที่ใช้
              </dt>
              <dd className="mt-1 font-medium text-amber-800">{resolveVehicleName(pendingEvent.vehicleId)}</dd>
            </div>
            <div className="rounded-md bg-amber-100/80 p-3">
              <dt className="flex items-center gap-2 text-amber-900">
                <User className="h-4 w-4" /> พนักงานขับรถ
              </dt>
              <dd className="mt-1 font-medium text-amber-800">{resolveDriverName(pendingEvent.driverId)}</dd>
            </div>
          </dl>
        </div>

        <div className="space-y-3 rounded-lg border border-amber-200 bg-white/80 p-4">
          <div className="flex items-center gap-3">
            <Clock className="h-10 w-10 rounded-full bg-amber-100 p-2 text-amber-600" />
            <div>
              <p className="text-sm font-semibold text-amber-900">ตารางที่ซ้อนกัน</p>
              <p className="text-xs text-amber-700">ตรวจสอบรายการที่ชนกันเพื่อพิจารณาปรับเวลา</p>
            </div>
          </div>
          <ul className="space-y-2 text-sm text-amber-900">
            {conflicts.map((conflict) => (
              <li key={conflict.id} className="rounded-md border border-amber-200/70 bg-white/70 p-3">
                <p className="font-medium">{conflict.title}</p>
                <p className="text-xs text-amber-700">
                  {formatDateTimeRange(conflict.start, conflict.end)} · รถ {resolveVehicleName(conflict.vehicleId)} · คนขับ {resolveDriverName(conflict.driverId)}
                </p>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-6 space-y-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-amber-900">
          <Lightbulb className="h-4 w-4 text-amber-600" /> ทางเลือกที่ระบบแนะนำ
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {suggestions.length === 0 && (
            <p className="rounded-md border border-amber-200 bg-white/70 p-3 text-sm text-amber-800">
              ไม่พบทางเลือกที่เหมาะสมทันที กรุณาปรับเวลาเองหรือเลือกใช้รถสำรอง
            </p>
          )}
          {suggestions.map((suggestion) => {
            const preview = {
              ...pendingEvent,
              ...suggestion,
              start: suggestion.start ?? pendingEvent.start,
              end: suggestion.end ?? pendingEvent.end,
              vehicleId: suggestion.vehicleId ?? pendingEvent.vehicleId,
              driverId: suggestion.driverId ?? pendingEvent.driverId,
            };
            return (
              <button
                key={suggestion.id}
                type="button"
                onClick={() => onApply(preview)}
                className="h-full rounded-lg border border-amber-200 bg-white/80 p-4 text-left text-sm text-amber-900 transition hover:border-amber-300 hover:bg-white"
              >
                <p className="font-semibold">{suggestion.label}</p>
                <p className="mt-1 text-xs text-amber-700">{suggestion.description}</p>
                <p className="mt-2 text-xs text-amber-600">
                  {formatDateTimeRange(preview.start, preview.end)} · รถ {resolveVehicleName(preview.vehicleId)} · คนขับ {resolveDriverName(preview.driverId)}
                </p>
              </button>
            );
          })}
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-lg bg-white/70 p-4">
        <div className="flex items-center gap-2 text-xs text-amber-700">
          <CalendarCheck2 className="h-4 w-4 text-amber-600" />
          สามารถกด &quot;คงค่าเดิม&quot; หากต้องการบันทึกภารกิจนี้ไว้ตรวจสอบภายหลัง
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={() => onKeep(pendingEvent)}
            className="rounded-md border border-amber-200 px-4 py-2 text-sm font-medium text-amber-700 transition hover:bg-amber-100"
          >
            คงค่าเดิม (ยังไม่แก้ไข)
          </button>
          <button
            type="button"
            onClick={onDismiss}
            className="rounded-md border border-transparent bg-amber-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-amber-700"
          >
            ปิดคำแนะนำ
          </button>
        </div>
      </div>
    </section>
  );
}
