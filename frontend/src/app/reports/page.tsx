"use client";

import { useCallback, useEffect, useMemo, useState } from 'react';

import {
  Activity,
  BarChart3,
  CalendarClock,
  Factory,
  Filter,
  Fuel,
  Gauge,
  LineChart,
  RefreshCcw,
  Sparkles,
  TrendingUp,
  Users2,
} from 'lucide-react';

import {
  HorizontalBarChart,
  SimpleColumnChart,
  StackedProgressBar,
  TrendPill,
} from '@/components/reports/visuals';
import type {
  BookingPattern,
  CostRecommendation,
  CustomReportOptions,
  CustomReportSummary,
  DepartmentUsage,
  DriverPerformance,
  ExpenseAnalytics,
  PredictiveMaintenance,
  RawReportOverview,
  ReportOverview,
  VehicleUtilisation,
} from '@/components/reports/types';
import {
  CardGrid,
  SectionCard,
  StatCard,
} from '@/components/dashboard/shared';
import { useAuth } from '@/context/AuthContext';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? '';

interface ReportFilters {
  start: string;
  end: string;
  department: string;
  vehicleType: string;
  drivers: number[];
}

const initialFilters: ReportFilters = {
  start: '',
  end: '',
  department: '',
  vehicleType: '',
  drivers: [],
};

function parseNumber(value: number | string): number {
  if (typeof value === 'number') return value;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatCurrency(value: number): string {
  return value.toLocaleString('th-TH', { style: 'currency', currency: 'THB' });
}

function toIsoBoundary(value: string, endOfDay = false): string {
  if (!value) return '';
  const [year, month, day] = value.split('-').map((segment) => Number(segment));
  if (Number.isNaN(year) || Number.isNaN(month) || Number.isNaN(day)) {
    return '';
  }
  const date = new Date(Date.UTC(year, month - 1, day, endOfDay ? 23 : 0, endOfDay ? 59 : 0, endOfDay ? 59 : 0));
  return date.toISOString();
}

function normaliseReport(payload: RawReportOverview): ReportOverview {
  const vehicleUtilisation: VehicleUtilisation[] = payload.vehicle_utilisation.map((item) => ({
    ...item,
  }));

  const departmentUsage: DepartmentUsage[] = payload.department_usage.map((item) => {
    const date = new Date(item.period);
    const periodLabel = date.toLocaleDateString('th-TH', {
      year: 'numeric',
      month: 'short',
    });
    return { ...item, periodLabel };
  });

  const driverPerformance: DriverPerformance[] = payload.driver_performance.map((item) => ({
    ...item,
  }));

  const expenseSummary: ExpenseAnalytics = {
    generatedAt: payload.expense_summary.generated_at,
    totalJobs: payload.expense_summary.total_jobs,
    totalFuelCost: parseNumber(payload.expense_summary.total_fuel_cost),
    totalTollCost: parseNumber(payload.expense_summary.total_toll_cost),
    totalOtherExpenses: parseNumber(payload.expense_summary.total_other_expenses),
    totalExpenses: parseNumber(payload.expense_summary.total_expenses),
    averageFuelCost: parseNumber(payload.expense_summary.average_fuel_cost),
    averageTotalExpense: parseNumber(payload.expense_summary.average_total_expense),
    statusBreakdown: payload.expense_summary.status_breakdown.map((entry) => ({
      status: entry.status,
      count: entry.count,
      totalExpenses: parseNumber(entry.total_expenses),
    })),
  };

  const predictiveMaintenance: PredictiveMaintenance[] = payload.predictive_maintenance.map((item) => ({
    ...item,
    projectedServiceLabel: new Date(item.projected_service_date).toLocaleDateString('th-TH', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    }),
  }));

  const bookingPatterns: BookingPattern[] = payload.booking_patterns.map((item) => ({
    ...item,
  }));

  const costRecommendations: CostRecommendation[] = payload.cost_recommendations.map((item) => ({
    ...item,
  }));

  const customReportSummary: CustomReportSummary = {
    totalBookings: payload.custom_report_summary.total_bookings,
    totalCompleted: payload.custom_report_summary.total_completed,
    totalExpenses: payload.custom_report_summary.total_expenses,
    averageBookingHours: payload.custom_report_summary.average_booking_hours,
    filters: payload.custom_report_summary.filters,
  };

  const customReportOptions: CustomReportOptions = {
    departments: payload.custom_report_options.departments,
    vehicleTypes: payload.custom_report_options.vehicle_types,
    drivers: payload.custom_report_options.drivers,
  };

  return {
    generatedAt: payload.generated_at,
    timeframeStart: payload.timeframe_start,
    timeframeEnd: payload.timeframe_end,
    vehicleUtilisation,
    departmentUsage,
    driverPerformance,
    expenseSummary,
    predictiveMaintenance,
    bookingPatterns,
    costRecommendations,
    customReportSummary,
    customReportOptions,
  };
}

