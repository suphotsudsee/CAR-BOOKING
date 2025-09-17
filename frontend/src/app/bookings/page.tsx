"use client";

import { useMemo, useState } from 'react';

import { format, isWithinInterval, parseISO } from 'date-fns';
import { Filter, ListFilter, Search, TrendingUp } from 'lucide-react';

import { mockBookings } from '@/components/bookings/sampleData';

const statusOptions = [
  { value: 'all', label: 'สถานะทั้งหมด' },
  { value: 'Pending', label: 'รอดำเนินการ' },
  { value: 'Approved', label: 'อนุมัติแล้ว' },
  { value: 'Rejected', label: 'ถูกปฏิเสธ' },
  { value: 'InProgress', label: 'กำลังดำเนินการ' },
  { value: 'Completed', label: 'เสร็จสิ้น' },
  { value: 'Cancelled', label: 'ถูกยกเลิก' },
];

export default function BookingsListPage() {
  const [status, setStatus] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });

  const filteredBookings = useMemo(() => {
    return mockBookings.filter((booking) => {
      const matchesStatus = status === 'all' || booking.status === status;
      const term = searchTerm.toLowerCase();
      const matchesSearch =
        term.length === 0 ||
        booking.id.toLowerCase().includes(term) ||
        booking.requester.toLowerCase().includes(term) ||
        booking.purpose.toLowerCase().includes(term) ||
        booking.destination.toLowerCase().includes(term);

      const matchesDate = (() => {
        if (!dateRange.start && !dateRange.end) return true;
        const bookingStart = parseISO(booking.start);
        const bookingEnd = parseISO(booking.end);
        if (dateRange.start && dateRange.end) {
          return isWithinInterval(bookingStart, {
            start: new Date(dateRange.start),
            end: new Date(dateRange.end),
          });
        }
        if (dateRange.start) {
          return bookingStart >= new Date(dateRange.start);
        }
        if (dateRange.end) {
          return bookingEnd <= new Date(dateRange.end);
        }
        return true;
      })();

      return matchesStatus && matchesSearch && matchesDate;
    });
  }, [dateRange.end, dateRange.start, searchTerm, status]);

  const upcoming = filteredBookings.filter((booking) => parseISO(booking.start) > new Date());

  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <p className="text-sm font-semibold uppercase tracking-wide text-primary-500">Booking Management</p>
          <h1 className="text-4xl font-bold text-gray-900">การจัดการคำขอจองรถ</h1>
          <p className="max-w-3xl text-sm text-gray-600">
            ตรวจสอบสถานะคำขอทั้งหมด ค้นหาด้วยรหัสคำขอ ผู้ขอ หรือปลายทาง พร้อมตัวกรองตามช่วงเวลาเพื่อการติดตามที่รวดเร็ว
          </p>
        </div>
        <div className="flex items-center gap-3">
          <a
            href="/bookings/new"
            className="rounded-xl bg-primary-500 px-4 py-2 text-sm font-semibold text-white shadow transition hover:bg-primary-600"
          >
            + สร้างคำขอใหม่
          </a>
          <a
            href="/bookings/approvals"
            className="rounded-xl border border-primary-300 px-4 py-2 text-sm font-semibold text-primary-600 transition hover:bg-primary-50"
          >
            พื้นที่อนุมัติสำหรับผู้จัดการ
          </a>
        </div>
      </header>

      <section className="rounded-3xl border border-gray-200/70 bg-white/90 p-6 shadow-sm">
        <div className="grid gap-4 md:grid-cols-[1.3fr_1fr]">
          <div className="flex items-center gap-3 rounded-2xl border border-primary-100 bg-primary-50/80 px-4 py-3 text-sm text-primary-700">
            <TrendingUp className="h-5 w-5" />
            <p>
              {upcoming.length > 0
                ? `มีคำขอที่กำลังจะถึง ${upcoming.length} รายการ ตรวจสอบรายละเอียดเพื่อเตรียมความพร้อม`
                : 'ไม่มีคำขอที่กำหนดในช่วงถัดไป สามารถจัดสรรยานพาหนะได้อย่างยืดหยุ่น'}
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3 text-xs text-gray-500">
            <div className="rounded-2xl border border-gray-200 bg-white p-3">
              <p className="font-semibold text-gray-800">คำขอทั้งหมด</p>
              <p className="mt-1 text-lg font-bold text-primary-600">{filteredBookings.length}</p>
            </div>
            <div className="rounded-2xl border border-gray-200 bg-white p-3">
              <p className="font-semibold text-gray-800">รอดำเนินการ</p>
              <p className="mt-1 text-lg font-bold text-amber-600">
                {filteredBookings.filter((booking) => booking.status === 'Pending').length}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-4 rounded-3xl border border-gray-200/70 bg-white/90 p-6 shadow-sm">
        <div className="grid gap-3 md:grid-cols-4">
          <label className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-500">
            <Search className="h-4 w-4" />
            <input
              type="search"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="ค้นหาด้วยรหัสคำขอ ชื่อ หรือปลายทาง"
              className="w-full border-none bg-transparent text-sm text-gray-700 focus:outline-none"
            />
          </label>
          <label className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-500">
            <ListFilter className="h-4 w-4" />
            <select
              value={status}
              onChange={(event) => setStatus(event.target.value)}
              className="w-full border-none bg-transparent text-sm text-gray-700 focus:outline-none"
            >
              {statusOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-500">
            <Filter className="h-4 w-4" />
            <input
              type="date"
              value={dateRange.start}
              onChange={(event) => setDateRange((prev) => ({ ...prev, start: event.target.value }))}
              className="w-full border-none bg-transparent text-sm text-gray-700 focus:outline-none"
            />
          </label>
          <label className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-500">
            <Filter className="h-4 w-4" />
            <input
              type="date"
              value={dateRange.end}
              onChange={(event) => setDateRange((prev) => ({ ...prev, end: event.target.value }))}
              className="w-full border-none bg-transparent text-sm text-gray-700 focus:outline-none"
            />
          </label>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-gray-500">
                <th className="pb-3 pr-4 font-medium">หมายเลขคำขอ</th>
                <th className="pb-3 pr-4 font-medium">ผู้ขอ / ฝ่าย</th>
                <th className="pb-3 pr-4 font-medium">ช่วงเวลา</th>
                <th className="pb-3 pr-4 font-medium">เส้นทาง</th>
                <th className="pb-3 pr-4 font-medium">ยานพาหนะ</th>
                <th className="pb-3 font-medium">สถานะ</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredBookings.map((booking) => (
                <tr key={booking.id} className="align-top transition hover:bg-primary-50/40">
                  <td className="py-3 pr-4 font-semibold text-primary-600">
                    <a href={`/bookings/${booking.id}`} className="hover:underline">
                      {booking.id}
                    </a>
                  </td>
                  <td className="py-3 pr-4 text-gray-600">
                    <p className="font-medium text-gray-900">{booking.requester}</p>
                    <p className="text-xs text-gray-500">{booking.department}</p>
                  </td>
                  <td className="py-3 pr-4 text-gray-600">
                    <p>{format(parseISO(booking.start), 'd MMM yyyy HH:mm')} น.</p>
                    <p className="text-xs text-gray-500">ถึง {format(parseISO(booking.end), 'd MMM yyyy HH:mm')} น.</p>
                  </td>
                  <td className="py-3 pr-4 text-gray-600">
                    <p className="font-medium text-gray-900">{booking.origin}</p>
                    <p className="text-xs text-gray-500">ปลายทาง {booking.destination}</p>
                  </td>
                  <td className="py-3 pr-4 text-gray-600">
                    <p>{booking.vehicleId || 'รอจัดสรร'}</p>
                    <p className="text-xs text-gray-500">คนขับ: {booking.driver || 'รอจัดสรร'}</p>
                  </td>
                  <td className="py-3">
                    <span
                      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${
                        booking.status === 'Approved'
                          ? 'bg-emerald-100 text-emerald-600'
                          : booking.status === 'Pending'
                            ? 'bg-amber-100 text-amber-600'
                            : booking.status === 'Rejected'
                              ? 'bg-rose-100 text-rose-600'
                              : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {statusOptions.find((option) => option.value === booking.status)?.label || booking.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
