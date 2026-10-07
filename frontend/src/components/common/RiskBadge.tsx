import React from 'react';
import { ShieldAlert, AlertTriangle, AlertCircle, CheckCircle } from 'lucide-react';

export type RiskTier = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;

interface RiskBadgeProps {
  level: RiskTier;
  score?: number;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({
  level,
  score,
  size = 'md',
  showIcon = true,
}) => {
  const normLevel = (level || 'LOW').toUpperCase();

  const getStyles = () => {
    switch (normLevel) {
      case 'CRITICAL':
        return {
          bg: 'bg-rose-500/15 border-rose-500/40 text-rose-400',
          dot: 'bg-rose-400',
          icon: ShieldAlert,
          label: 'CRITICAL',
        };
      case 'HIGH':
        return {
          bg: 'bg-amber-500/15 border-amber-500/40 text-amber-400',
          dot: 'bg-amber-400',
          icon: AlertTriangle,
          label: 'HIGH',
        };
      case 'MEDIUM':
        return {
          bg: 'bg-yellow-500/15 border-yellow-500/40 text-yellow-400',
          dot: 'bg-yellow-400',
          icon: AlertCircle,
          label: 'MEDIUM',
        };
      case 'LOW':
      default:
        return {
          bg: 'bg-emerald-500/15 border-emerald-500/40 text-emerald-400',
          dot: 'bg-emerald-400',
          icon: CheckCircle,
          label: 'LOW',
        };
    }
  };

  const config = getStyles();
  const IconComponent = config.icon;

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-xs font-semibold px-2.5 py-1 gap-1.5',
    lg: 'text-sm font-semibold px-3 py-1.5 gap-2',
  }[size];

  return (
    <span
      className={`inline-flex items-center rounded-md border font-mono tracking-wide ${config.bg} ${sizeClasses}`}
    >
      {showIcon && <IconComponent className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />}
      <span>{config.label}</span>
      {score !== undefined && (
        <span className="opacity-80 font-normal">({score.toFixed(1)})</span>
      )}
    </span>
  );
};
