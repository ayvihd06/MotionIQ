import React from 'react';
import { HelpCircle, AlertTriangle, RefreshCw } from 'lucide-react';

// ── StatusBadge ───────────────────────────────────────────────────────────────
interface StatusBadgeProps {
  label: string;
  variant?: 'emerald' | 'amber' | 'rose' | 'cyan' | 'indigo' | 'slate';
  size?: 'xs' | 'sm';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  label,
  variant = 'slate',
  size = 'xs'
}) => {
  const colorMap = {
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
    rose: 'bg-rose-50 text-rose-700 border-rose-200',
    cyan: 'bg-cyan-50 text-cyan-700 border-cyan-200',
    indigo: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    slate: 'bg-slate-100 text-slate-700 border-slate-200'
  };

  const sizeClass = size === 'xs' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs';

  return (
    <span className={`inline-flex items-center font-mono font-medium rounded-md border ${colorMap[variant]} ${sizeClass}`}>
      {label}
    </span>
  );
};

// ── MotionCard ────────────────────────────────────────────────────────────────
interface MotionCardProps {
  children: React.ReactNode;
  className?: string;
  glow?: boolean;
}

export const MotionCard: React.FC<MotionCardProps> = ({
  children,
  className = '',
  glow = false
}) => {
  const baseClass = glow ? 'motion-card-elevated' : 'motion-card';
  return (
    <div className={`${baseClass} ${className}`}>
      {children}
    </div>
  );
};

// ── MetricCard ────────────────────────────────────────────────────────────────
interface MetricCardProps {
  name: string;
  value: string | number;
  unit?: string;
  trend?: React.ReactNode;
  confidence?: string;
  description?: string;
  limitations?: string;
  status?: string;
  statusVariant?: 'emerald' | 'amber' | 'rose' | 'cyan' | 'indigo' | 'slate';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  name,
  value,
  unit = '',
  trend,
  confidence,
  description,
  limitations,
  status,
  statusVariant = 'slate'
}) => {
  return (
    <MotionCard className="space-y-3 flex flex-col justify-between">
      <div className="space-y-2">
        <div className="flex justify-between items-start">
          <span className="text-[11px] font-mono uppercase tracking-wider text-slate-500 font-semibold">
            {name}
          </span>
          <div className="flex items-center gap-1.5">
            {status && <StatusBadge label={status} variant={statusVariant} />}
            {confidence && (
              <span className="text-[10px] font-mono bg-slate-50 border border-slate-200 text-slate-600 px-1.5 py-0.5 rounded">
                {confidence}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-baseline gap-1.5">
          <span className="text-3xl font-bold text-slate-900 font-mono tracking-tight">
            {value}
          </span>
          {unit && (
            <span className="text-xs font-semibold text-cyan-700 font-mono">
              {unit}
            </span>
          )}
          {trend && <span className="ml-2">{trend}</span>}
        </div>

        {description && (
          <p className="text-xs text-slate-600 leading-relaxed pt-0.5">
            {description}
          </p>
        )}
      </div>

      {limitations && (
        <div className="text-[11px] text-slate-400 italic pt-2 border-t border-slate-100 leading-snug">
          Caveat: {limitations}
        </div>
      )}
    </MotionCard>
  );
};

// ── SectionHeader ─────────────────────────────────────────────────────────────
interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  badge?: string;
  badgeVariant?: 'emerald' | 'amber' | 'rose' | 'cyan' | 'indigo' | 'slate';
  action?: React.ReactNode;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({
  title,
  subtitle,
  badge,
  badgeVariant = 'cyan',
  action
}) => {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          {badge && <StatusBadge label={badge} variant={badgeVariant} />}
          <h2 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">{title}</h2>
        </div>
        {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
};

// ── PageHeader ────────────────────────────────────────────────────────────────
interface PageHeaderProps {
  title: string;
  description?: string;
  breadcrumb?: React.ReactNode;
  action?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  breadcrumb,
  action
}) => {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5 mb-8">
      <div className="space-y-1.5">
        {breadcrumb && <div className="text-xs text-slate-500">{breadcrumb}</div>}
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">{title}</h1>
        {description && <p className="text-sm text-slate-600">{description}</p>}
      </div>
      {action && <div className="shrink-0 self-start sm:self-auto">{action}</div>}
    </div>
  );
};

// ── EmptyState ────────────────────────────────────────────────────────────────
interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  actionLabel,
  onAction,
  icon
}) => {
  return (
    <MotionCard className="py-12 px-6 text-center space-y-4 max-w-lg mx-auto border border-dashed border-slate-200">
      <div className="w-12 h-12 rounded-xl bg-slate-100 border border-slate-200 flex items-center justify-center mx-auto text-slate-500">
        {icon || <HelpCircle className="w-6 h-6" />}
      </div>
      <div className="space-y-1">
        <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">{title}</h3>
        <p className="text-xs text-slate-500 max-w-sm mx-auto leading-relaxed">{description}</p>
      </div>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="motion-btn-primary text-xs"
        >
          {actionLabel}
        </button>
      )}
    </MotionCard>
  );
};

// ── ErrorState ────────────────────────────────────────────────────────────────
interface ErrorStateProps {
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title,
  message,
  actionLabel = 'Try Again',
  onAction
}) => {
  return (
    <div className="max-w-md mx-auto p-5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs text-center space-y-4">
      <AlertTriangle className="w-8 h-8 text-rose-500 mx-auto" />
      <div className="space-y-1">
        <h4 className="font-bold text-slate-900 text-sm">{title}</h4>
        <p className="leading-relaxed">{message}</p>
      </div>
      {onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2 bg-rose-100 hover:bg-rose-200 text-rose-800 border border-rose-300 rounded-lg font-semibold transition-all cursor-pointer"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
};

// ── LoadingState ──────────────────────────────────────────────────────────────
interface LoadingStateProps {
  message?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading data...'
}) => {
  return (
    <div className="max-w-md mx-auto py-12 text-center space-y-3">
      <RefreshCw className="w-6 h-6 text-cyan-600 animate-spin mx-auto" />
      <p className="text-xs font-mono text-slate-500">{message}</p>
    </div>
  );
};
