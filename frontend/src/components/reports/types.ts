export interface RawVehicleUtilisation {
  vehicle_id: number;
  registration_number: string;
  vehicle_type: string;
  total_trips: number;
  total_hours: number;
  active_days: number;
  average_trip_duration_hours: number;
  utilisation_rate: number;
  current_mileage: number;
}

export interface RawDepartmentUsage {
  period: string;
  department: string;
  total_requests: number;
  completed_trips: number;
  total_passengers: number;
  total_hours: number;
}

export interface RawDriverPerformance {
  driver_id: number;
  full_name: string;
  assignments: number;
  completed_jobs: number;
  total_hours: number;
  average_completion_time_hours: number;
  workload_index: number;
}

export interface RawPredictiveMaintenance {
  vehicle_id: number;
  registration_number: string;
  vehicle_type: string;
  risk_score: number;
  recommended_action: string;
  projected_service_date: string;
}

export interface RawBookingPattern {
  day_of_week: string;
  weekday_index: number;
  average_bookings: number;
  peak_hour: number;
  average_passengers: number;
}

export interface RawCostRecommendation {
  label: string;
  detail: string;
  potential_saving: number;
}

export interface RawExpenseStatusEntry {
  status: string;
  count: number;
  total_expenses: string | number;
}

export interface RawExpenseAnalytics {
  generated_at: string;
  total_jobs: number;
  total_fuel_cost: string | number;
  total_toll_cost: string | number;
  total_other_expenses: string | number;
  total_expenses: string | number;
  average_fuel_cost: string | number;
  average_total_expense: string | number;
  status_breakdown: RawExpenseStatusEntry[];
}

export interface RawCustomReportSummary {
  total_bookings: number;
  total_completed: number;
  total_expenses: number;
  average_booking_hours: number;
  filters: Record<string, unknown>;
}

export interface RawCustomReportOptions {
  departments: string[];
  vehicle_types: string[];
  drivers: { id: number; name: string }[];
}

export interface RawReportOverview {
  generated_at: string;
  timeframe_start: string | null;
  timeframe_end: string | null;
  vehicle_utilisation: RawVehicleUtilisation[];
  department_usage: RawDepartmentUsage[];
  driver_performance: RawDriverPerformance[];
  expense_summary: RawExpenseAnalytics;
  predictive_maintenance: RawPredictiveMaintenance[];
  booking_patterns: RawBookingPattern[];
  cost_recommendations: RawCostRecommendation[];
  custom_report_summary: RawCustomReportSummary;
  custom_report_options: RawCustomReportOptions;
}

export interface VehicleUtilisation extends RawVehicleUtilisation {}
export interface DepartmentUsage extends RawDepartmentUsage {
  periodLabel: string;
}
export interface DriverPerformance extends RawDriverPerformance {}
export interface PredictiveMaintenance extends RawPredictiveMaintenance {
  projectedServiceLabel: string;
}
export interface BookingPattern extends RawBookingPattern {}
export interface CostRecommendation extends RawCostRecommendation {}

export interface ExpenseStatusEntry {
  status: string;
  count: number;
  totalExpenses: number;
}

export interface ExpenseAnalytics {
  generatedAt: string;
  totalJobs: number;
  totalFuelCost: number;
  totalTollCost: number;
  totalOtherExpenses: number;
  totalExpenses: number;
  averageFuelCost: number;
  averageTotalExpense: number;
  statusBreakdown: ExpenseStatusEntry[];
}

export interface CustomReportSummary {
  totalBookings: number;
  totalCompleted: number;
  totalExpenses: number;
  averageBookingHours: number;
  filters: Record<string, unknown>;
}

export interface CustomReportOptions {
  departments: string[];
  vehicleTypes: string[];
  drivers: { id: number; name: string }[];
}

export interface ReportOverview {
  generatedAt: string;
  timeframeStart: string | null;
  timeframeEnd: string | null;
  vehicleUtilisation: VehicleUtilisation[];
  departmentUsage: DepartmentUsage[];
  driverPerformance: DriverPerformance[];
  expenseSummary: ExpenseAnalytics;
  predictiveMaintenance: PredictiveMaintenance[];
  bookingPatterns: BookingPattern[];
  costRecommendations: CostRecommendation[];
  customReportSummary: CustomReportSummary;
  customReportOptions: CustomReportOptions;
}
