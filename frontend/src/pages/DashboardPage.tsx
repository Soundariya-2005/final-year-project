import React, { useState, useEffect } from 'react';
import {
  Users,
  Database,
  AlertTriangle,
  ShieldAlert,
  Activity,
  RefreshCw,
  TrendingUp,
  BrainCircuit,
  Sliders,
  ExternalLink,
} from 'lucide-react';
import {
  fetchDashboardSummary,
  fetchUsersList,
  DashboardSummaryResponse,
  UserSummaryItem,
} from '../services/api';
import { SummaryCard } from '../components/common/SummaryCard';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { ProgressiveRiskTrendChart } from '../components/charts/ProgressiveRiskTrendChart';
import { RiskDistributionChart } from '../components/charts/RiskDistributionChart';
import { UsersRankedByRiskChart } from '../components/charts/UsersRankedByRiskChart';
import { AnomalyTrendChart } from '../components/charts/AnomalyTrendChart';
import { ShapContributingFactorsChart } from '../components/charts/ShapContributingFactorsChart';

interface DashboardPageProps {
  onNavigate: (page: string, params?: Record<string, any>) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigate }) => {
  const [summary, setSummary] = useState<DashboardSummaryResponse | null>(null);
  const [rankedUsers, setRankedUsers] = useState<UserSummaryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [sumData, usersData] = await Promise.all([
        fetchDashboardSummary(),
        fetchUsersList(),
      ]);
      setSummary(sumData);
      setRankedUsers(usersData.users || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return <LoadingState message="Connecting to Threat Detection Engine..." subMessage="Loading progressive risk models, isolation forest scores, and SHAP feature attributions" />;
  }

  if (error || !summary) {
    return <ErrorMessage message={error || 'Dashboard data unavailable'} onRetry={loadData} />;
  }

  return (
    <div className="space-y-6">
      {/* Executive Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-xl bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/40 border border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-mono uppercase tracking-wider text-cyan-400">
              Live Telemetry &bull; Privacy-Preserved Monitoring
            </span>
          </div>
          <h2 className="text-xl font-bold text-slate-100 mt-1">
            Cybersecurity Threat Intelligence Dashboard
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Observing {summary.total_users} pseudonymous users across {summary.date_range.start} to {summary.date_range.end} with adaptive EWMA baselines and Isolation Forest
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => onNavigate('upload')}
            className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 transition flex items-center gap-1.5 cursor-pointer"
          >
            <Activity className="w-3.5 h-3.5" />
            Upload New Logs
          </button>
          <button
            onClick={loadData}
            className="p-1.5 rounded-lg border border-slate-800 bg-slate-900/80 hover:bg-slate-800 text-slate-300 transition cursor-pointer"
            title="Refresh Metrics"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 4 Primary Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          title="Total Users"
          value={summary.total_users}
          subtitle="Pseudonymized employee entities"
          icon={Users}
          badge="Masked IDs"
          badgeColor="cyan"
        />
        <SummaryCard
          title="Activity Records"
          value={summary.activity_records}
          subtitle="User-day feature vectors"
          icon={Database}
          badge={`${summary.daily_trend.length} Days`}
          badgeColor="indigo"
        />
        <SummaryCard
          title="High Risk Users"
          value={summary.high_risk_users}
          subtitle="Threshold: 50.0 - 74.9"
          icon={AlertTriangle}
          badge="High Tier"
          badgeColor="amber"
        />
        <SummaryCard
          title="Critical Risk Users"
          value={summary.critical_risk_users}
          subtitle="Threshold: 75.0 - 100.0"
          icon={ShieldAlert}
          badge="Immediate Triage"
          badgeColor="rose"
        />
      </div>

      {/* Primary Visualizations: Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Progressive Risk Score Trend */}
        <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-semibold text-slate-200">
                1. Progressive Risk Score Trend
              </h3>
            </div>
            <span className="text-xs text-slate-400 font-mono">
              risk(t) = decay &times; risk(t-1) + gain &times; anomaly(t)
            </span>
          </div>
          <p className="text-xs text-slate-400 mb-4">
            Tracks cumulative temporal risk accumulation. Single isolated anomalies decay smoothly; repeated anomalous activities compound exponentially.
          </p>
          <ProgressiveRiskTrendChart data={summary.daily_trend} height={260} />
        </div>

        {/* Risk-Level Distribution */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              <h3 className="text-sm font-semibold text-slate-200">
                2. Risk-Level Distribution
              </h3>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              Current organization-wide classification into LOW (0-24), MEDIUM (25-49), HIGH (50-74), and CRITICAL (75-100).
            </p>
            <RiskDistributionChart distribution={summary.risk_level_distribution} height={230} />
          </div>

          <div className="mt-4 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
            <span>Critical Users Flagged:</span>
            <span className="font-mono font-bold text-rose-400">{summary.critical_risk_users}</span>
          </div>
        </div>
      </div>

      {/* Primary Visualizations: Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Users Ranked by Risk */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-amber-400" />
              <h3 className="text-sm font-semibold text-slate-200">
                3. Users Ranked by Risk
              </h3>
            </div>
            <button
              onClick={() => onNavigate('users')}
              className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 cursor-pointer"
            >
              View All <ExternalLink className="w-3 h-3" />
            </button>
          </div>
          <p className="text-xs text-slate-400 mb-3">
            Top anomalous entities prioritized by final progressive risk score.
          </p>
          <UsersRankedByRiskChart users={rankedUsers} height={240} maxUsers={6} />
        </div>

        {/* Anomaly Trend */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-rose-400" />
              <h3 className="text-sm font-semibold text-slate-200">
                4. Anomaly Trend
              </h3>
            </div>
            <span className="text-xs font-mono text-slate-400">
              {summary.total_anomalies} total outliers
            </span>
          </div>
          <p className="text-xs text-slate-400 mb-3">
            Daily count of Isolation Forest unsupervised outliers (contamination = {(summary.parameters.contamination * 100).toFixed(0)}%).
          </p>
          <AnomalyTrendChart data={summary.daily_trend} height={240} />
        </div>

        {/* Top Contributing Factors */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <BrainCircuit className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-semibold text-slate-200">
                5. Top Contributing Factors
              </h3>
            </div>
            <button
              onClick={() => onNavigate('analysis')}
              className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 cursor-pointer"
            >
              Deep Dive <ExternalLink className="w-3 h-3" />
            </button>
          </div>
          <p className="text-xs text-slate-400 mb-3">
            Global SHAP feature attribution across all anomalous behaviors.
          </p>
          <ShapContributingFactorsChart factors={summary.top_contributing_factors} height={240} />
        </div>
      </div>

      {/* Critical Quick Alerts Bar */}
      {summary.critical_risk_users > 0 && (
        <div className="p-4 rounded-xl border border-rose-500/40 bg-rose-500/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-rose-500/20 text-rose-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-rose-200">
                {summary.critical_risk_users} Critical Insider Threat Incidents Detected
              </h4>
              <p className="text-xs text-rose-300/80">
                Sustained abnormal behavior observed (data exfiltration, after-hours privilege abuse, sensitive file harvesting).
              </p>
            </div>
          </div>
          <button
            onClick={() => onNavigate('alerts')}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-rose-500 hover:bg-rose-600 text-white shadow-sm transition flex items-center gap-1.5 cursor-pointer shrink-0"
          >
            Review Security Alerts
          </button>
        </div>
      )}
    </div>
  );
};
