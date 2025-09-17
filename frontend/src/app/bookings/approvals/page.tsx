"use client";

import { useMemo, useState } from 'react';

import { format, parseISO } from 'date-fns';
import { CheckCircle, ClipboardCheck, Clock4, Filter, Hourglass, Search, XCircle } from 'lucide-react';

import { managerPendingApprovals, mockBookings } from '@/components/bookings/sampleData';

interface ApprovalDecision {
  id: string;
  status: 'Approved' | 'Rejected' | 'Pending';
  comment?: string;
}

export default function BookingApprovalsPage() {
  const [decisions, setDecisions] = useState<Record<string, ApprovalDecision>>({});
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'Pending' | 'Approved' | 'Rejected'>('all');

  const pendingBookings = useMemo(() => {
    return mockBookings.filter((booking) => booking.status === 'Pending');
  }, []);

  const filteredQueue = useMemo(() => {
    return managerPendingApprovals.filter((booking) => {
      const term = searchTerm.toLowerCase();
      const matchesTerm =
        !term ||
        booking.id.toLowerCase().includes(term) ||
        booking.requester.toLowerCase().includes(term) ||
        booking.destination.toLowerCase().includes(term);
      const decision = decisions[booking.id];
      const status = decision?.status ?? 'Pending';
      const matchesStatus = filterStatus === 'all' || status === filterStatus;
      return matchesTerm && matchesStatus;
    });
  }, [decisions, filterStatus, searchTerm]);

  const handleDecision = (id: string, status: 'Approved' | 'Rejected') => {
    setDecisions((prev) => ({
      ...prev,
      [id]: { id, status },
    }));
  };

  const handleCommentChange = (id: string, comment: string) => {
    setDecisions((prev) => ({
      ...prev,
      [id]: { ...(prev[id] ?? { id, status: 'Pending' }), comment },
    }));
  };

  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <p className="text-sm font-semibold uppercase tracking-wide text-primary-500">Manager Workspace</p>
          <h1 className="text-4xl font-bold text-gray-900">ศูนย์อนุมัติคำขอจองรถ</h1>
          <p className="max-w-3xl text-sm text-gray-600">
            ตรวจสอบคำขอรออนุมัติ จัดการลำดับความสำคัญ และบันทึกข้อเสนอแนะอย่างเป็นระบบ ช่วยให้ทีมยานพาหนะเตรียมการได้รวดเร็ว
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-center">
            <p className="text-xs font-semibold text-emerald-600">คำขอรอดำเนินการ</p>
            <p className="text-xl font-bold text-emerald-600">{managerPendingApprovals.length}</p>
          </div>
          <div className="rounded-2xl border border-primary-200 bg-primary-50 px-4 py-3 text-center">
            <p className="text-xs font-semibold text-primary-600">รอคำตอบจากฉัน</p>
            <p className="text-xl font-bold text-primary-600">
              {Object.values(decisions).filter((decision) => decision.status === 'Pending').length}
            </p>
          </div>
        </div>
      </header>

      <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-4 rounded-3xl border border-gray-200/70 bg-white/95 p-6">
          <div className="flex flex-wrap items-center gap-3">
            <label className="flex flex-1 min-w-[200px] items-center gap-3 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-500">
              <Search className="h-4 w-4" />
              <input
                type="search"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="ค้นหาคำขอจากรหัส ผู้ขอ หรือปลายทาง"
                className="w-full border-none bg-transparent text-sm text-gray-700 focus:outline-none"
              />
            </label>
            <label className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-500">
              <Filter className="h-4 w-4" />
              <select
                value={filterStatus}
                onChange={(event) => setFilterStatus(event.target.value as typeof filterStatus)}
                className="w-full border-none bg-transparent text-sm text-gray-700 focus:outline-none"
              >
                <option value="all">สถานะทั้งหมด</option>
                <option value="Pending">รอพิจารณา</option>
                <option value="Approved">อนุมัติแล้ว</option>
                <option value="Rejected">ถูกปฏิเสธ</option>
              </select>
            </label>
          </div>

          <div className="space-y-4">
            {filteredQueue.map((booking) => {
              const decision = decisions[booking.id];
              return (
                <div key={booking.id} className="space-y-4 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-gray-900">{booking.id}</p>
                      <p className="text-xs text-gray-500">
                        {booking.requester} • ฝ่าย {booking.department} • ผู้โดยสาร {booking.passengers} คน
                      </p>
                    </div>
                    <span className="inline-flex items-center gap-2 rounded-full bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-600">
                      <Hourglass className="h-3.5 w-3.5" /> ความเร่งด่วน: {booking.urgency}
                    </span>
                  </div>

                  <div className="grid gap-3 text-xs text-gray-600 md:grid-cols-3">
                    <p>เส้นทาง: {booking.destination}</p>
                    <p>ช่วงเวลา: {format(parseISO(booking.start), 'd MMM yyyy HH:mm')} - {format(parseISO(booking.end), 'HH:mm')} น.</p>
                    <p>ประเภทรถที่ต้องการ: {booking.vehicleType}</p>
                  </div>
                  {booking.notes && <p className="text-xs text-gray-500">บันทึกเพิ่มเติม: {booking.notes}</p>}

                  <div className="flex flex-col gap-3 rounded-2xl border border-dashed border-primary-200 bg-primary-50/60 p-4 text-xs text-primary-700">
                    <p className="flex items-center gap-2 text-sm font-semibold text-primary-700">
                      <ClipboardCheck className="h-4 w-4" /> การตัดสินใจของฉัน
                    </p>
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        type="button"
                        onClick={() => handleDecision(booking.id, 'Approved')}
                        className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition ${
                          decision?.status === 'Approved'
                            ? 'bg-emerald-500 text-white shadow'
                            : 'bg-white text-emerald-600 hover:bg-emerald-100'
                        }`}
                      >
                        <CheckCircle className="h-4 w-4" /> อนุมัติ
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDecision(booking.id, 'Rejected')}
                        className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition ${
                          decision?.status === 'Rejected'
                            ? 'bg-rose-500 text-white shadow'
                            : 'bg-white text-rose-600 hover:bg-rose-100'
                        }`}
                      >
                        <XCircle className="h-4 w-4" /> ปฏิเสธ
                      </button>
                      <span className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-1 text-[11px] font-semibold text-amber-600">
                        สถานะปัจจุบัน: {decision?.status ?? 'Pending'}
                      </span>
                    </div>
                    <textarea
                      rows={2}
                      placeholder="บันทึกเหตุผลหรือคำแนะนำสำหรับทีมยานพาหนะ"
                      value={decision?.comment ?? ''}
                      onChange={(event) => handleCommentChange(booking.id, event.target.value)}
                      className="w-full rounded-xl border border-primary-200 bg-white px-3 py-2 text-xs text-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-200"
                    />
                  </div>
                </div>
              );
            })}

            {filteredQueue.length === 0 && (
              <div className="rounded-2xl border border-gray-200 bg-white/80 p-6 text-center text-sm text-gray-500">
                ไม่มีคำขอที่ตรงตามตัวกรองในขณะนี้
              </div>
            )}
          </div>
        </div>

        <aside className="space-y-4 rounded-3xl border border-gray-200/70 bg-white/95 p-6">
          <h2 className="text-lg font-semibold text-gray-900">ภาพรวมคำขอรอดำเนินการ</h2>
          <div className="space-y-3 text-sm text-gray-600">
            {pendingBookings.map((booking) => (
              <div key={booking.id} className="rounded-2xl border border-gray-100 bg-gray-50/70 p-4">
                <p className="text-sm font-semibold text-gray-900">{booking.id}</p>
                <p className="text-xs text-gray-500">{booking.requester} • {booking.department}</p>
                <p className="text-xs text-gray-500">
                  {format(parseISO(booking.start), 'd MMM yyyy HH:mm')} - {format(parseISO(booking.end), 'HH:mm')} น.
                </p>
                <p className="mt-1 text-xs text-gray-500">ปลายทาง {booking.destination}</p>
              </div>
            ))}
          </div>
          <div className="rounded-2xl border border-dashed border-primary-200 bg-primary-50/60 p-4 text-xs text-primary-700">
            <p className="flex items-center gap-2 text-sm font-semibold text-primary-700">
              <Clock4 className="h-4 w-4" /> เคล็ดลับการอนุมัติเร็ว
            </p>
            <ul className="mt-2 list-inside list-disc space-y-1">
              <li>ตรวจสอบความสอดคล้องกับนโยบายการใช้รถและจำนวนผู้โดยสาร</li>
              <li>พิจารณาความเร่งด่วนและทรัพยากรที่มีในช่วงเวลาเดียวกัน</li>
              <li>ให้ข้อเสนอแนะเพิ่มเติมเพื่อช่วยทีมยานพาหนะเตรียมการ</li>
            </ul>
          </div>
        </aside>
      </section>
    </div>
  );
}
