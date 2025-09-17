"use client";

import { notFound, useRouter } from 'next/navigation';
import { useMemo, useState } from 'react';

import { format, parseISO } from 'date-fns';
import { ArrowLeft, CalendarCheck2, CarFront, Edit3, MapPinned, RefreshCcw, ShieldAlert, UserRound } from 'lucide-react';

import { mockBookings, vehicleOptions } from '@/components/bookings/sampleData';

function StatusBadge({ status }: { status: string }) {
  const variant = (() => {
    switch (status) {
      case 'Approved':
        return 'bg-emerald-100 text-emerald-600';
      case 'Pending':
        return 'bg-amber-100 text-amber-600';
      case 'Rejected':
        return 'bg-rose-100 text-rose-600';
      case 'Completed':
        return 'bg-primary-100 text-primary-600';
      case 'InProgress':
        return 'bg-sky-100 text-sky-600';
      default:
        return 'bg-slate-100 text-slate-600';
    }
  })();

  return <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${variant}`}>{status}</span>;
}

export default function BookingDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const booking = useMemo(() => mockBookings.find((item) => item.id === params.id), [params.id]);
  const [currentBooking, setCurrentBooking] = useState(() => booking);
  const [editMode, setEditMode] = useState(false);
  const [formState, setFormState] = useState(() => ({
    start: booking ? booking.start.slice(0, 16) : '',
    end: booking ? booking.end.slice(0, 16) : '',
    notes: booking?.notes ?? '',
  }));
  const [cancelled, setCancelled] = useState(false);

  if (!booking) {
    notFound();
  }

  const vehicle = vehicleOptions.find((item) => item.id === (currentBooking?.vehicleId ?? ''));

  const handleSave = () => {
    if (!currentBooking || !formState.start || !formState.end) return;
    const updated = {
      ...currentBooking,
      start: formState.start,
      end: formState.end,
      notes: formState.notes,
      status: cancelled ? 'Cancelled' : currentBooking.status,
    };
    setCurrentBooking(updated);
    setEditMode(false);
  };

  const handleCancelBooking = () => {
    setCancelled(true);
    setCurrentBooking((prev) => (prev ? { ...prev, status: 'Cancelled' } : prev));
  };

  return (
    <div className="space-y-8">
      <button
        type="button"
        onClick={() => router.push('/bookings')}
        className="inline-flex items-center gap-2 text-sm font-semibold text-primary-600 transition hover:text-primary-700"
      >
        <ArrowLeft className="h-4 w-4" /> ย้อนกลับไปยังรายการทั้งหมด
      </button>

      <header className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-3 rounded-3xl border border-primary-100/80 bg-gradient-to-br from-primary-50 via-white to-secondary-50 p-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-primary-500">Booking ID</p>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-bold text-gray-900">{currentBooking?.id}</h1>
            {currentBooking && <StatusBadge status={currentBooking.status} />}
          </div>
          <p className="text-sm text-gray-600">{currentBooking?.purpose}</p>
          <div className="grid gap-3 text-xs text-gray-500 sm:grid-cols-2">
            <p>
              ผู้ขอ: <span className="font-semibold text-gray-800">{currentBooking?.requester}</span>
            </p>
            <p>
              ฝ่าย: <span className="font-semibold text-gray-800">{currentBooking?.department}</span>
            </p>
            <p>
              ผู้โดยสาร: <span className="font-semibold text-gray-800">{currentBooking?.passengers} คน</span>
            </p>
            <p>
              คนขับ: <span className="font-semibold text-gray-800">{currentBooking?.driver || 'รอจัดสรร'}</span>
            </p>
          </div>
        </div>
        <div className="space-y-4 rounded-3xl border border-gray-200/80 bg-white/90 p-6">
          <h2 className="flex items-center gap-3 text-lg font-semibold text-gray-900">
            <CalendarCheck2 className="h-5 w-5 text-primary-500" /> ตารางการเดินทาง
          </h2>
          <div className="space-y-2 text-sm text-gray-600">
            <p>
              ออกเดินทาง:{' '}
              {currentBooking?.start ? `${format(parseISO(currentBooking.start), 'd MMM yyyy HH:mm')} น.` : 'ยังไม่กำหนด'}
            </p>
            <p>
              กลับถึง:{' '}
              {currentBooking?.end ? `${format(parseISO(currentBooking.end), 'd MMM yyyy HH:mm')} น.` : 'ยังไม่กำหนด'}
            </p>
          </div>
          {vehicle && (
            <div className="rounded-2xl border border-primary-100 bg-primary-50/70 p-4 text-sm text-primary-700">
              <p className="font-semibold">ยานพาหนะที่จัดสรร</p>
              <p className="text-xs text-primary-600">{vehicle.name} • {vehicle.type} • รองรับ {vehicle.capacity} ที่นั่ง</p>
            </div>
          )}
        </div>
      </header>

      <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6 rounded-3xl border border-gray-200/70 bg-white/90 p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">ประวัติสถานะ</h2>
            <button
              type="button"
              onClick={() => setEditMode((prev) => !prev)}
              className="inline-flex items-center gap-2 rounded-xl border border-primary-300 px-3 py-1.5 text-xs font-semibold text-primary-600 transition hover:bg-primary-50"
            >
              <Edit3 className="h-3.5 w-3.5" /> {editMode ? 'ยกเลิก' : 'แก้ไขรายละเอียด'}
            </button>
          </div>
          <ol className="space-y-4 border-l-2 border-dashed border-primary-200 pl-5 text-sm text-gray-600">
            {currentBooking?.history?.map((item) => (
              <li key={item.id} className="relative space-y-1">
                <span
                  className={`absolute -left-6 flex h-9 w-9 items-center justify-center rounded-full border-2 bg-white text-xs font-semibold ${
                    item.state === 'complete'
                      ? 'border-emerald-300 text-emerald-600'
                      : item.state === 'current'
                        ? 'border-primary-300 text-primary-600'
                        : 'border-gray-200 text-gray-400'
                  }`}
                >
                  ●
                </span>
                <p className="text-sm font-semibold text-gray-900">{item.label}</p>
                <p className="text-xs text-gray-500">{item.description}</p>
                <p className="text-[11px] text-gray-400">{format(parseISO(item.timestamp), 'd MMM yyyy HH:mm')} น.</p>
              </li>
            ))}
          </ol>

          {editMode && (
            <div className="space-y-4 rounded-2xl border border-primary-100 bg-primary-50/60 p-5 text-sm">
              <h3 className="font-semibold text-primary-700">ปรับปรุงข้อมูลการเดินทาง</h3>
              <label className="space-y-1 text-xs text-primary-700">
                <span className="font-semibold">เวลาออกเดินทาง</span>
                <input
                  type="datetime-local"
                  value={formState.start}
                  onChange={(event) => setFormState((prev) => ({ ...prev, start: event.target.value }))}
                  className="w-full rounded-xl border border-primary-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-200"
                />
              </label>
              <label className="space-y-1 text-xs text-primary-700">
                <span className="font-semibold">เวลากลับถึง</span>
                <input
                  type="datetime-local"
                  value={formState.end}
                  onChange={(event) => setFormState((prev) => ({ ...prev, end: event.target.value }))}
                  className="w-full rounded-xl border border-primary-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-200"
                />
              </label>
              <label className="space-y-1 text-xs text-primary-700">
                <span className="font-semibold">บันทึกเพิ่มเติมสำหรับคนขับ</span>
                <textarea
                  rows={3}
                  value={formState.notes}
                  onChange={(event) => setFormState((prev) => ({ ...prev, notes: event.target.value }))}
                  className="w-full rounded-xl border border-primary-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-200"
                />
              </label>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleSave}
                  className="inline-flex items-center gap-2 rounded-xl bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-600"
                >
                  <RefreshCcw className="h-4 w-4" /> บันทึกการเปลี่ยนแปลง
                </button>
                <button
                  type="button"
                  onClick={() => setEditMode(false)}
                  className="rounded-xl border border-primary-300 px-3 py-2 text-xs font-semibold text-primary-600 hover:bg-primary-50"
                >
                  ยกเลิกการแก้ไข
                </button>
              </div>
            </div>
          )}
        </div>

        <aside className="space-y-6 rounded-3xl border border-gray-200/70 bg-white/95 p-6">
          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-gray-900">รายละเอียดการเดินทาง</h2>
            <div className="rounded-2xl border border-gray-100 bg-gray-50/80 p-4 text-sm text-gray-600">
              <p className="flex items-center gap-2 font-semibold text-gray-900">
                <MapPinned className="h-4 w-4 text-primary-500" /> เส้นทาง
              </p>
              <p className="mt-1 text-xs">จาก {currentBooking?.origin}</p>
              <p className="text-xs">ไป {currentBooking?.destination}</p>
              {currentBooking?.notes && <p className="mt-2 text-xs text-gray-500">หมายเหตุ: {currentBooking.notes}</p>}
            </div>
            <div className="rounded-2xl border border-gray-100 bg-gray-50/80 p-4 text-sm text-gray-600">
              <p className="flex items-center gap-2 font-semibold text-gray-900">
                <CarFront className="h-4 w-4 text-primary-500" /> ยานพาหนะ
              </p>
              <p className="mt-1 text-xs">{currentBooking?.vehicleId || 'รอจัดสรรรถ'}</p>
              <p className="text-xs">คนขับ {currentBooking?.driver || 'รอจัดสรร'}</p>
            </div>
            <div className="rounded-2xl border border-gray-100 bg-gray-50/80 p-4 text-sm text-gray-600">
              <p className="flex items-center gap-2 font-semibold text-gray-900">
                <UserRound className="h-4 w-4 text-primary-500" /> ผู้อนุมัติ
              </p>
              <ul className="mt-2 space-y-2 text-xs text-gray-600">
                {currentBooking?.approvals?.map((approval) => (
                  <li key={approval.id} className="flex items-center justify-between rounded-xl border border-gray-200 bg-white px-3 py-2">
                    <div>
                      <p className="font-semibold text-gray-900">{approval.approver}</p>
                      <p className="text-[11px] text-gray-500">{approval.role}</p>
                    </div>
                    <span
                      className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${
                        approval.status === 'Approved'
                          ? 'bg-emerald-100 text-emerald-600'
                          : approval.status === 'Rejected'
                            ? 'bg-rose-100 text-rose-600'
                            : 'bg-amber-100 text-amber-600'
                      }`}
                    >
                      {approval.status}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="space-y-3 rounded-2xl border border-rose-200 bg-rose-50/70 p-5 text-xs text-rose-700">
            <p className="flex items-center gap-2 text-sm font-semibold text-rose-600">
              <ShieldAlert className="h-4 w-4" /> ยกเลิกคำขอ
            </p>
            <p>
              หากภารกิจถูกยกเลิกหรือเลื่อนออกไป สามารถกดยกเลิกคำขอได้ ระบบจะแจ้งเตือนผู้เกี่ยวข้องและปล่อยทรัพยากรให้ทีมอื่นใช้งาน
            </p>
            <button
              type="button"
              onClick={handleCancelBooking}
              className="w-full rounded-xl border border-rose-300 px-3 py-2 text-sm font-semibold text-rose-600 transition hover:bg-rose-100"
              disabled={cancelled}
            >
              {cancelled ? 'คำขอถูกยกเลิกแล้ว' : 'ยืนยันการยกเลิกคำขอ'}
            </button>
          </div>
        </aside>
      </section>
    </div>
  );
}
