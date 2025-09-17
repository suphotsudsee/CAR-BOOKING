"use client";

import { useMemo, useState } from 'react';

import { zodResolver } from '@hookform/resolvers/zod';
import { addMinutes, format, isAfter, isBefore, isEqual, parseISO } from 'date-fns';
import { CalendarClock, CheckCircle2, ChevronLeft, ChevronRight, Info, MapPin, Users } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import {
  existingScheduleConflicts,
  popularLocations,
  vehicleOptions,
  type VehicleOption,
} from './sampleData';

const bookingSchema = z
  .object({
    requesterName: z.string().min(1, 'กรุณาระบุชื่อผู้ขอใช้รถ'),
    department: z.string().min(1, 'กรุณาระบุฝ่าย/แผนก'),
    contactEmail: z.string().email('รูปแบบอีเมลไม่ถูกต้อง'),
    contactPhone: z.string().min(9, 'กรุณาระบุหมายเลขโทรศัพท์ติดต่อ'),
    passengers: z.number().min(1, 'ต้องมีผู้โดยสารอย่างน้อย 1 คน').max(50, 'ผู้โดยสารไม่เกิน 50 คน'),
    purpose: z.string().min(10, 'กรุณาอธิบายวัตถุประสงค์อย่างน้อย 10 ตัวอักษร'),
    start: z.string().min(1, 'กรุณาเลือกเวลาออกเดินทาง'),
    end: z.string().min(1, 'กรุณาเลือกเวลาสิ้นสุดการเดินทาง'),
    origin: z.string().min(1, 'กรุณาระบุสถานที่รับ'),
    destination: z.string().min(1, 'กรุณาระบุสถานที่ส่ง'),
    originNotes: z.string().optional(),
    destinationNotes: z.string().optional(),
    preferredVehicleType: z.string().min(1, 'เลือกประเภทรถที่ต้องการ'),
    preferredVehicleId: z.string().optional(),
    additionalEquipment: z.array(z.string()).optional(),
    requireDriverSupport: z.boolean().default(true),
    allowSharing: z.boolean().default(false),
    termsAccepted: z.boolean().default(false),
  })
  .refine((data) => isBefore(new Date(data.start), new Date(data.end)), {
    message: 'เวลาออกเดินทางต้องอยู่ก่อนเวลาสิ้นสุด',
    path: ['end'],
  })
  .refine((data) => data.termsAccepted, {
    message: 'กรุณายอมรับเงื่อนไขการใช้บริการ',
    path: ['termsAccepted'],
  });

type BookingFormValues = z.infer<typeof bookingSchema>;

const stepFields: Array<(keyof BookingFormValues)[]> = [
  ['requesterName', 'department', 'contactEmail', 'contactPhone', 'passengers', 'purpose'],
  ['start', 'end'],
  ['origin', 'destination'],
  ['preferredVehicleType', 'preferredVehicleId'],
  [],
];

function findConflicts(start: string, end: string) {
  if (!start || !end) return [] as typeof existingScheduleConflicts;
  const startDate = new Date(start);
  const endDate = new Date(end);
  return existingScheduleConflicts.filter((item) => {
    const itemStart = new Date(item.start);
    const itemEnd = new Date(item.end);
    const overlaps =
      isBefore(startDate, itemEnd) &&
      isAfter(endDate, itemStart) &&
      !(isEqual(endDate, itemStart) || isEqual(startDate, itemEnd));
    return overlaps;
  });
}

function vehicleAvailability(vehicle: VehicleOption, start: string, end: string) {
  const conflicts = findConflicts(start, end).filter((conflict) => conflict.vehicleId === vehicle.id);
  if (vehicle.status === 'maintenance') {
    return { status: 'maintenance', message: 'อยู่ระหว่างบำรุงรักษา' } as const;
  }
  if (vehicle.status === 'assigned') {
    return { status: 'assigned', message: 'มอบหมายภารกิจอื่นอยู่' } as const;
  }
  if (conflicts.length > 0) {
    return { status: 'conflict', message: 'มีคิวใช้งานซ้อนกับเวลาที่เลือก' } as const;
  }
  return { status: 'available', message: 'พร้อมให้บริการในช่วงเวลานี้' } as const;
}

