import React from 'react';
import { LucideIcon } from 'lucide-react';

interface SummaryCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  badge?: string;
  badgeColor?: 'emerald' | 'amber' | 'rose' | 'indigo' | 'cyan';
  trend?: {
    label: string;
    positive?: boolean;
  };
}

export const SummaryCard: React.FC<SummaryCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  badge,
  badgeColor = 'cyan',
}) => {
  const badgeStyles = {
    emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    amber: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    rose: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    indigo: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
    cyan: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
  }[badgeColor];

  const iconBg = {
    emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    rose: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    indigo: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
    cyan: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  }[badgeColor];

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">
          {title}
        </span>
        <div className={`p-2 rounded-lg border ${iconBg}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>

      <div className="flex items-baseline justify-between">
        <div className="text-2xl font-bold font-mono text-slate-100 tracking-tight">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </div>
        {badge && (
          <span className={`text-xs px-2 py-0.5 rounded border font-mono ${badgeStyles}`}>
            {badge}
          </span>
        )}
      </div>

      {subtitle && (
        <p className="mt-2 text-xs text-slate-400 leading-relaxed truncate">
          {subtitle}
        </p>
      )}
    </div>
  );
};
