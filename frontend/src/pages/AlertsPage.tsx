import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle,
  Eye,
  RefreshCw,
  Search,
  Calendar,
  HardDrive,
  FileWarning,
  Clock,
  ArrowRight,
} from 'lucide-react';
import { fetchAlerts, AlertsResponse, AlertItem } from '../services/api';
import { RiskBadge } from '../components/common/RiskBadge';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorMessage } from '../components/common/ErrorMessage';

interface AlertsPageProps {
  onNavigate: (page: string, params?: Record<string, any>) => void;
}

export const AlertsPage: React.FC<AlertsPageProps> = ({ onNavigate }) => {
  const [alertsData, setAlertsData] = useState<AlertsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [filterTier, setFilterTier] = useState<'ALL' | 'CRITICAL' | 'HIGH'>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const loadAlerts = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetchAlerts();
      setAlertsData(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load security alerts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  const filteredAlerts = (alertsData?.alerts || []).filter((a) => {
    const matchesTier = filterTier === 'ALL' || a.risk_level === filterTier;
    const matchesSearch =
      !searchTerm ||
      a.pseudonymous_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.primary_threat_vector.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesTier && matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            Active Threat &amp; Early Warning Alerts
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time insider threat alerts triaged from high and critical risk progressive scores.
          </p>
        </div>

        <button
          onClick={loadAlerts}
          className="p-2 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-300 transition flex items-center gap-1.5 text-xs font-semibold cursor-pointer self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh Alerts
        </button>
      </div>

      {error && <ErrorMessage message={error} onRetry={loadAlerts} />}

      {/* Metrics Banner */}
      {alertsData && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                Total High/Critical Alerts
              </span>
              <span className="text-2xl font-bold font-mono text-slate-100 mt-1 block">
                {alertsData.total_alerts}
              </span>
            </div>
            <div className="p-2.5 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <ShieldAlert className="w-5 h-5" />
            </div>
          </div>

          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-rose-300 uppercase tracking-wider block">
                Critical Severity (Score &ge; 75.0)
              </span>
              <span className="text-2xl font-bold font-mono text-rose-400 mt-1 block">
                {alertsData.critical_count}
              </span>
            </div>
            <div className="p-2.5 rounded-lg bg-rose-500/20 text-rose-300">
              <ShieldAlert className="w-5 h-5" />
            </div>
          </div>

          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-amber-300 uppercase tracking-wider block">
                High Severity (Score 50.0 - 74.9)
              </span>
              <span className="text-2xl font-bold font-mono text-amber-400 mt-1 block">
                {alertsData.high_count}
              </span>
            </div>
            <div className="p-2.5 rounded-lg bg-amber-500/20 text-amber-300">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>
        </div>
      )}

      {/* Search & Tier Filters */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3 rounded-xl bg-slate-900/40 border border-slate-800">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Filter by user ID or threat vector..."
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-sans"
          />
        </div>

        <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 p-1 rounded-lg text-xs font-mono self-start sm:self-auto">
          {(['ALL', 'CRITICAL', 'HIGH'] as const).map((tier) => (
            <button
              key={tier}
              onClick={() => setFilterTier(tier)}
              className={`px-3 py-1 rounded-md transition cursor-pointer ${
                filterTier === tier
                  ? 'bg-slate-800 text-cyan-400 font-bold border border-slate-700'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {tier}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <LoadingState message="Triaging active insider threat alerts..." />
      ) : filteredAlerts.length === 0 ? (
        <div className="p-12 text-center rounded-xl bg-slate-900/40 border border-slate-800">
          <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
          <h4 className="text-sm font-semibold text-slate-200">No Active Threats Matching Filter</h4>
          <p className="text-xs text-slate-400 mt-1">
            All user entities currently maintain risk trajectories within normal or low thresholds.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredAlerts.map((alert) => (
            <div
              key={alert.alert_id}
              className={`rounded-xl border p-5 space-y-4 transition hover:border-slate-700 ${
                alert.risk_level === 'CRITICAL'
                  ? 'bg-slate-900/80 border-rose-500/40 shadow-sm shadow-rose-950/30'
                  : 'bg-slate-900/80 border-amber-500/40 shadow-sm shadow-amber-950/30'
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[10px] font-mono text-slate-500 block">
                    {alert.alert_id}
                  </span>
                  <h3 className="text-base font-bold font-mono text-slate-100 mt-0.5">
                    {alert.pseudonymous_id}
                  </h3>
                </div>
                <RiskBadge level={alert.risk_level} score={alert.risk_score} size="md" />
              </div>

              {/* Threat Vector Tag */}
              <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-1">
                <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-400 block">
                  Primary Threat Driver (SHAP Attribution)
                </span>
                <span className="font-mono font-bold text-rose-400 block">
                  {alert.primary_threat_vector.replace(/_/g, ' ')}
                </span>
              </div>

              {/* Behavioral Indicators */}
              <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                <div className="p-2 rounded bg-slate-950/80 border border-slate-800/80 text-center">
                  <span className="text-[10px] text-slate-500 block truncate">Upload Vol</span>
                  <span className="font-bold text-slate-200">{alert.recent_upload_volume_mb} MB</span>
                </div>
                <div className="p-2 rounded bg-slate-950/80 border border-slate-800/80 text-center">
                  <span className="text-[10px] text-slate-500 block truncate">Sens. Files</span>
                  <span className="font-bold text-slate-200">{alert.recent_sensitive_files}</span>
                </div>
                <div className="p-2 rounded bg-slate-950/80 border border-slate-800/80 text-center">
                  <span className="text-[10px] text-slate-500 block truncate">Late Logins</span>
                  <span className="font-bold text-slate-200">{alert.recent_after_hours_logins}</span>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
                <span className="text-slate-400">
                  {alert.anomalous_days_count} anomalous days
                </span>
                <button
                  onClick={() => onNavigate('users', { userId: alert.pseudonymous_id })}
                  className="px-3 py-1.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 transition flex items-center gap-1 font-medium cursor-pointer"
                >
                  <Eye className="w-3.5 h-3.5" />
                  Investigate
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