const vehicleTypeOptions = [
  { value: 'Sedan', label: 'รถยนต์ 4 ที่นั่ง (Sedan)' },
  { value: 'SUV', label: 'รถเอนกประสงค์ (SUV)' },
  { value: 'Van', label: 'รถตู้โดยสาร (Van)' },
  { value: 'Pickup', label: 'รถกระบะ (Pickup)' },
  { value: 'Electric', label: 'รถพลังงานไฟฟ้า (EV)' },
];

const equipmentOptions = [
  'Car Seat',
  'Child Booster',
  'Portable Wi-Fi',
  'Mobile Printer',
  'Wheelchair Lift',
  'Refrigerated Compartment',
];

export function NewBookingForm() {
  const [currentStep, setCurrentStep] = useState(0);
  const [submitted, setSubmitted] = useState(false);
  const form = useForm<BookingFormValues>({
    resolver: zodResolver(bookingSchema),
    mode: 'onBlur',
    defaultValues: {
      requesterName: 'ศศิประภา จันทร์ทอง',
      department: 'ฝ่ายขาย',
      contactEmail: 'sasi.parn@example.com',
      contactPhone: '0891234567',
      passengers: 3,
      purpose: '',
      start: format(addMinutes(new Date(), 120), "yyyy-MM-dd'T'HH:00"),
      end: format(addMinutes(new Date(), 300), "yyyy-MM-dd'T'HH:00"),
      origin: '',
      destination: '',
      preferredVehicleType: 'Sedan',
      requireDriverSupport: true,
      allowSharing: false,
      additionalEquipment: [],
      termsAccepted: false,
    },
  });

  const values = form.watch();
  const conflicts = useMemo(() => findConflicts(values.start, values.end), [values.start, values.end]);

  const locationPreview = useMemo(() => {
    const resolveLocation = (name: string) => popularLocations.find((location) => location.name === name);
    const origin = resolveLocation(values.origin);
    const destination = resolveLocation(values.destination);
    return { origin, destination };
  }, [values.destination, values.origin]);

  const availableVehicles = useMemo(() => {
    return vehicleOptions.filter((vehicle) => {
      if (!values.start || !values.end) return true;
      const availability = vehicleAvailability(vehicle, values.start, values.end);
      return availability.status === 'available';
    });
  }, [values.end, values.start]);

  const startDate = values.start ? new Date(values.start) : null;
  const endDate = values.end ? new Date(values.end) : null;

  const handleNext = async () => {
    const fields = stepFields[currentStep];
    if (fields.length > 0) {
      const valid = await form.trigger(fields);
      if (!valid) return;
    }
    setCurrentStep((prev) => Math.min(prev + 1, stepFields.length - 1));
  };

  const handlePrevious = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 0));
  };

  const onSubmit = (data: BookingFormValues) => {
    setSubmitted(true);
    console.log('booking', data);
  };

  return (
    <div className="rounded-3xl border border-primary-100/70 bg-white/90 shadow-2xl shadow-primary-100/40">
      <div className="flex flex-col gap-12 p-6 sm:p-10">
        <header className="space-y-2">
          <p className="text-sm font-semibold uppercase tracking-wide text-primary-500">สร้างคำขอการจองรถ</p>
          <h1 className="text-3xl font-bold text-gray-900">ขั้นตอนการจองแบบละเอียด</h1>
          <p className="text-sm text-gray-500">
            กรอกรายละเอียดการเดินทางอย่างครบถ้วน ระบบจะแนะนำยานพาหนะและตรวจสอบตารางงานที่ซ้ำซ้อนโดยอัตโนมัติ
          </p>
        </header>

        <nav className="grid gap-4 sm:grid-cols-5">
          {['รายละเอียดผู้ขอ', 'กำหนดการเดินทาง', 'สถานที่รับ-ส่ง', 'ยานพาหนะที่ต้องการ', 'ตรวจสอบและยืนยัน'].map(
            (label, index) => {
              const stepActive = index === currentStep;
              const completed = index < currentStep;
              return (
                <div
                  key={label}
                  className={`flex flex-col rounded-2xl border p-4 transition-all ${
                    stepActive
                      ? 'border-primary-500 bg-primary-50 text-primary-600 shadow-md'
                      : completed
                        ? 'border-emerald-200 bg-emerald-50 text-emerald-600'
                        : 'border-gray-200 bg-white text-gray-500'
                  }`}
                >
                  <span className="text-xs font-semibold uppercase tracking-wide">ขั้นตอนที่ {index + 1}</span>
                  <span className="mt-2 text-sm font-bold">{label}</span>
                  <span className="mt-3 h-1 w-full rounded-full bg-gradient-to-r from-primary-400 to-secondary-400" />
                </div>
              );
            },
          )}
        </nav>

        <form className="space-y-10" onSubmit={form.handleSubmit(onSubmit)}>
          {currentStep === 0 && (
            <section className="grid gap-6 lg:grid-cols-2">
              <div className="space-y-5 rounded-2xl border border-gray-200/70 bg-white/80 p-6">
                <h2 className="flex items-center gap-3 text-lg font-semibold text-gray-900">
                  <Users className="h-5 w-5 text-primary-500" /> ข้อมูลผู้ขอใช้รถ
                </h2>
                <div className="grid gap-4">
                  <label className="space-y-2 text-sm">
                    <span className="font-medium text-gray-700">ชื่อผู้ขอใช้รถ</span>
                    <input
                      type="text"
                      {...form.register('requesterName')}
                      className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
                      placeholder="กรอกชื่อ-นามสกุล"
                    />
                    {form.formState.errors.requesterName && (
                      <p className="text-xs text-rose-500">{form.formState.errors.requesterName.message}</p>
                    )}
                  </label>
                  <label className="space-y-2 text-sm">
                    <span className="font-medium text-gray-700">ฝ่าย/แผนก</span>
                    <input
                      type="text"
                      {...form.register('department')}
                      className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
                      placeholder="เช่น ฝ่ายขาย วิศวกรรม"
                    />
                    {form.formState.errors.department && (
                      <p className="text-xs text-rose-500">{form.formState.errors.department.message}</p>
                    )}
                  </label>
                  <label className="space-y-2 text-sm">
                    <span className="font-medium text-gray-700">อีเมลสำหรับติดต่อ</span>
                    <input
                      type="email"
                      {...form.register('contactEmail')}
                      className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
                      placeholder="name@example.com"
                    />
                    {form.formState.errors.contactEmail && (
                      <p className="text-xs text-rose-500">{form.formState.errors.contactEmail.message}</p>
                    )}
                  </label>
                  <label className="space-y-2 text-sm">
                    <span className="font-medium text-gray-700">เบอร์ติดต่อ</span>
                    <input
                      type="tel"
                      {...form.register('contactPhone')}
                      className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
                      placeholder="08X-XXX-XXXX"
                    />
                    {form.formState.errors.contactPhone && (
                      <p className="text-xs text-rose-500">{form.formState.errors.contactPhone.message}</p>
                    )}
                  </label>
                </div>
              </div>
              <div className="space-y-5 rounded-2xl border border-gray-200/70 bg-gradient-to-br from-primary-50/90 via-white to-secondary-50/90 p-6">
                <h2 className="text-lg font-semibold text-gray-900">ข้อมูลเสริม</h2>
                <label className="space-y-2 text-sm">
                  <span className="font-medium text-gray-700">จำนวนผู้โดยสาร</span>
                  <input
                    type="number"
                    min={1}
                    max={50}
                    {...form.register('passengers', { valueAsNumber: true })}
                    className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
                  />
                  {form.formState.errors.passengers && (
                    <p className="text-xs text-rose-500">{form.formState.errors.passengers.message}</p>
                  )}
                </label>
                <label className="space-y-2 text-sm">
                  <span className="font-medium text-gray-700">วัตถุประสงค์ของการเดินทาง</span>
                  <textarea
                    rows={4}
                    {...form.register('purpose')}
                    className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
                    placeholder="อธิบายเป้าหมายของการเดินทางและภารกิจ"
                  />
                  {form.formState.errors.purpose && (
                    <p className="text-xs text-rose-500">{form.formState.errors.purpose.message}</p>
                  )}
                </label>
                <div className="rounded-2xl border border-dashed border-primary-200 bg-primary-50/70 p-4 text-xs text-primary-700">
                  <p className="font-semibold">เคล็ดลับการอนุมัติเร็ว</p>
                  <p className="mt-1">
                    ระบุจุดประสงค์และรายละเอียดผู้ร่วมเดินทางให้ชัดเจน ผู้อนุมัติจะสามารถตรวจสอบและอนุมัติได้เร็วขึ้น
                  </p>
                </div>
              </div>
            </section>
          )}

          {currentStep === 1 && (
            <section className="grid gap-6 lg:grid-cols-[1.3fr_1fr]">
              <div className="space-y-6 rounded-2xl border border-gray-200/70 bg-white/80 p-6">
                <h2 className="flex items-center gap-3 text-lg font-semibold text-gray-900">
                  <CalendarClock className="h-5 w-5 text-primary-500" /> เลือกกำหนดการเดินทาง
                </h2>
                <div className="grid gap-4 sm:grid-cols-2">
                  <label className="space-y-2 text-sm">
                    <span className="font-medium text-gray-700">วันและเวลาออกเดินทาง</span>
                    <input
                      type="datetime-local"
                      {...form.register('start')}
                      min={format(new Date(), "yyyy-MM-dd'T'HH:00")}
                      className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
                    />
                    {form.formState.errors.start && (
                      <p className="text-xs text-rose-500">{form.formState.errors.start.message}</p>
                    )}
                  </label>
                  <label className="space-y-2 text-sm">
                    <span className="font-medium text-gray-700">วันและเวลากลับถึง</span>
                    <input
                      type="datetime-local"
                      {...form.register('end')}
                      min={values.start}
                      className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
                    />
                    {form.formState.errors.end && (
                      <p className="text-xs text-rose-500">{form.formState.errors.end.message}</p>
                    )}
                  </label>
                </div>
                <div className="rounded-2xl border border-dashed border-amber-200 bg-amber-50/60 p-4 text-sm text-amber-700">
                  <p className="font-semibold">คำแนะนำ</p>
                  <p className="mt-1">
                    ระบบจะตรวจสอบความซ้ำซ้อนกับตารางการใช้งานของยานพาหนะ หากพบการจองที่ทับซ้อนกันจะแจ้งเตือนโดยอัตโนมัติ
                  </p>
                </div>
              </div>
              <aside className="space-y-4 rounded-2xl border border-primary-100/70 bg-gradient-to-br from-primary-50 via-white to-secondary-50 p-6">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-primary-600">การตรวจสอบความซ้ำซ้อน</h3>
                {conflicts.length === 0 ? (
                  <div className="rounded-2xl border border-emerald-200 bg-emerald-50/80 p-4 text-sm text-emerald-700">
                    <p className="flex items-center gap-2 font-semibold">
                      <CheckCircle2 className="h-4 w-4" /> ไม่มีการจองทับซ้อน
                    </p>
                    <p className="mt-2 text-xs">สามารถดำเนินการต่อได้ทันที</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {conflicts.map((conflict) => (
                      <div key={conflict.id} className="rounded-2xl border border-rose-200 bg-rose-50/90 p-4 text-sm text-rose-700">
                        <p className="font-semibold">{conflict.summary}</p>
                        <p className="mt-1 text-xs">
                          {format(parseISO(conflict.start), 'd MMM yyyy HH:mm')} - {format(parseISO(conflict.end), 'HH:mm')} น.
                        </p>
                        <p className="mt-2 text-xs">กรุณาเลือกช่วงเวลาอื่นหรือยานพาหนะคนละคัน</p>
                      </div>
                    ))}
                  </div>
                )}
              </aside>
            </section>
          )}

          {currentStep === 2 && (
            <section className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
              <div className="space-y-6 rounded-2xl border border-gray-200/70 bg-white/85 p-6">
                <h2 className="flex items-center gap-3 text-lg font-semibold text-gray-900">
                  <MapPin className="h-5 w-5 text-primary-500" /> ระบุสถานที่รับและส่ง
                </h2>
                <div className="grid gap-4">
                  <div className="space-y-2 text-sm">
                    <label className="font-medium text-gray-700">สถานที่รับ</label>
                    <input
                      type="text"
                      {...form.register('origin')}
                      list="popular-origins"
                      placeholder="ค้นหาหรือเลือกจากรายการ"
                      className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
                    />
                    <datalist id="popular-origins">
                      {popularLocations.map((location) => (
                        <option key={location.id} value={location.name}>
                          {location.address}
                        </option>
                      ))}
                    </datalist>
                    {form.formState.errors.origin && (
                      <p className="text-xs text-rose-500">{form.formState.errors.origin.message}</p>
                    )}
                  </div>
                  <label className="space-y-2 text-sm">
                    <span className="font-medium text-gray-700">รายละเอียดเพิ่มเติมจุดรับ</span>
                    <input
                      type="text"
                      {...form.register('originNotes')}
                      placeholder="เช่น อาคาร A ประตู 3"
                      className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
                    />
                  </label>
                  <div className="space-y-2 text-sm">
                    <label className="font-medium text-gray-700">สถานที่ปลายทาง</label>
                    <input
                      type="text"
                      {...form.register('destination')}
                      list="popular-destinations"
                      placeholder="ค้นหาหรือเลือกจากรายการ"
                      className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
                    />
                    <datalist id="popular-destinations">
                      {popularLocations.map((location) => (
                        <option key={location.id} value={location.name}>
                          {location.address}
                        </option>
                      ))}
                    </datalist>
                    {form.formState.errors.destination && (
                      <p className="text-xs text-rose-500">{form.formState.errors.destination.message}</p>
                    )}
                  </div>
                  <label className="space-y-2 text-sm">
                    <span className="font-medium text-gray-700">รายละเอียดเพิ่มเติมปลายทาง</span>
                    <input
                      type="text"
                      {...form.register('destinationNotes')}
                      placeholder="เช่น อาคารสัมมนา ชั้น 5"
                      className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
                    />
                  </label>
                </div>
              </div>
              <aside className="space-y-4 rounded-2xl border border-primary-100/70 bg-gradient-to-br from-primary-50 via-white to-secondary-50 p-6">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-primary-600">แผนที่นำทาง</h3>
                {locationPreview.origin ? (
                  <div className="space-y-3 text-xs text-gray-600">
                    <p className="font-semibold text-gray-800">จุดรับ</p>
                    <p>{locationPreview.origin.address}</p>
                    <iframe
                      title="origin-map"
                      className="h-40 w-full rounded-xl border border-primary-100"
                      src={`https://www.google.com/maps?q=${locationPreview.origin.latitude},${locationPreview.origin.longitude}&z=15&output=embed`}
                      loading="lazy"
                    />
                  </div>
                ) : (
                  <p className="text-xs text-gray-500">เลือกสถานที่เพื่อดูแผนที่ทันที</p>
                )}
                {locationPreview.destination && (
                  <div className="space-y-3 text-xs text-gray-600">
                    <p className="font-semibold text-gray-800">ปลายทาง</p>
                    <p>{locationPreview.destination.address}</p>
                    <iframe
                      title="destination-map"
                      className="h-40 w-full rounded-xl border border-primary-100"
                      src={`https://www.google.com/maps?q=${locationPreview.destination.latitude},${locationPreview.destination.longitude}&z=15&output=embed`}
                      loading="lazy"
                    />
                  </div>
                )}
              </aside>
            </section>
          )}

          {currentStep === 3 && (
            <section className="space-y-6">
              <div className="rounded-2xl border border-gray-200 bg-white/90 p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900">เลือกยานพาหนะที่ต้องการ</h2>
                <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                  {vehicleOptions.map((vehicle) => {
                    const availability = vehicleAvailability(vehicle, values.start, values.end);
                    const selected = values.preferredVehicleId === vehicle.id;
                    return (
                      <button
                        type="button"
                        key={vehicle.id}
                        onClick={() => {
                          if (availability.status !== 'available') return;
                          form.setValue('preferredVehicleId', vehicle.id);
                          form.setValue('preferredVehicleType', vehicle.type);
                        }}
                        className={`flex h-full flex-col rounded-2xl border p-5 text-left transition-all ${
                          selected
                            ? 'border-primary-500 bg-primary-50 shadow-lg'
                            : 'border-gray-200 bg-white/80 hover:border-primary-300 hover:shadow-md'
                        } ${availability.status !== 'available' ? 'cursor-not-allowed opacity-70' : ''}`}
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="text-sm font-semibold text-gray-900">{vehicle.name}</p>
                            <p className="text-xs text-gray-500">{vehicle.type} • รองรับ {vehicle.capacity} ที่นั่ง</p>
                          </div>
                          <span
                            className={`inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-semibold ${
                              availability.status === 'available'
                                ? 'bg-emerald-100 text-emerald-600'
                                : availability.status === 'conflict'
                                  ? 'bg-rose-100 text-rose-600'
                                  : 'bg-amber-100 text-amber-600'
                            }`}
                          >
                            {availability.message}
                          </span>
                        </div>
                        <ul className="mt-3 space-y-1 text-xs text-gray-600">
                          {vehicle.features.map((feature) => (
                            <li key={feature} className="flex items-center gap-2">
                              <span className="h-1.5 w-1.5 rounded-full bg-primary-400" /> {feature}
                            </li>
                          ))}
                        </ul>
                        <p className="mt-3 text-xs text-gray-400">ที่ตั้ง: {vehicle.location}</p>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                <div className="space-y-4 rounded-2xl border border-gray-200 bg-white/90 p-6">
                  <label className="space-y-2 text-sm">
                    <span className="font-medium text-gray-700">ประเภทยานพาหนะที่เหมาะสม</span>
                    <select
                      {...form.register('preferredVehicleType')}
                      className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
                    >
                      {vehicleTypeOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                    {form.formState.errors.preferredVehicleType && (
                      <p className="text-xs text-rose-500">{form.formState.errors.preferredVehicleType.message}</p>
                    )}
                  </label>
                  <label className="flex items-center gap-3 text-sm text-gray-700">
                    <input type="checkbox" {...form.register('requireDriverSupport')} className="h-4 w-4 rounded border-gray-300" />
                    ต้องการคนขับจากศูนย์ยานพาหนะ
                  </label>
                  <label className="flex items-center gap-3 text-sm text-gray-700">
                    <input type="checkbox" {...form.register('allowSharing')} className="h-4 w-4 rounded border-gray-300" />
                    ยินยอมแชร์รถกับทีมอื่น หากเส้นทางใกล้เคียง
                  </label>
                </div>
                <div className="space-y-3 rounded-2xl border border-gray-200 bg-white/90 p-6">
                  <p className="text-sm font-semibold text-gray-900">อุปกรณ์เสริมที่ต้องการ</p>
                  <div className="grid grid-cols-2 gap-3">
                    {equipmentOptions.map((item) => {
                      const checked = values.additionalEquipment?.includes(item) ?? false;
                      return (
                        <label
                          key={item}
                          className={`flex cursor-pointer items-center gap-2 rounded-xl border px-3 py-2 text-xs font-medium transition ${
                            checked ? 'border-primary-400 bg-primary-50 text-primary-700' : 'border-gray-200 text-gray-600'
                          }`}
                        >
                          <input
                            type="checkbox"
                            value={item}
                            checked={checked}
                            onChange={(event) => {
                              const selected = new Set(values.additionalEquipment ?? []);
                              if (event.target.checked) {
                                selected.add(item);
                              } else {
                                selected.delete(item);
                              }
                              form.setValue('additionalEquipment', Array.from(selected));
                            }}
                            className="hidden"
                          />
                          <span className="h-2 w-2 rounded-full bg-primary-400" /> {item}
                        </label>
                      );
                    })}
                  </div>
                  <div className="rounded-xl border border-dashed border-primary-200 bg-primary-50/70 p-4 text-xs text-primary-700">
                    มีรถที่พร้อมให้บริการ {availableVehicles.length} คัน ในช่วงเวลาที่เลือก
                  </div>
                </div>
              </div>
            </section>
          )}

          {currentStep === 4 && (
            <section className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
              <div className="space-y-5 rounded-2xl border border-gray-200 bg-white/95 p-6">
                <h2 className="text-lg font-semibold text-gray-900">ตรวจสอบรายละเอียดก่อนยืนยัน</h2>
                <div className="grid gap-4 text-sm text-gray-600">
                  <div className="rounded-2xl border border-gray-100 bg-gray-50/80 p-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">กำหนดการ</p>
                    <p className="mt-1 text-sm font-semibold text-gray-900">
                      {startDate && endDate
                        ? `${format(startDate, 'd MMM yyyy HH:mm')} - ${format(endDate, 'd MMM yyyy HH:mm')} น.`
                        : 'ยังไม่ได้ระบุช่วงเวลา'}
                    </p>
                    <p className="mt-2 text-xs text-gray-500">ผู้โดยสาร {values.passengers} คน</p>
                    <p className="text-xs text-gray-500">วัตถุประสงค์: {values.purpose || '—'}</p>
                  </div>
                  <div className="rounded-2xl border border-gray-100 bg-gray-50/80 p-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">ข้อมูลผู้ขอ</p>
                    <p className="mt-1 text-sm font-semibold text-gray-900">{values.requesterName}</p>
                    <p className="text-xs text-gray-500">ฝ่าย {values.department}</p>
                    <p className="mt-2 text-xs">อีเมล: {values.contactEmail}</p>
                    <p className="text-xs">โทร: {values.contactPhone}</p>
                  </div>
                  <div className="rounded-2xl border border-gray-100 bg-gray-50/80 p-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">เส้นทาง</p>
                    <p className="mt-1 text-sm font-semibold text-gray-900">จาก {values.origin} ไป {values.destination}</p>
                    <p className="mt-1 text-xs text-gray-500">
                      จุดรับ: {values.originNotes || '—'} • ปลายทาง: {values.destinationNotes || '—'}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-gray-100 bg-gray-50/80 p-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">ยานพาหนะและบริการ</p>
                    <p className="mt-1 text-sm font-semibold text-gray-900">
                      ประเภท: {values.preferredVehicleType} • คันที่เลือก: {values.preferredVehicleId || 'ยังไม่ได้เลือก'}
                    </p>
                    <p className="mt-1 text-xs text-gray-500">
                      {values.requireDriverSupport ? 'ต้องการคนขับจากศูนย์' : 'เตรียมคนขับเอง'} •{' '}
                      {values.allowSharing ? 'ยินยอมแชร์รถ' : 'ไม่แชร์รถกับทีมอื่น'}
                    </p>
                    {values.additionalEquipment && values.additionalEquipment.length > 0 ? (
                      <p className="mt-1 text-xs text-gray-500">
                        อุปกรณ์เสริม: {values.additionalEquipment.join(', ')}
                      </p>
                    ) : (
                      <p className="mt-1 text-xs text-gray-400">ไม่มีอุปกรณ์เสริม</p>
                    )}
                  </div>
                </div>
                <label className="flex items-center gap-3 rounded-2xl border border-gray-200 bg-white px-4 py-3 text-xs text-gray-600">
                  <input type="checkbox" {...form.register('termsAccepted')} className="h-4 w-4 rounded border-gray-300" />
                  ข้าพเจ้าขอยืนยันว่าข้อมูลถูกต้องและยอมรับนโยบายการใช้ยานพาหนะขององค์กร
                </label>
                {form.formState.errors.termsAccepted && (
                  <p className="text-xs text-rose-500">{form.formState.errors.termsAccepted.message}</p>
                )}
              </div>
              <aside className="space-y-4 rounded-2xl border border-primary-100/70 bg-gradient-to-br from-primary-50 via-white to-secondary-50 p-6">
                <div className="flex items-start gap-3">
                  <span className="mt-1 inline-flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-primary-600">
                    <Info className="h-4 w-4" />
                  </span>
                  <div className="text-sm text-gray-600">
                    <p className="font-semibold text-gray-900">ตรวจสอบก่อนส่ง</p>
                    <p className="mt-1 text-xs">
                      หลังจากส่งคำขอ คุณสามารถติดตามสถานะได้ทันทีผ่านแดชบอร์ด และสามารถแก้ไขหรือยกเลิกได้ก่อนการอนุมัติ
                    </p>
                  </div>
                </div>
                {submitted ? (
                  <div className="rounded-2xl border border-emerald-200 bg-emerald-50/80 p-4 text-sm text-emerald-700">
                    <p className="font-semibold">ส่งคำขอเรียบร้อยแล้ว</p>
                    <p className="mt-1 text-xs">ระบบได้บันทึกคำขอของคุณและแจ้งเตือนผู้อนุมัติแล้ว</p>
                  </div>
                ) : (
                  <button
                    type="submit"
                    className="w-full rounded-2xl bg-gradient-to-r from-primary-500 to-secondary-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-primary-200 transition hover:from-primary-600 hover:to-secondary-600"
                  >
                    ส่งคำขอจองรถ
                  </button>
                )}
              </aside>
            </section>
          )}

          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={handlePrevious}
              disabled={currentStep === 0}
              className="inline-flex items-center gap-2 rounded-xl border border-gray-300 px-4 py-2 text-sm font-medium text-gray-600 transition hover:border-primary-300 hover:text-primary-600 disabled:cursor-not-allowed disabled:border-gray-200 disabled:text-gray-300"
            >
              <ChevronLeft className="h-4 w-4" /> ย้อนกลับ
            </button>
            {currentStep < stepFields.length - 1 && (
              <button
                type="button"
                onClick={handleNext}
                className="inline-flex items-center gap-2 rounded-xl bg-primary-500 px-5 py-2.5 text-sm font-semibold text-white shadow transition hover:bg-primary-600"
              >
                ถัดไป <ChevronRight className="h-4 w-4" />
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
