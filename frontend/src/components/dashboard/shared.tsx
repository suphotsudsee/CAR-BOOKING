"use client";

import Link from 'next/link';
import { ComponentProps, ReactNode } from 'react';

import clsx from 'clsx';
import { type LucideIcon } from 'lucide-react';

const accentMap = {
  primary: 'from-primary-500/10 to-primary-500/5 text-primary-600',
  emerald: 'from-emerald-500/10 to-emerald-500/5 text-emerald-600',
  amber: 'from-amber-500/10 to-amber-500/5 text-amber-600',
  sky: 'from-sky-500/10 to-sky-500/5 text-sky-600',
  violet: 'from-violet-500/10 to-violet-500/5 text-violet-600',
  rose: 'from-rose-500/10 to-rose-500/5 text-rose-600',
} as const;

type AccentKey = keyof typeof accentMap;

export interface StatCardProps {
  label: string;
  value: string;
  icon: LucideIcon;
  accent?: AccentKey;
  trend?: {
    value: string;
    description?: string;
    direction: 'up' | 'down' | 'steady';
  };
}

export function StatCard({ label, value, icon: Icon, accent = 'primary', trend }: StatCardProps) {
  const accentClass = accentMap[accent] ?? accentMap.primary;

  return (
    <div className="flex flex-col justify-between rounded-2xl border border-gray-200 bg-white/80 p-5 shadow-sm backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <span
          className={clsx(
            'inline-flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br',
            accentClass,
            'shadow-inner shadow-white/30',
          )}
        >
          <Icon className="h-6 w-6" />
        </span>
        <div>
          <p className="text-sm font-medium text-gray-500">{label}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
        </div>
      </div>
      {trend && (
        <p
          className={clsx(
            'mt-4 inline-flex items-center text-xs font-medium',
            trend.direction === 'down'
              ? 'text-rose-600'
              : trend.direction === 'up'
                ? 'text-emerald-600'
                : 'text-gray-500',
          )}
        >
          <span>{trend.value}</span>
          {trend.description && <span className="ml-1 text-gray-500">{trend.description}</span>}
        </p>
      )}
    </div>
  );
}

export interface QuickActionButtonProps {
  label: string;
  description?: string;
  icon: LucideIcon;
  tone?: AccentKey;
  href?: string;
  onClick?: () => void;
  disabled?: boolean;
}

export function QuickActionButton({
  label,
  description,
  icon: Icon,
  tone = 'primary',
  href,
  onClick,
  disabled,
}: QuickActionButtonProps) {
  const content = (
    <div
      className={clsx(
        'group flex h-full flex-col justify-between gap-3 rounded-xl border border-gray-200 bg-white/70 p-4 text-left shadow-sm transition-all hover:-translate-y-1 hover:shadow-lg',
        disabled && 'pointer-events-none opacity-60',
      )}
    >
      <span
        className={clsx(
          'inline-flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br text-sm font-semibold',
          accentMap[tone] ?? accentMap.primary,
        )}
      >
        <Icon className="h-5 w-5" />
      </span>
      <div className="space-y-1">
        <p className="text-base font-semibold text-gray-900">{label}</p>
        {description && <p className="text-sm text-gray-500">{description}</p>}
      </div>
      <span className="text-sm font-medium text-primary-600 group-hover:text-primary-700">ดูรายละเอียด</span>
    </div>
  );

  if (href) {
    return (
      <Link href={href} className="block h-full" aria-disabled={disabled} onClick={disabled ? (event) => event.preventDefault() : undefined}>
        {content}
      </Link>
    );
  }

  return (
    <button type="button" className="h-full w-full" onClick={onClick} disabled={disabled}>
      {content}
    </button>
  );
}

export interface SectionCardProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function SectionCard({ title, description, actions, children, className }: SectionCardProps) {
  return (
    <section className={clsx('rounded-2xl border border-gray-200 bg-white/80 p-6 shadow-sm backdrop-blur', className)}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="text-xl font-semibold text-gray-900">{title}</h3>
          {description && <p className="mt-1 text-sm text-gray-500">{description}</p>}
        </div>
        {actions && <div className="flex shrink-0 items-center gap-3">{actions}</div>}
      </div>
      <div className="mt-6 space-y-4 text-sm text-gray-600 sm:space-y-5">{children}</div>
    </section>
  );
}

export function EmptyState({ icon: Icon, title, description }: { icon: LucideIcon; title: string; description: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 bg-white/60 p-10 text-center text-gray-500">
      <Icon className="h-10 w-10 text-gray-400" />
      <p className="mt-4 text-lg font-medium text-gray-700">{title}</p>
      <p className="mt-1 max-w-sm text-sm text-gray-500">{description}</p>
    </div>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const normalised = status.toLowerCase();
  const styles: Record<string, string> = {
    approved: 'bg-emerald-100 text-emerald-700 ring-emerald-500/30',
    pending: 'bg-amber-100 text-amber-700 ring-amber-500/30',
    rejected: 'bg-rose-100 text-rose-700 ring-rose-500/30',
    completed: 'bg-primary-100 text-primary-700 ring-primary-500/30',
    scheduled: 'bg-sky-100 text-sky-700 ring-sky-500/30',
    inprogress: 'bg-sky-100 text-sky-700 ring-sky-500/30',
  };

  const className = styles[normalised.replace(/\s+/g, '')] ?? 'bg-gray-100 text-gray-700 ring-gray-500/20';

  return <span className={clsx('inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ring-1 ring-inset', className)}>{status}</span>;
}

export function TimelineItem({
  title,
  timestamp,
  description,
  status,
  accent = 'primary',
}: {
  title: string;
  timestamp: string;
  description?: string;
  status?: string;
  accent?: AccentKey;
}) {
  return (
    <div className="relative pl-7">
      <span
        className={clsx(
          'absolute left-1 top-1 h-4 w-4 rounded-full border-2 border-white bg-gradient-to-br',
          accentMap[accent] ?? accentMap.primary,
        )}
        aria-hidden
      />
      <div className="rounded-xl border border-gray-100 bg-white/80 p-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="text-sm font-semibold text-gray-900">{title}</p>
            {description && <p className="text-xs text-gray-500">{description}</p>}
          </div>
          <div className="flex items-center gap-3">
            {status && <StatusBadge status={status} />}
            <time className="text-xs text-gray-400">{timestamp}</time>
          </div>
        </div>
      </div>
    </div>
  );
}

export function CardGrid({ className, ...props }: ComponentProps<'div'>) {
  return <div className={clsx('grid gap-4 sm:grid-cols-2 xl:grid-cols-4', className)} {...props} />;
}
