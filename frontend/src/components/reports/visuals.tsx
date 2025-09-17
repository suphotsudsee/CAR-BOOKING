"use client";

import clsx from 'clsx';

interface HorizontalBarDatum {
  label: string;
  value: number;
  hint?: string;
  accent?: 'primary' | 'emerald' | 'amber' | 'rose' | 'slate';
}

const accentMap: Record<NonNullable<HorizontalBarDatum['accent']>, string> = {
  primary: 'bg-primary-500',
  emerald: 'bg-emerald-500',
  amber: 'bg-amber-400',
  rose: 'bg-rose-500',
  slate: 'bg-slate-500',
};

export function HorizontalBarChart({
  data,
  maxValue = 100,
  unit = '%',
}: {
  data: HorizontalBarDatum[];
  maxValue?: number;
  unit?: string;
}) {
  return (
    <div className="space-y-4">
      {data.map((item) => {
        const width = Math.max(2, Math.min(100, (item.value / maxValue) * 100));
        const accent = accentMap[item.accent ?? 'primary'];
        return (
          <div key={item.label}>
            <div className="flex items-center justify-between text-xs font-medium text-gray-600">
              <span>{item.label}</span>
              <span className="text-gray-800">{item.value.toFixed(1)}{unit}</span>
            </div>
            <div className="mt-1 h-2.5 rounded-full bg-gray-100">
              <div
                className={clsx('h-2.5 rounded-full transition-all duration-500', accent)}
                style={{ width: `${width}%` }}
              />
            </div>
            {item.hint && <p className="mt-1 text-[11px] text-gray-500">{item.hint}</p>}
          </div>
        );
      })}
    </div>
  );
}

interface ColumnChartDatum {
  label: string;
  value: number;
  detail?: string;
}

export function SimpleColumnChart({ data, maxValue }: { data: ColumnChartDatum[]; maxValue?: number }) {
  const computedMax = maxValue ?? Math.max(...data.map((item) => item.value), 1);
  return (
    <div className="flex items-end gap-4">
      {data.map((item) => {
        const height = Math.round((item.value / computedMax) * 160);
        return (
          <div key={item.label} className="flex flex-col items-center text-xs text-gray-600">
            <div className="flex h-40 w-10 items-end justify-center rounded-t-lg bg-gradient-to-t from-primary-100 to-primary-400/70">
              <div className="w-7 rounded-t-lg bg-primary-500 shadow-md" style={{ height: `${height}px` }} />
            </div>
            <span className="mt-2 font-medium">{item.label}</span>
            {item.detail && <span className="text-[11px] text-gray-500">{item.detail}</span>}
          </div>
        );
      })}
    </div>
  );
}

interface StackedBarDatum {
  label: string;
  segments: { value: number; accent: 'primary' | 'emerald' | 'amber' | 'rose' | 'violet' | 'slate'; }[];
  total: number;
}

const stackedAccentMap: Record<StackedBarDatum['segments'][number]['accent'], string> = {
  primary: 'bg-primary-500',
  emerald: 'bg-emerald-500',
  amber: 'bg-amber-400',
  rose: 'bg-rose-500',
  violet: 'bg-violet-500',
  slate: 'bg-slate-400',
};

export function StackedProgressBar({ data }: { data: StackedBarDatum[] }) {
  return (
    <div className="space-y-4">
      {data.map((item) => (
        <div key={item.label}>
          <div className="flex items-center justify-between text-xs font-medium text-gray-600">
            <span>{item.label}</span>
            <span className="text-gray-800">รวม {item.total.toLocaleString()} บาท</span>
          </div>
          <div className="mt-1 flex h-3 overflow-hidden rounded-full bg-gray-100 shadow-inner">
            {item.segments.map((segment, index) => {
              const width = item.total === 0 ? 0 : Math.max(2, (segment.value / item.total) * 100);
              return (
                <div
                  key={`${item.label}-${index}`}
                  className={clsx('h-full transition-all duration-500', stackedAccentMap[segment.accent])}
                  style={{ width: `${width}%` }}
                />
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

export function TrendPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-primary-200 bg-primary-50 px-3 py-1 text-xs font-medium text-primary-600">
      <span className="inline-flex h-1.5 w-1.5 rounded-full bg-primary-500" />
      <span>{label}: {value}</span>
    </div>
  );
}
