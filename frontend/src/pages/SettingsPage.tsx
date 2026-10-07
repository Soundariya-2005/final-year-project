import React, { useState, useEffect } from 'react';
import {
  Sliders,
  Database,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Save,
  Server,
  Lock,
  Terminal,
} from 'lucide-react';
import {
  fetchSettings,
  updateSettings,
  fetchDatabaseStatus,
  SettingsResponse,
  DatabaseStatusResponse,
} from '../services/api';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorMessage } from '../components/common/ErrorMessage';

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<SettingsResponse | null>(null);
  const [dbStatus, setDbStatus] = useState<DatabaseStatusResponse | null>(null);

  const [alpha, setAlpha] = useState<number>(0.15);
  const [contamination, setContamination] = useState<number>(0.07);
  const [riskDecay, setRiskDecay] = useState<number>(0.88);
  const [riskGain, setRiskGain] = useState<number>(0.13);

  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [sData, dData] = await Promise.all([
        fetchSettings(),
        fetchDatabaseStatus(),
      ]);
      setSettings(sData);
      setDbStatus(dData);
      setAlpha(sData.parameters.alpha);
      setContamination(sData.parameters.contamination);
      setRiskDecay(sData.parameters.risk_decay);
      setRiskGain(sData.parameters.risk_gain);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load system settings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSave = async () => {
    try {
      setSaving(true);
      setSavedSuccess(false);
      setError(null);
      await updateSettings({
        alpha,
        contamination,
        risk_decay: riskDecay,
        risk_gain: riskGain,
      });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 4000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <LoadingState message="Loading system configuration and database telemetry..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <Sliders className="w-5 h-5 text-cyan-400" />
          System Settings &amp; Engine Hyper-Parameters
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Tune adaptive learning rates, unsupervised anomaly contamination bounds, progressive risk temporal gains, and MySQL storage.
        </p>
      </div>

      {error && <ErrorMessage message={error} />}

      {savedSuccess && (
        <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10 text-emerald-300 flex items-center gap-2 text-xs">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>Hyper-parameters successfully updated! Pipeline automatically re-evaluated.</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ML & Risk Engine Parameters */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 shadow-sm space-y-6">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Sliders className="w-4 h-4 text-cyan-400" />
            Detection &amp; Risk Parameters
          </h3>

          <div className="space-y-4 text-xs">
            {/* Alpha */}
            <div className="space-y-1.5 p-3 rounded-lg bg-slate-950/60 border border-slate-800">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-200">
                  Adaptive Profile Alpha (&alpha;): <span className="text-cyan-400 font-mono">{alpha}</span>
                </span>
                <span className="text-[10px] text-slate-500 font-mono">Default: 0.15</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.50"
                step="0.01"
                value={alpha}
                onChange={(e) => setAlpha(parseFloat(e.target.value))}
                className="w-full accent-cyan-500 cursor-pointer"
              />
              <p className="text-[11px] text-slate-400">
                Formula: <code className="text-slate-300">b(t) = (1 - &alpha;)&times;b(t-1) + &alpha;&times;x(t)</code>. Higher &alpha; adapts faster to changing user habits; lower &alpha; resists poisoning.
              </p>
            </div>

            {/* Contamination */}
            <div className="space-y-1.5 p-3 rounded-lg bg-slate-950/60 border border-slate-800">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-200">
                  Isolation Forest Contamination: <span className="text-cyan-400 font-mono">{(contamination * 100).toFixed(0)}%</span>
                </span>
                <span className="text-[10px] text-slate-500 font-mono">Default: 0.07</span>
              </div>
              <input
                type="range"
                min="0.01"
                max="0.20"
                step="0.01"
                value={contamination}
                onChange={(e) => setContamination(parseFloat(e.target.value))}
                className="w-full accent-cyan-500 cursor-pointer"
              />
              <p className="text-[11px] text-slate-400">
                Expected proportion of outliers in the behavioral dataset. Controls threshold boundary for isolation trees.
              </p>
            </div>

            {/* Risk Decay */}
            <div className="space-y-1.5 p-3 rounded-lg bg-slate-950/60 border border-slate-800">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-200">
                  Progressive Risk Decay (&lambda;): <span className="text-cyan-400 font-mono">{riskDecay}</span>
                </span>
                <span className="text-[10px] text-slate-500 font-mono">Default: 0.88</span>
              </div>
              <input
                type="range"
                min="0.50"
                max="0.99"
                step="0.01"
                value={riskDecay}
                onChange={(e) => setRiskDecay(parseFloat(e.target.value))}
                className="w-full accent-cyan-500 cursor-pointer"
              />
              <p className="text-[11px] text-slate-400">
                Determines how swiftly previous risk attenuates when a user exhibits standard behavior.
              </p>
            </div>

            {/* Risk Gain */}
            <div className="space-y-1.5 p-3 rounded-lg bg-slate-950/60 border border-slate-800">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-200">
                  Progressive Risk Gain (&eta;): <span className="text-cyan-400 font-mono">{riskGain}</span>
                </span>
                <span className="text-[10px] text-slate-500 font-mono">Default: 0.13</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.40"
                step="0.01"
                value={riskGain}
                onChange={(e) => setRiskGain(parseFloat(e.target.value))}
                className="w-full accent-cyan-500 cursor-pointer"
              />
              <p className="text-[11px] text-slate-400">
                Controls the amplification rate applied when an anomaly event is confirmed by the Isolation Forest.
              </p>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-5 py-2.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-semibold text-xs transition flex items-center gap-2 cursor-pointer shadow-md shadow-cyan-500/20"
            >
              <Save className="w-3.5 h-3.5" />
              {saving ? 'Updating & Re-Running...' : 'Save & Re-execute Pipeline'}
            </button>
          </div>
        </div>

        {/* Database Diagnostic & Connection Guide */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 shadow-sm space-y-6">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Database className="w-4 h-4 text-cyan-400" />
            MySQL Database Connection Diagnostic
          </h3>

          {dbStatus && (
            <div className="space-y-4 text-xs font-mono">
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Connectivity Status:</span>
                  <span
                    className={`px-2 py-0.5 rounded font-bold ${
                      dbStatus.connected
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : 'bg-amber-500/20 text-amber-400'
                    }`}
                  >
                    {dbStatus.connected ? 'ONLINE (CONNECTED)' : 'OFFLINE (IN-MEMORY CACHE ACTIVE)'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-400">
                  <span>Host / Port:</span>
                  <span className="text-slate-200">
                    {dbStatus.connection_details.host}:{dbStatus.connection_details.port}
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-400">
                  <span>Target Database:</span>
                  <span className="text-slate-200">{dbStatus.connection_details.database}</span>
                </div>
                <div className="flex items-center justify-between text-slate-400">
                  <span>Database User:</span>
                  <span className="text-slate-200">{dbStatus.connection_details.user}</span>
                </div>
              </div>

              {/* Defined Models List */}
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
                <span className="text-slate-400 font-sans font-semibold block">
                  Registered SQLAlchemy Schemas (8 Models):
                </span>
                <div className="flex flex-wrap gap-1.5 font-mono text-[10px]">
                  {dbStatus.schema_tables_defined.map((t) => (
                    <span
                      key={t}
                      className="px-2 py-1 rounded bg-slate-900 border border-slate-800 text-cyan-400"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>

              {/* Environment Variable Template Guide */}
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1 font-sans text-xs">
                <span className="font-semibold text-slate-300 block">External MySQL Setup:</span>
                <p className="text-slate-400 text-[11px]">
                  To connect an external MySQL service, populate <code>.env</code> with:
                </p>
                <div className="p-2 rounded bg-slate-900 font-mono text-[10px] text-slate-300 space-y-0.5 border border-slate-800">
                  <div>DB_HOST=localhost</div>
                  <div>DB_PORT=3306</div>
                  <div>DB_NAME=insider_threat_db</div>
                  <div>DB_USER=root</div>
                  <div>DB_PASSWORD=your_secure_password</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
