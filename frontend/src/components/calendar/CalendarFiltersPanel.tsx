'use client';

import { useMemo } from 'react';
import { CalendarRange, Car, FilterIcon, RefreshCw, Users } from 'lucide-react';

import {
  CalendarDriverResource,
  CalendarStatus,
  CalendarVehicleResource,
} from './sampleData';

export type ResourceMode = 'vehicle' | 'driver';

export interface CalendarFiltersState {
  statuses: CalendarStatus[];
  vehicleTypes: string[];
  driverSkills: string[];
  resourceIds: string[];
  search: string;
  allowSharing?: boolean | null;
}

interface CalendarFiltersPanelProps {
  filters: CalendarFiltersState;
  onChange: (filters: CalendarFiltersState) => void;
  vehicles: CalendarVehicleResource[];
  drivers: CalendarDriverResource[];
  resourceMode: ResourceMode;
  onResourceModeChange: (mode: ResourceMode) => void;
}

const statusOptions: Array<{ value: CalendarStatus; label: string; color: string }> = [
  { value: 'planned', label: 'วางแผน', color: 'bg-slate-100 text-slate-700' },
  { value: 'pending', label: 'รออนุมัติ', color: 'bg-amber-100 text-amber-700' },
  { value: 'confirmed', label: 'ยืนยันแล้ว', color: 'bg-emerald-100 text-emerald-700' },
  { value: 'inProgress', label: 'กำลังดำเนินการ', color: 'bg-blue-100 text-blue-700' },
  { value: 'completed', label: 'เสร็จสิ้น', color: 'bg-sky-100 text-sky-700' },
  { value: 'cancelled', label: 'ยกเลิก', color: 'bg-rose-100 text-rose-700' },
];

const driverSkillOptions = Array.from(
  new Set(
    [
      'ภาษาอังกฤษ',
      'งานพิธีการ',
      'VIP Protocol',
      'ขับรถระยะไกล',
      'ความปลอดภัยขั้นสูง',
      'ภาษาจีน',
      'งานบริการลูกค้า',
      'การแพทย์ฉุกเฉิน',
      'รถพิเศษ',
      'งานราชการ',
      'ขับขบวน',
    ].sort(),
  ),
);

function toggleValue<T>(values: T[], value: T): T[] {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}

