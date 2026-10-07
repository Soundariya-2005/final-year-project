import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Brain,
  Sliders,
  Calendar,
  Activity,
  Layers,
  ArrowRight,
  ShieldAlert,
  Info,
} from 'lucide-react';
import {
  fetchUsersList,
  fetchUserRiskTrend,
  fetchUserShapExplanations,
  UserSummaryItem,
  UserRiskTrendResponse,
  UserShapExplanationResponse,
} from '../services/api';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { RiskBadge } from '../components/common/RiskBadge';
import { ShapContributingFactorsChart } from '../components/charts/ShapContributingFactorsChart';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';

export const RiskAnalysisPage: React.FC = () => {
  const [users, setUsers] = useState<UserSummaryItem[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<string>('');
  const [riskTrend, setRiskTrend] = useState<UserRiskTrendResponse | null>(null);
  const [shapExplanations, setShapExplanations] = useState<UserShapExplanationResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [trendLoading, setTrendLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function init() {
      try {
        setLoading(true);
        const usersRes = await fetchUsersList();
        setUsers(usersRes.users || []);
        if (usersRes.users && usersRes.users.length > 0) {
          // Select highest risk user by default (e.g. USR-1012 or USR-1025)
          const firstUser = usersRes.users[0].pseudonymous_id;
          setSelectedUserId(firstUser);
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to load risk analysis data');
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  useEffect(() => {
    if (!selectedUserId) return;
    async function loadUserAnalysis() {
      try {
        setTrendLoading(true);
        const [trendRes, shapRes] = await Promise.all([
          fetchUserRiskTrend(selectedUserId),
          fetchUserShapExplanations(selectedUserId),
        ]);
        setRiskTrend(trendRes);
        setShapExplanations(shapRes);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to load user timeline');
      } finally {
        setTrendLoading(false);
      }
    }
    loadUserAnalysis();
  }, [selectedUserId]);

  if (loading) {
    return <LoadingState message="Loading risk analysis environment..." />;
  }

  const selectedUserMeta = users.find((u) => u.pseudonymous_id === selectedUserId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-cyan-400" />
            Adaptive Profiling &amp; Progressive Risk Engine
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Demonstrates EWMA baseline tracking, deviation quantification, and multi-day temporal risk accumulation.
          </p>
        </div>

        {/* User Picker Dropdown */}
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 p-2 rounded-xl">
          <span className="text-xs font-semibold text-slate-400">Target User:</span>
          <select
            value={selectedUserId}
            onChange={(e) => setSelectedUserId(e.target.value)}
            className="bg-slate-950 border border-slate-700 text-cyan-400 font-mono text-xs rounded-lg px-2.5 py-1 focus:outline-none focus:border-cyan-500 cursor-pointer"
          >
            {users.map((u) => (
              <option key={u.pseudonymous_id} value={u.pseudonymous_id}>
                {u.pseudonymous_id} &mdash; [{u.latest_risk_level}] ({u.latest_risk_score.toFixed(1)})
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <ErrorMessage message={error} />}

      {/* Mathematical Principles Architecture Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs space-y-1">
          <span className="text-cyan-400 font-bold uppercase tracking-wider text-[10px] block">
            1. Adaptive Profiling (EWMA)
          </span>
          <div className="font-mono text-slate-200 bg-slate-950 p-2 rounded border border-slate-800">
            b(t) = (1 - &alpha;)&times;b(t-1) + &alpha;&times;x(t)
          </div>
          <p className="text-slate-400 text-[11px] mt-1">
            Builds dynamic personalized baseline per feature. Dampens baseline poisoning while learning authentic behavioral shifts.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs space-y-1">
          <span className="text-rose-400 font-bold uppercase tracking-wider text-[10px] block">
            2. Progressive Risk Accumulation
          </span>
          <div className="font-mono text-slate-200 bg-slate-950 p-2 rounded border border-slate-800">
            risk(t) = decay&times;risk(t-1) + gain&times;anomaly(t)
          </div>
          <p className="text-slate-400 text-[11px] mt-1">
            Normal days cause risk to decay towards zero (&lambda; = 0.88). Sustained anomalous acts accumulate exponentially (&eta; = 0.13).
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs space-y-1">
          <span className="text-amber-400 font-bold uppercase tracking-wider text-[10px] block">
            3. Game-Theoretic SHAP XAI
          </span>
          <div className="font-mono text-slate-200 bg-slate-950 p-2 rounded border border-slate-800">
            &phi;_i = &sum; [f(S &cup; &#123;i&#125;) - f(S)] / (|F|! / |S|!(|F|-|S|-1)!)
          </div>
          <p className="text-slate-400 text-[11px] mt-1">
            TreeExplainer quantifies exact feature attribution. Isolates whether web upload or after-hours login drove the anomaly.
          </p>
        </div>
      </div>

      {trendLoading ? (
        <LoadingState message={`Calculating temporal trajectory for ${selectedUserId}...`} />
      ) : riskTrend && (
        <div className="space-y-6">
          {/* Main Risk Trajectory Chart */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-cyan-400" />
                  Day-by-Day Risk Progression for {selectedUserId}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Visualizes how behavioral outliers trigger progressive spikes and how normal days decay risk.
                </p>
              </div>

              {selectedUserMeta && (
                <div className="flex items-center gap-2">
                  <RiskBadge
                    level={selectedUserMeta.latest_risk_level}
                    score={selectedUserMeta.latest_risk_score}
                    size="lg"
                  />
                </div>
              )}
            </div>

            <div style={{ width: '100%', height: 300 }}>
              <ResponsiveContainer>
                <LineChart
                  data={riskTrend.trend}
                  margin={{ top: 10, right: 20, left: -10, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis
                    dataKey="date"
                    stroke="#64748b"
                    fontSize={11}
                    tickFormatter={(d) => (d.length > 5 ? d.slice(5) : d)}
                    tickLine={false}
                  />
                  <YAxis
                    stroke="#64748b"
                    fontSize={11}
                    domain={[0, 100]}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '8px',
                      fontSize: '12px',
                      color: '#f8fafc',
                    }}
                    formatter={(val: any, name: any) => [
                      name === 'risk_score' ? `${Number(val).toFixed(1)} / 100` : val,
                      name === 'risk_score' ? 'Progressive Risk' : 'Anomalous Incident',
                    ]}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                  <Line
                    type="monotone"
                    dataKey="risk_score"
                    name="Progressive Risk Score"
                    stroke="#f43f5e"
                    strokeWidth={2.5}
                    dot={(props: any) => {
                      const { cx, cy, payload } = props;
                      if (payload.anomaly_flag) {
                        return (
                          <circle
                            key={`anom-${cx}-${cy}`}
                            cx={cx}
                            cy={cy}
                            r={4.5}
                            fill="#f43f5e"
                            stroke="#fff"
                            strokeWidth={1.5}
                          />
                        );
                      }
                      return null;
                    }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* User Specific SHAP Waterfall */}
          {shapExplanations && (
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
                <Brain className="w-4 h-4 text-cyan-400" />
                SHAP Behavioral Attribution Factors for {selectedUserId}
              </h3>
              <ShapContributingFactorsChart
                factors={shapExplanations.explanation.top_features_overall}
                title="Primary Behavioral Dimensions Deviating from Baseline"
                height={240}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
};
