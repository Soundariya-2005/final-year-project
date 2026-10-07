import React, { useState, useEffect } from 'react';
import {
  Users,
  Search,
  Filter,
  Eye,
  TrendingUp,
  BrainCircuit,
  Activity,
  ArrowUpRight,
  Shield,
  X,
  Calendar,
} from 'lucide-react';
import {
  fetchUsersList,
  fetchUserDetail,
  UserSummaryItem,
  UserDetailResponse,
} from '../services/api';
import { RiskBadge } from '../components/common/RiskBadge';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { DataTable, ColumnDef } from '../components/common/DataTable';
import { ProgressiveRiskTrendChart } from '../components/charts/ProgressiveRiskTrendChart';
import { ShapContributingFactorsChart } from '../components/charts/ShapContributingFactorsChart';

interface UsersPageProps {
  onNavigate: (page: string, params?: Record<string, any>) => void;
  initialUserId?: string;
}

export const UsersPage: React.FC<UsersPageProps> = ({ onNavigate, initialUserId }) => {
  const [users, setUsers] = useState<UserSummaryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [levelFilter, setLevelFilter] = useState<string>('ALL');

  // Selected User Modal / Inspection State
  const [selectedUser, setSelectedUser] = useState<UserDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetchUsersList(levelFilter === 'ALL' ? undefined : levelFilter);
      setUsers(res.users || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectUser = async (userId: string) => {
    try {
      setDetailLoading(true);
      setDetailError(null);
      const res = await fetchUserDetail(userId);
      setSelectedUser(res);
    } catch (err: unknown) {
      setDetailError(err instanceof Error ? err.message : 'Failed to fetch user details');
    } finally {
      setDetailLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, [levelFilter]);

  useEffect(() => {
    if (initialUserId) {
      handleSelectUser(initialUserId);
    }
  }, [initialUserId]);

  const columns: ColumnDef<UserSummaryItem>[] = [
    {
      header: 'Pseudonymous ID',
      accessorKey: 'pseudonymous_id',
      cell: (row) => (
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded bg-slate-800 border border-slate-700 flex items-center justify-center font-mono text-[10px] text-cyan-400">
            {row.pseudonymous_id.replace('USR-', '')}
          </div>
          <div>
            <span className="font-mono font-semibold text-slate-100">{row.pseudonymous_id}</span>
            <span className="text-[10px] text-slate-500 block">Deterministic Mask</span>
          </div>
        </div>
      ),
    },
    {
      header: 'Current Risk Level',
      accessorKey: 'latest_risk_level',
      cell: (row) => (
        <RiskBadge level={row.latest_risk_level} score={row.latest_risk_score} size="md" />
      ),
    },
    {
      header: 'Peak Risk',
      accessorKey: 'peak_risk_score',
      cell: (row) => (
        <span className="font-mono text-slate-300">
          {row.peak_risk_score.toFixed(1)} / 100
        </span>
      ),
    },
    {
      header: 'Anomalies',
      accessorKey: 'anomaly_count',
      cell: (row) => (
        <span
          className={`font-mono font-semibold ${
            row.anomaly_count > 10
              ? 'text-rose-400'
              : row.anomaly_count > 0
              ? 'text-amber-400'
              : 'text-slate-400'
          }`}
        >
          {row.anomaly_count} days
        </span>
      ),
    },
    {
      header: 'Avg Web Upload',
      accessorKey: 'avg_web_upload_volume',
      cell: (row) => (
        <span className="font-mono text-slate-400">
          {row.avg_web_upload_volume.toFixed(1)} MB
        </span>
      ),
    },
    {
      header: 'Last Active Date',
      accessorKey: 'last_activity_date',
      cell: (row) => (
        <span className="font-mono text-slate-500">{row.last_activity_date}</span>
      ),
    },
    {
      header: 'Action',
      cell: (row) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            handleSelectUser(row.pseudonymous_id);
          }}
          className="px-2.5 py-1 text-xs font-medium rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 transition flex items-center gap-1 cursor-pointer"
        >
          <Eye className="w-3 h-3" />
          Inspect
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Users className="w-5 h-5 text-cyan-400" />
            Pseudonymous User Entities
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Privacy-preserving insider profiles indexed by deterministic SHA-256 tokens. No real employee PII is stored or presented.
          </p>
        </div>

        {/* Risk Level Filter Chips */}
        <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 p-1 rounded-lg text-xs font-mono">
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setLevelFilter(lvl)}
              className={`px-3 py-1 rounded-md transition cursor-pointer ${
                levelFilter === lvl
                  ? 'bg-slate-800 text-cyan-400 font-bold border border-slate-700'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {lvl}
            </button>
          ))}
        </div>
      </div>

      {error && <ErrorMessage message={error} onRetry={loadUsers} />}

      {loading ? (
        <LoadingState message="Loading analyzed user entities..." />
      ) : (
        <DataTable
          columns={columns}
          data={users}
          searchKey="pseudonymous_id"
          searchPlaceholder="Search pseudonymous ID (e.g. USR-1012)..."
          pageSize={10}
          onRowClick={(row) => handleSelectUser(row.pseudonymous_id)}
        />
      )}

      {/* User Details Inspection Modal */}
      {selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-4xl max-h-[90vh] overflow-y-auto bg-slate-900 border border-slate-700 rounded-2xl p-6 shadow-2xl space-y-6">
            <div className="flex items-start justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center font-mono text-cyan-400 font-bold text-sm">
                  {selectedUser.pseudonymous_id.replace('USR-', '')}
                </div>
                <div>
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-bold text-slate-100 font-mono">
                      {selectedUser.pseudonymous_id}
                    </h3>
                    <RiskBadge
                      level={selectedUser.risk_level}
                      score={selectedUser.current_risk}
                      size="md"
                    />
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Total anomalous days: <strong>{selectedUser.anomaly_count}</strong> &bull; Last Activity: {selectedUser.last_activity_date}
                  </p>
                </div>
              </div>

              <button
                onClick={() => setSelectedUser(null)}
                className="p-2 rounded-lg bg-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-700 transition cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Behavioral Feature Comparison Grid */}
            <div>
              <h4 className="text-xs uppercase font-semibold text-slate-400 tracking-wider mb-2">
                Behavioral Metric Comparison (Average vs Latest Active Day)
              </h4>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                {Object.entries(selectedUser.behavioral_summary.averages).map(([feat, avgVal]) => {
                  const latestVal = selectedUser.behavioral_summary.latest[feat] ?? avgVal;
                  const isElevated = latestVal > avgVal * 1.5 && avgVal > 0;
                  return (
                    <div
                      key={feat}
                      className={`p-3 rounded-lg border bg-slate-950/60 ${
                        isElevated
                          ? 'border-rose-500/40 bg-rose-500/5'
                          : 'border-slate-800'
                      }`}
                    >
                      <span className="text-[10px] text-slate-400 uppercase tracking-wider block truncate">
                        {feat.replace(/_/g, ' ')}
                      </span>
                      <div className="flex items-baseline justify-between mt-1 font-mono">
                        <span className="text-sm font-bold text-slate-200">
                          {latestVal}
                        </span>
                        <span className="text-[10px] text-slate-500">
                          Avg: {avgVal}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* SHAP Feature Contribution Waterfall */}
            <div>
              <h4 className="text-xs uppercase font-semibold text-slate-400 tracking-wider mb-2 flex items-center gap-2">
                <BrainCircuit className="w-4 h-4 text-cyan-400" />
                SHAP Anomaly Drivers for {selectedUser.pseudonymous_id}
              </h4>
              <ShapContributingFactorsChart
                factors={selectedUser.top_shap_factors}
                title="Features Contributing to Threat Classification"
                height={220}
              />
            </div>

            {/* Progressive Risk History Timeline */}
            <div>
              <h4 className="text-xs uppercase font-semibold text-slate-400 tracking-wider mb-2 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-rose-400" />
                Progressive Risk Accumulation Timeline
              </h4>
              <div className="max-h-48 overflow-y-auto border border-slate-800 rounded-lg bg-slate-950/40">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-900 border-b border-slate-800 text-slate-400 sticky top-0">
                    <tr>
                      <th className="p-2.5">Date</th>
                      <th className="p-2.5">Risk Score</th>
                      <th className="p-2.5">Risk Tier</th>
                      <th className="p-2.5">Anomaly Flag</th>
                      <th className="p-2.5">Outlier Score</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {selectedUser.risk_history.map((rh, idx) => (
                      <tr
                        key={idx}
                        className={rh.anomaly_flag ? 'bg-rose-500/5 text-rose-300' : 'text-slate-300'}
                      >
                        <td className="p-2.5">{rh.date}</td>
                        <td className="p-2.5 font-bold">{rh.risk_score.toFixed(1)}</td>
                        <td className="p-2.5">
                          <RiskBadge level={rh.risk_level} size="sm" showIcon={false} />
                        </td>
                        <td className="p-2.5">
                          {rh.anomaly_flag ? (
                            <span className="text-rose-400 font-bold">&bull; ANOMALOUS</span>
                          ) : (
                            <span className="text-slate-500">Normal</span>
                          )}
                        </td>
                        <td className="p-2.5 text-slate-400">{rh.anomaly_score.toFixed(3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setSelectedUser(null)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold cursor-pointer"
              >
                Close Inspection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