export function CalendarFiltersPanel({
  filters,
  onChange,
  vehicles,
  drivers,
  resourceMode,
  onResourceModeChange,
}: CalendarFiltersPanelProps) {
  const vehicleTypeOptions = useMemo(() => {
    return Array.from(new Set(vehicles.map((vehicle) => vehicle.type))).sort();
  }, [vehicles]);

  const resources = resourceMode === 'vehicle' ? vehicles : drivers;

  return (
    <aside className="card space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">ตัวกรองการแสดงผล</h2>
          <p className="mt-1 text-sm text-gray-600">
            เลือกเงื่อนไขเพื่อโฟกัสเฉพาะภารกิจที่ต้องการตรวจสอบหรือปรับเปลี่ยน
          </p>
        </div>
        <button
          type="button"
          onClick={() =>
            onChange({
              statuses: [],
              vehicleTypes: [],
              driverSkills: [],
              resourceIds: [],
              search: '',
              allowSharing: null,
            })
          }
          className="inline-flex items-center gap-2 rounded-md border border-gray-200 px-3 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-100"
        >
          <RefreshCw className="h-4 w-4" /> รีเซ็ต
        </button>
      </div>

      <div className="space-y-3">
        <label className="form-label" htmlFor="calendar-search">
          ค้นหากิจกรรม
        </label>
        <div className="relative">
          <input
            id="calendar-search"
            type="search"
            placeholder="ค้นหาโดยชื่อภารกิจ ผู้ขอใช้รถ หรือสถานที่"
            value={filters.search}
            onChange={(event) => onChange({ ...filters, search: event.target.value })}
            className="form-input pr-10"
          />
          <FilterIcon className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        </div>
      </div>

      <section className="space-y-3">
        <p className="text-sm font-semibold text-gray-800">มุมมองทรัพยากร</p>
        <div className="inline-flex rounded-lg border border-gray-200 bg-gray-50 p-1 text-sm">
          <button
            type="button"
            className={`inline-flex items-center gap-1 rounded-md px-3 py-1.5 font-medium transition ${
              resourceMode === 'vehicle'
                ? 'bg-white text-primary-600 shadow'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => onResourceModeChange('vehicle')}
          >
            <Car className="h-4 w-4" /> รถยนต์
          </button>
          <button
            type="button"
            className={`inline-flex items-center gap-1 rounded-md px-3 py-1.5 font-medium transition ${
              resourceMode === 'driver'
                ? 'bg-white text-primary-600 shadow'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => onResourceModeChange('driver')}
          >
            <Users className="h-4 w-4" /> พนักงานขับรถ
          </button>
        </div>
      </section>

      <section className="space-y-3">
        <p className="text-sm font-semibold text-gray-800">สถานะภารกิจ</p>
        <div className="flex flex-wrap gap-2">
          {statusOptions.map((option) => {
            const isActive = filters.statuses.includes(option.value);
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => onChange({ ...filters, statuses: toggleValue(filters.statuses, option.value) })}
                className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-sm font-medium transition ${
                  isActive
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : `border-transparent ${option.color} hover:border-gray-300`
                }`}
              >
                <span className="inline-block h-2 w-2 rounded-full bg-current" aria-hidden />
                {option.label}
              </button>
            );
          })}
        </div>
      </section>

      <section className="space-y-3">
        <p className="text-sm font-semibold text-gray-800">
          {resourceMode === 'vehicle' ? 'ประเภทรถที่ต้องการ' : 'ทักษะพนักงานขับรถ'}
        </p>
        <div className="flex flex-wrap gap-2">
          {(resourceMode === 'vehicle' ? vehicleTypeOptions : driverSkillOptions).map((value) => {
            const activeList = resourceMode === 'vehicle' ? filters.vehicleTypes : filters.driverSkills;
            const isActive = activeList.includes(value);
            return (
              <button
                key={value}
                type="button"
                onClick={() =>
                  onChange(
                    resourceMode === 'vehicle'
                      ? { ...filters, vehicleTypes: toggleValue(filters.vehicleTypes, value) }
                      : { ...filters, driverSkills: toggleValue(filters.driverSkills, value) },
                  )
                }
                className={`rounded-full border px-3 py-1 text-sm font-medium transition ${
                  isActive ? 'border-primary-500 bg-primary-50 text-primary-700' : 'border-gray-200 text-gray-600 hover:border-primary-200'
                }`}
              >
                {value}
              </button>
            );
          })}
        </div>
      </section>

      <section className="space-y-3">
        <p className="text-sm font-semibold text-gray-800">
          {resourceMode === 'vehicle' ? 'เลือกรถที่ต้องการติดตาม' : 'เลือกพนักงานขับรถที่ต้องการติดตาม'}
        </p>
        <div className="max-h-64 space-y-2 overflow-y-auto rounded-lg border border-gray-100 bg-gray-50 p-3">
          {resources.map((resource) => {
            const isChecked = filters.resourceIds.includes(resource.id);
            const description =
              resourceMode === 'vehicle'
                ? `${(resource as CalendarVehicleResource).type} · ${(resource as CalendarVehicleResource).capacity} ที่นั่ง`
                : (resource as CalendarDriverResource).skills.slice(0, 2).join(', ');
            return (
              <label
                key={resource.id}
                className={`flex cursor-pointer items-start gap-3 rounded-md border px-3 py-2 text-sm transition ${
                  isChecked ? 'border-primary-400 bg-primary-50' : 'border-transparent hover:border-gray-200 hover:bg-white'
                }`}
              >
                <input
                  type="checkbox"
                  className="mt-1 h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  checked={isChecked}
                  onChange={() =>
                    onChange({ ...filters, resourceIds: toggleValue(filters.resourceIds, resource.id) })
                  }
                />
                <div>
                  <p className="font-semibold text-gray-800">{resource.name}</p>
                  <p className="text-xs text-gray-500">{description}</p>
                </div>
              </label>
            );
          })}
        </div>
      </section>

      <section className="space-y-3">
        <p className="text-sm font-semibold text-gray-800">การแชร์การเดินทาง</p>
        <div className="flex gap-2 text-sm">
          {[{ label: 'ทั้งหมด', value: null }, { label: 'อนุญาตให้แชร์', value: true }, { label: 'ไม่แชร์', value: false }].map(
            (option) => {
              const isActive = filters.allowSharing === option.value;
              return (
                <button
                  key={option.label}
                  type="button"
                  onClick={() => onChange({ ...filters, allowSharing: option.value })}
                  className={`flex-1 rounded-md border px-3 py-1.5 font-medium transition ${
                    isActive
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-gray-200 text-gray-600 hover:border-primary-200'
                  }`}
                >
                  {option.label}
                </button>
              );
            },
          )}
        </div>
      </section>

      <section className="rounded-lg border border-dashed border-gray-200 bg-white/60 p-4">
        <div className="flex items-center gap-3">
          <CalendarRange className="h-10 w-10 rounded-full bg-primary-100 p-2 text-primary-600" />
          <div>
            <p className="text-sm font-semibold text-gray-800">เคล็ดลับการใช้งาน</p>
            <p className="text-xs text-gray-500">
              ลากและวางเหตุการณ์เพื่อเปลี่ยนเวลาหรือสลับรถได้ทันที พร้อมตรวจสอบความขัดแย้งผ่านแถบแจ้งเตือนด้านล่าง
            </p>
          </div>
        </div>
      </section>
    </aside>
  );
}