export default function ReportsPage() {
  const { authenticatedFetch } = useAuth();
  const [data, setData] = useState<ReportOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [appliedFilters, setAppliedFilters] = useState<ReportFilters>(initialFilters);
  const [formState, setFormState] = useState<ReportFilters>(initialFilters);

  const fetchReports = useCallback(
    async (filters: ReportFilters) => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        if (filters.start) {
          params.set('start', toIsoBoundary(filters.start));
        }
        if (filters.end) {
          params.set('end', toIsoBoundary(filters.end, true));
        }
        if (filters.department) {
          params.set('department', filters.department);
        }
        if (filters.vehicleType) {
          params.set('vehicle_type', filters.vehicleType);
        }
        filters.drivers.forEach((driverId) => {
          params.append('drivers', String(driverId));
        });

        const query = params.toString();
        const endpoint = `${API_URL}/api/v1/reports/overview${query ? `?${query}` : ''}`;
        const response = await authenticatedFetch(endpoint);
        if (!response.ok) {
          const details = await response.json().catch(() => ({}));
          const message = typeof details?.detail === 'string' ? details.detail : 'ไม่สามารถโหลดรายงานได้';
          throw new Error(message);
        }
        const payload = (await response.json()) as RawReportOverview;
        setData(normaliseReport(payload));
      } catch (err) {
        const message = err instanceof Error ? err.message : 'เกิดข้อผิดพลาดไม่ทราบสาเหตุ';
        setError(message);
        setData(null);
      } finally {
        setLoading(false);
      }
    },
    [authenticatedFetch],
  );

  useEffect(() => {
    fetchReports(appliedFilters).catch(() => {
      // error state handled in fetchReports
    });
  }, [appliedFilters, fetchReports]);

  const averageUtilisation = useMemo(() => {
    if (!data || data.vehicleUtilisation.length === 0) return 0;
    const total = data.vehicleUtilisation.reduce((sum, item) => sum + item.utilisation_rate, 0);
    return total / data.vehicleUtilisation.length;
  }, [data]);

  const totalRequests = useMemo(() => {
    if (!data) return 0;
    return data.departmentUsage.reduce((sum, item) => sum + item.total_requests, 0);
  }, [data]);

  const activeDrivers = useMemo(() => data?.driverPerformance.length ?? 0, [data]);

  const monthlyAggregation = useMemo(() => {
    if (!data) return [] as { label: string; value: number; detail: string }[];
    const map = new Map<string, { value: number; passengers: number }>();
    data.departmentUsage.forEach((item) => {
      const existing = map.get(item.periodLabel) ?? { value: 0, passengers: 0 };
      existing.value += item.total_requests;
      existing.passengers += item.total_passengers;
      map.set(item.periodLabel, existing);
    });
    return Array.from(map.entries()).map(([label, { value, passengers }]) => ({
      label,
      value,
      detail: `${passengers.toLocaleString()} คน`,
    }));
  }, [data]);

  const expenseStacked = useMemo(() => {
    if (!data) return [];
    const total = data.expenseSummary.totalExpenses;
    const accentMap: Record<string, 'primary' | 'emerald' | 'amber' | 'rose' | 'violet' | 'slate'> = {
      APPROVED: 'emerald',
      PENDING_REVIEW: 'amber',
      NOT_SUBMITTED: 'slate',
      REJECTED: 'rose',
      COMPLETED: 'primary',
    };
    return [
      {
        label: 'ภาพรวมค่าใช้จ่าย',
        total,
        segments: data.expenseSummary.statusBreakdown.map((entry) => ({
          value: entry.totalExpenses,
          accent: accentMap[entry.status] ?? 'primary',
        })),
      },
    ];
  }, [data]);

  const appliedFilterSummary = useMemo(() => {
    const parts: string[] = [];
    if (appliedFilters.start) {
      parts.push(`ตั้งแต่ ${new Date(appliedFilters.start).toLocaleDateString('th-TH')}`);
    }
    if (appliedFilters.end) {
      parts.push(`ถึง ${new Date(appliedFilters.end).toLocaleDateString('th-TH')}`);
    }
    if (appliedFilters.department) {
      parts.push(`หน่วยงาน ${appliedFilters.department}`);
    }
    if (appliedFilters.vehicleType) {
      parts.push(`ประเภทรถ ${appliedFilters.vehicleType}`);
    }
    if (appliedFilters.drivers.length > 0 && data) {
      const labels = data.customReportOptions.drivers
        .filter((driver) => appliedFilters.drivers.includes(driver.id))
        .map((driver) => driver.name);
      if (labels.length > 0) {
        parts.push(`คนขับ ${labels.join(', ')}`);
      }
    }
    return parts.length > 0 ? parts.join(' • ') : 'ทั้งหมด';
  }, [appliedFilters, data]);

  const handleFilterChange = (field: keyof ReportFilters, value: string | number) => {
    setFormState((prev) => {
      if (field === 'drivers' && typeof value === 'number') {
        const exists = prev.drivers.includes(value);
        const drivers = exists ? prev.drivers.filter((id) => id !== value) : [...prev.drivers, value];
        return { ...prev, drivers };
      }
      if (field === 'start' || field === 'end' || field === 'department' || field === 'vehicleType') {
        return { ...prev, [field]: String(value) };
      }
      return prev;
    });
  };

  const handleApplyFilters = () => {
    setAppliedFilters(formState);
  };

  const handleResetFilters = () => {
    setFormState(initialFilters);
    setAppliedFilters(initialFilters);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50/80 via-white to-secondary-50/70 py-10">
      <div className="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mb-8 flex flex-col gap-3">
          <div className="inline-flex items-center gap-2 self-start rounded-full border border-primary-200 bg-white/70 px-4 py-1 text-xs font-semibold text-primary-600 shadow-sm">
            <BarChart3 className="h-3.5 w-3.5" /> ระบบรายงานและการวิเคราะห์
          </div>
          <h1 className="text-3xl font-bold text-gray-900">แดชบอร์ดรายงานภาพรวม</h1>
          <p className="text-sm text-gray-600">
            ติดตามประสิทธิภาพการใช้รถ ค่าใช้จ่าย แนวโน้มการจอง และคำแนะนำเพื่อเพิ่มประสิทธิภาพการบริหารจัดการยานพาหนะ
          </p>
        </div>

        <CardGrid>
          <StatCard
            label="อัตราการใช้งานเฉลี่ย"
            value={`${averageUtilisation.toFixed(1)}%`}
            icon={Gauge}
            accent="primary"
            trend={{ value: appliedFilterSummary, direction: 'steady' }}
          />
          <StatCard
            label="คำขอทั้งหมดในช่วง"
            value={totalRequests.toLocaleString('th-TH')}
            icon={Activity}
            accent="emerald"
            trend={{ value: `${appliedFilters.start || 'เริ่มต้น'} - ${appliedFilters.end || 'ปัจจุบัน'}`, direction: 'up' }}
          />
          <StatCard
            label="ค่าใช้จ่ายรวม"
            value={formatCurrency(data?.expenseSummary.totalExpenses ?? 0)}
            icon={Fuel}
            accent="amber"
            trend={{ value: `${data?.expenseSummary.totalJobs ?? 0} งาน`, direction: 'steady' }}
          />
          <StatCard
            label="จำนวนคนขับที่มีข้อมูล"
            value={`${activeDrivers} คน`}
            icon={Users2}
            accent="violet"
            trend={{ value: 'ปรับตามข้อมูลจริง', direction: 'steady' }}
          />
        </CardGrid>

        <div className="mt-8 grid gap-6 lg:grid-cols-[360px_1fr]">
          <SectionCard
            title="ตัวกรองรายงาน"
            description="ปรับแต่งช่วงเวลาและหน่วยงานเพื่อสร้างรายงานแบบกำหนดเอง"
            icon={Filter}
            actions={
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleResetFilters}
                  className="rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50"
                >
                  รีเซ็ต
                </button>
                <button
                  type="button"
                  onClick={handleApplyFilters}
                  className="rounded-lg bg-primary-600 px-3 py-1.5 text-xs font-semibold text-white shadow hover:bg-primary-700"
                >
                  นำไปใช้
                </button>
              </div>
            }
          >
            <div className="space-y-4 text-sm text-gray-600">
              <div className="grid gap-3">
                <label className="text-xs font-semibold text-gray-500">วันที่เริ่มต้น</label>
                <input
                  type="date"
                  value={formState.start}
                  onChange={(event) => handleFilterChange('start', event.target.value)}
                  className="rounded-lg border border-gray-200 px-3 py-2 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
                />
              </div>
              <div className="grid gap-3">
                <label className="text-xs font-semibold text-gray-500">วันที่สิ้นสุด</label>
                <input
                  type="date"
                  value={formState.end}
                  onChange={(event) => handleFilterChange('end', event.target.value)}
                  className="rounded-lg border border-gray-200 px-3 py-2 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
                />
              </div>
              <div className="grid gap-3">
                <label className="text-xs font-semibold text-gray-500">หน่วยงาน</label>
                <select
                  value={formState.department}
                  onChange={(event) => handleFilterChange('department', event.target.value)}
                  className="rounded-lg border border-gray-200 px-3 py-2 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
                >
                  <option value="">ทั้งหมด</option>
                  {data?.customReportOptions.departments.map((department) => (
                    <option key={department} value={department}>
                      {department}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid gap-3">
                <label className="text-xs font-semibold text-gray-500">ประเภทยานพาหนะ</label>
                <select
                  value={formState.vehicleType}
                  onChange={(event) => handleFilterChange('vehicleType', event.target.value)}
                  className="rounded-lg border border-gray-200 px-3 py-2 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
                >
                  <option value="">ทั้งหมด</option>
                  {data?.customReportOptions.vehicleTypes.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <p className="text-xs font-semibold text-gray-500">เลือกรายชื่อคนขับ</p>
                <div className="grid gap-2">
                  {data?.customReportOptions.drivers.map((driver) => {
                    const checked = formState.drivers.includes(driver.id);
                    return (
                      <label key={driver.id} className="flex items-center gap-2 text-xs">
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => handleFilterChange('drivers', driver.id)}
                          className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                        />
                        <span>{driver.name}</span>
                      </label>
                    );
                  })}
                  {data && data.customReportOptions.drivers.length === 0 && (
                    <p className="text-xs text-gray-400">ยังไม่มีข้อมูลคนขับในระบบ</p>
                  )}
                </div>
              </div>
              <div className="rounded-xl border border-dashed border-gray-200 bg-white/70 p-3 text-xs text-gray-500">
                <p className="font-semibold text-gray-700">ตัวกรองที่ใช้งาน:</p>
                <p className="mt-1 text-gray-600">{appliedFilterSummary}</p>
              </div>
              <button
                type="button"
                onClick={() => fetchReports(appliedFilters)}
                className="inline-flex w-full items-center justify-center gap-2 rounded-lg border border-primary-200 bg-white/70 px-3 py-1.5 text-xs font-semibold text-primary-600 hover:bg-primary-50"
              >
                <RefreshCcw className="h-3.5 w-3.5" /> โหลดข้อมูลล่าสุด
              </button>
              {error && <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-600">{error}</p>}
              {loading && <p className="text-xs text-gray-500">กำลังโหลดข้อมูล...</p>}
            </div>
          </SectionCard>

          <div className="space-y-6">
            <SectionCard
              title="อัตราการใช้งานยานพาหนะ"
              description="ติดตามการใช้รถแต่ละคัน พร้อมระบุชั่วโมงปฏิบัติงานและความหนาแน่น"
              icon={Gauge}
            >
              {data ? (
                <div className="grid gap-6 lg:grid-cols-2">
                  <HorizontalBarChart
                    data={data.vehicleUtilisation.map((item) => ({
                      label: `${item.registration_number} (${item.vehicle_type})`,
                      value: item.utilisation_rate,
                      hint: `${item.total_trips} งาน • ${item.total_hours.toFixed(1)} ชม. • ${item.current_mileage.toLocaleString()} กม.`,
                    }))}
                  />
                  <div className="space-y-3 rounded-2xl border border-gray-100 bg-white/80 p-5 shadow-sm">
                    <h3 className="text-sm font-semibold text-gray-800">สรุปเชิงลึก</h3>
                    <ul className="space-y-2 text-xs text-gray-600">
                      <li className="flex items-start gap-2"><Sparkles className="mt-0.5 h-3.5 w-3.5 text-primary-500" />
                        รถ {data.vehicleUtilisation[0]?.registration_number ?? '—'} มีการใช้งานสูงสุด {data.vehicleUtilisation[0]?.utilisation_rate.toFixed(1) ?? '0'}%</li>
                      <li className="flex items-start gap-2"><LineChart className="mt-0.5 h-3.5 w-3.5 text-emerald-500" />
                        ค่าเฉลี่ยระยะเวลาต่อทริป {data.vehicleUtilisation.length > 0 ? (data.vehicleUtilisation.reduce((sum, item) => sum + item.average_trip_duration_hours, 0) / data.vehicleUtilisation.length).toFixed(1) : '0'} ชั่วโมง</li>
                      <li className="flex items-start gap-2"><Factory className="mt-0.5 h-3.5 w-3.5 text-amber-500" />
                        มี {data.vehicleUtilisation.filter((item) => item.utilisation_rate < 40).length} คันที่ต้องติดตามเพิ่มเพื่อเพิ่มอัตราการใช้งาน</li>
                    </ul>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-gray-500">ยังไม่มีข้อมูล</p>
              )}
            </SectionCard>

            <SectionCard
              title="รายงานการใช้งานรายเดือนตามหน่วยงาน"
              description="ดูจำนวนคำขอและผู้โดยสารเพื่อวางแผนทรัพยากร"
              icon={CalendarClock}
            >
              {data && monthlyAggregation.length > 0 ? (
                <div className="grid gap-6 lg:grid-cols-[260px_1fr]">
                  <SimpleColumnChart data={monthlyAggregation.slice(-5)} />
                  <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white/70 shadow-sm">
                    <table className="min-w-full divide-y divide-gray-100 text-left text-xs">
                      <thead className="bg-primary-50 text-gray-600">
                        <tr>
                          <th className="px-4 py-2 font-semibold">เดือน</th>
                          <th className="px-4 py-2 font-semibold">หน่วยงาน</th>
                          <th className="px-4 py-2 font-semibold">คำขอ</th>
                          <th className="px-4 py-2 font-semibold">เสร็จสมบูรณ์</th>
                          <th className="px-4 py-2 font-semibold">ผู้โดยสาร</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100 bg-white/70">
                        {data.departmentUsage.map((item) => (
                          <tr key={`${item.period}-${item.department}`} className="hover:bg-primary-50/40">
                            <td className="px-4 py-2 text-gray-700">{item.periodLabel}</td>
                            <td className="px-4 py-2 text-gray-700">{item.department}</td>
                            <td className="px-4 py-2 text-gray-600">{item.total_requests.toLocaleString('th-TH')}</td>
                            <td className="px-4 py-2 text-gray-600">{item.completed_trips.toLocaleString('th-TH')}</td>
                            <td className="px-4 py-2 text-gray-600">{item.total_passengers.toLocaleString('th-TH')}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-gray-500">ยังไม่มีข้อมูลคำขอในช่วงที่เลือก</p>
              )}
            </SectionCard>

            <SectionCard
              title="ประสิทธิภาพและภาระงานของคนขับ"
              description="ระบุคนขับที่มีภาระงานสูงและค่าเฉลี่ยเวลาปฏิบัติงาน"
              icon={Users2}
            >
              {data && data.driverPerformance.length > 0 ? (
                <div className="space-y-4">
                  {data.driverPerformance.map((driver) => {
                    const completionRate = driver.assignments === 0 ? 0 : (driver.completed_jobs / driver.assignments) * 100;
                    return (
                      <div key={driver.driver_id} className="rounded-2xl border border-gray-100 bg-white/70 p-4 shadow-sm">
                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <div>
                            <p className="text-sm font-semibold text-gray-900">{driver.full_name}</p>
                            <p className="text-xs text-gray-500">{driver.assignments.toLocaleString('th-TH')} งาน • {driver.total_hours.toFixed(1)} ชั่วโมง</p>
                          </div>
                          <TrendPill label="อัตราสำเร็จ" value={`${completionRate.toFixed(1)}%`} />
                        </div>
                        <div className="mt-3 h-2.5 overflow-hidden rounded-full bg-gray-100">
                          <div className="h-full rounded-full bg-emerald-500" style={{ width: `${Math.min(100, completionRate)}%` }} />
                        </div>
                        <p className="mt-2 text-xs text-gray-500">เฉลี่ย {driver.average_completion_time_hours.toFixed(1)} ชม./งาน • ดัชนีภาระงาน {driver.workload_index.toFixed(1)}%</p>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-xs text-gray-500">ยังไม่มีข้อมูลการปฏิบัติงานของคนขับ</p>
              )}
            </SectionCard>

            <SectionCard
              title="การติดตามค่าใช้จ่าย"
              description="สรุปค่าใช้จ่ายตามสถานะการอนุมัติและค่าเฉลี่ยต่อทริป"
              icon={Fuel}
            >
              {data ? (
                <div className="grid gap-5 lg:grid-cols-[300px_1fr]">
                  <div className="rounded-2xl border border-gray-100 bg-white/80 p-4 shadow-sm">
                    <h3 className="text-sm font-semibold text-gray-800">สถานะค่าใช้จ่าย</h3>
                    <StackedProgressBar data={expenseStacked} />
                    <div className="mt-4 space-y-2 text-xs text-gray-600">
                      {data.expenseSummary.statusBreakdown.map((entry) => (
                        <div key={entry.status} className="flex items-center justify-between rounded-lg border border-gray-100 bg-white/70 px-3 py-2">
                          <span className="font-medium text-gray-700">{entry.status}</span>
                          <span>{formatCurrency(entry.totalExpenses)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="rounded-2xl border border-gray-100 bg-white/80 p-4 shadow-sm">
                      <p className="text-xs font-semibold text-gray-500">ค่าใช้จ่ายเฉลี่ยต่อทริป</p>
                      <p className="mt-2 text-xl font-bold text-gray-900">{formatCurrency(data.expenseSummary.averageTotalExpense)}</p>
                      <p className="mt-1 text-xs text-gray-500">จากทั้งหมด {data.expenseSummary.totalJobs.toLocaleString('th-TH')} งาน</p>
                    </div>
                    <div className="rounded-2xl border border-gray-100 bg-white/80 p-4 shadow-sm">
                      <p className="text-xs font-semibold text-gray-500">ค่าเชื้อเพลิงรวม</p>
                      <p className="mt-2 text-xl font-bold text-gray-900">{formatCurrency(data.expenseSummary.totalFuelCost)}</p>
                      <p className="mt-1 text-xs text-gray-500">รวมค่าทางด่วน {formatCurrency(data.expenseSummary.totalTollCost)} และอื่น ๆ {formatCurrency(data.expenseSummary.totalOtherExpenses)}</p>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-gray-500">ไม่มีข้อมูลค่าใช้จ่าย</p>
              )}
            </SectionCard>

            <SectionCard
              title="การบำรุงรักษาเชิงคาดการณ์"
              description="วิเคราะห์ความเสี่ยงและแนะนำการวางแผนงานบำรุงรักษา"
              icon={Sparkles}
            >
              {data && data.predictiveMaintenance.length > 0 ? (
                <div className="grid gap-4 md:grid-cols-2">
                  {data.predictiveMaintenance.map((item) => (
                    <div key={item.vehicle_id} className="rounded-2xl border border-gray-100 bg-gradient-to-br from-white/90 to-primary-50/60 p-4 shadow-sm">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-semibold text-gray-900">{item.registration_number}</p>
                          <p className="text-xs text-gray-500">ประเภท {item.vehicle_type}</p>
                        </div>
                        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-100 text-sm font-bold text-primary-700">
                          {item.risk_score.toFixed(0)}%
                        </div>
                      </div>
                      <p className="mt-3 text-xs text-gray-600">{item.recommended_action}</p>
                      <p className="mt-2 text-xs font-semibold text-primary-600">ควรดำเนินการก่อน: {item.projectedServiceLabel}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-gray-500">ยังไม่มีความเสี่ยงที่ต้องติดตามเป็นพิเศษ</p>
              )}
            </SectionCard>

            <SectionCard
              title="การวิเคราะห์รูปแบบการจอง"
              description="ดูแนวโน้มวันที่มีการใช้งานสูงและช่วงเวลาที่ได้รับความนิยม"
              icon={Activity}
            >
              {data && data.bookingPatterns.length > 0 ? (
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-3 rounded-2xl border border-gray-100 bg-white/80 p-4 shadow-sm">
                    <h3 className="text-sm font-semibold text-gray-800">รูปแบบตามวัน</h3>
                    <ul className="space-y-2 text-xs text-gray-600">
                      {data.bookingPatterns.map((pattern) => (
                        <li key={pattern.weekday_index} className="flex items-center justify-between rounded-lg border border-gray-100 bg-white/70 px-3 py-2">
                          <span className="font-medium text-gray-700">{pattern.day_of_week}</span>
                          <span>{pattern.average_bookings.toFixed(1)} งาน/วัน</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="rounded-2xl border border-gray-100 bg-white/80 p-4 shadow-sm">
                    <h3 className="text-sm font-semibold text-gray-800">คำแนะนำในการจัดการ</h3>
                    <ul className="space-y-2 text-xs text-gray-600">
                      <li className="flex items-start gap-2"><TrendingUp className="mt-0.5 h-3.5 w-3.5 text-primary-500" />
                        จัดเพิ่มรถสำรองในช่วง {Math.round(data.bookingPatterns[0].peak_hour).toString().padStart(2, '0')}:00 น. ของวันยอดนิยม</li>
                      <li className="flex items-start gap-2"><LineChart className="mt-0.5 h-3.5 w-3.5 text-emerald-500" />
                        พิจารณาควบรวมคำขอที่มีจำนวนผู้โดยสารน้อยกว่า 3 คนในวันอัตราใช้งานต่ำ</li>
                      <li className="flex items-start gap-2"><Activity className="mt-0.5 h-3.5 w-3.5 text-amber-500" />
                        ใช้ข้อมูลนี้เพื่อแจ้งเตือนผู้อนุมัติให้เตรียมพร้อมในช่วงเวลาที่มีคำขอหนาแน่น</li>
                    </ul>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-gray-500">ยังไม่มีข้อมูลรูปแบบการจอง</p>
              )}
            </SectionCard>

            <SectionCard
              title="คำแนะนำการปรับค่าใช้จ่าย"
              description="ข้อเสนอเพื่อเพิ่มประสิทธิภาพการใช้งบประมาณ"
              icon={TrendingUp}
            >
              {data && data.costRecommendations.length > 0 ? (
                <div className="grid gap-4 md:grid-cols-2">
                  {data.costRecommendations.map((item) => (
                    <div key={item.label} className="rounded-2xl border border-gray-100 bg-gradient-to-br from-emerald-50/80 to-white/80 p-4 shadow-sm">
                      <p className="text-sm font-semibold text-gray-900">{item.label}</p>
                      <p className="mt-2 text-xs text-gray-600">{item.detail}</p>
                      <p className="mt-3 inline-flex rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
                        ศักยภาพในการประหยัด {formatCurrency(item.potential_saving)} ต่อทริป
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-gray-500">ยังไม่มีคำแนะนำเพิ่มเติม</p>
              )}
            </SectionCard>

            <SectionCard
              title="สรุปรายงานแบบกำหนดเอง"
              description="สรุปผลลัพธ์จากตัวกรองที่เลือกไว้"
              icon={BarChart3}
            >
              {data ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-2xl border border-gray-100 bg-white/80 p-4 shadow-sm">
                    <p className="text-xs font-semibold text-gray-500">คำขอที่อยู่ในช่วง</p>
                    <p className="mt-2 text-xl font-bold text-gray-900">{data.customReportSummary.totalBookings.toLocaleString('th-TH')}</p>
                    <p className="mt-1 text-xs text-gray-500">เสร็จสมบูรณ์ {data.customReportSummary.totalCompleted.toLocaleString('th-TH')} งาน</p>
                  </div>
                  <div className="rounded-2xl border border-gray-100 bg-white/80 p-4 shadow-sm">
                    <p className="text-xs font-semibold text-gray-500">ค่าใช้จ่ายรวม</p>
                    <p className="mt-2 text-xl font-bold text-gray-900">{formatCurrency(data.customReportSummary.totalExpenses)}</p>
                    <p className="mt-1 text-xs text-gray-500">เฉลี่ย {data.customReportSummary.averageBookingHours.toFixed(1)} ชม./งาน</p>
                  </div>
                  <div className="rounded-2xl border border-gray-100 bg-white/80 p-4 shadow-sm sm:col-span-2">
                    <p className="text-xs font-semibold text-gray-500">รายละเอียดตัวกรองที่ใช้</p>
                    <pre className="mt-2 whitespace-pre-wrap text-xs text-gray-600">
                      {JSON.stringify(data.customReportSummary.filters, null, 2) || 'ไม่พบตัวกรอง'}
                    </pre>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-gray-500">ยังไม่มีข้อมูลสรุป</p>
              )}
            </SectionCard>
          </div>
        </div>
      </div>
    </div>
  );
}
