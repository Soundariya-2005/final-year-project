import React, { useState } from 'react';
import {
  UploadCloud,
  FileText,
  Play,
  CheckCircle2,
  Clock,
  Database,
  ShieldCheck,
  Brain,
  Sliders,
  AlertCircle,
  TrendingUp,
} from 'lucide-react';
import { executePipeline, PipelineRunResponse } from '../services/api';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorMessage } from '../components/common/ErrorMessage';

interface UploadLogsPageProps {
  onNavigate: (page: string, params?: Record<string, any>) => void;
}

export const UploadLogsPage: React.FC<UploadLogsPageProps> = ({ onNavigate }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [alpha, setAlpha] = useState<number>(0.15);
  const [contamination, setContamination] = useState<number>(0.07);
  const [riskDecay, setRiskDecay] = useState<number>(0.88);
  const [riskGain, setRiskGain] = useState<number>(0.13);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PipelineRunResponse | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleRunPipeline = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await executePipeline(selectedFile || undefined, {
        alpha,
        contamination,
        risk_decay: riskDecay,
        risk_gain: riskGain,
      });
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Analysis pipeline failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-100">
          Upload Activity Logs & Run Unified Pipeline
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Executes the complete 11-stage pipeline: CSV validation &rarr; pseudonymization &rarr; behavioral feature engineering &rarr; EWMA profiling &rarr; Isolation Forest &rarr; progressive risk &rarr; SHAP explainability &rarr; database persistence.
        </p>
      </div>

      {error && <ErrorMessage message={error} />}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload & Parameter Configuration Form */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <UploadCloud className="w-4 h-4 text-cyan-400" />
              1. Select Activity Log CSV File
            </h3>

            <div className="border-2 border-dashed border-slate-800 hover:border-cyan-500/50 rounded-xl p-8 text-center transition bg-slate-950/40">
              <input
                type="file"
                accept=".csv"
                id="file-upload"
                onChange={handleFileChange}
                className="hidden"
              />
              <label
                htmlFor="file-upload"
                className="flex flex-col items-center justify-center cursor-pointer"
              >
                <FileText className="w-10 h-10 text-cyan-400/80 mb-3" />
                <span className="text-xs font-semibold text-slate-200">
                  {selectedFile ? selectedFile.name : 'Click to select CSV or drop file here'}
                </span>
                <span className="text-[11px] text-slate-500 mt-1">
                  Accepts user activity logs with user IDs, timestamps, logins, file access, and upload volume.
                </span>
              </label>

              {selectedFile && (
                <div className="mt-4 flex items-center justify-center gap-2 text-xs text-cyan-400">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Selected file: <strong>{selectedFile.name}</strong> ({(selectedFile.size / 1024).toFixed(1)} KB)</span>
                </div>
              )}
            </div>

            <p className="text-[11px] text-slate-400 mt-3">
              * Note: If no custom file is selected, the system automatically uses the verified <strong>40-user / 45-day demonstration dataset</strong> (1,800 records).
            </p>
          </div>

          {/* Hyper-Parameter Settings */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-cyan-400" />
              2. Pipeline Hyper-Parameters
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="text-slate-300 font-medium block mb-1">
                  EWMA Profile Alpha (&alpha;): {alpha}
                </label>
                <input
                  type="range"
                  min="0.05"
                  max="0.50"
                  step="0.01"
                  value={alpha}
                  onChange={(e) => setAlpha(parseFloat(e.target.value))}
                  className="w-full accent-cyan-500 cursor-pointer"
                />
                <span className="text-[10px] text-slate-500">Default: 0.15 (Adaptive learning rate)</span>
              </div>

              <div>
                <label className="text-slate-300 font-medium block mb-1">
                  Isolation Forest Contamination: {(contamination * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  min="0.01"
                  max="0.20"
                  step="0.01"
                  value={contamination}
                  onChange={(e) => setContamination(parseFloat(e.target.value))}
                  className="w-full accent-cyan-500 cursor-pointer"
                />
                <span className="text-[10px] text-slate-500">Default: 0.07 (Expected outlier ratio)</span>
              </div>

              <div>
                <label className="text-slate-300 font-medium block mb-1">
                  Progressive Risk Decay: {riskDecay}
                </label>
                <input
                  type="range"
                  min="0.50"
                  max="0.99"
                  step="0.01"
                  value={riskDecay}
                  onChange={(e) => setRiskDecay(parseFloat(e.target.value))}
                  className="w-full accent-cyan-500 cursor-pointer"
                />
                <span className="text-[10px] text-slate-500">Default: 0.88 (Memory retention over time)</span>
              </div>

              <div>
                <label className="text-slate-300 font-medium block mb-1">
                  Risk Gain Rate: {riskGain}
                </label>
                <input
                  type="range"
                  min="0.05"
                  max="0.40"
                  step="0.01"
                  value={riskGain}
                  onChange={(e) => setRiskGain(parseFloat(e.target.value))}
                  className="w-full accent-cyan-500 cursor-pointer"
                />
                <span className="text-[10px] text-slate-500">Default: 0.13 (Anomaly accumulation speed)</span>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between">
              <span className="text-xs text-slate-400">
                Data minimization &amp; deterministic SHA-256 masking applied automatically.
              </span>
              <button
                onClick={handleRunPipeline}
                disabled={loading}
                className="px-5 py-2.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-semibold text-xs transition flex items-center gap-2 cursor-pointer shadow-md shadow-cyan-500/20"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                {loading ? 'Executing Pipeline...' : 'Run Analysis Pipeline'}
              </button>
            </div>
          </div>
        </div>

        {/* Pipeline Architecture Stages Panel */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Brain className="w-4 h-4 text-cyan-400" />
            11-Stage Pipeline Flow
          </h3>

          <div className="space-y-2 text-xs">
            {[
              { num: '01', name: 'CSV Upload & Validation', desc: 'Checks headers, nulls, and date parsing' },
              { num: '02', name: 'Data Preprocessing', desc: 'Cleaning, normalization & chronological sorting' },
              { num: '03', name: 'Pseudonymization', desc: 'Deterministic SHA-256 identity masking' },
              { num: '04', name: 'Feature Engineering', desc: '8 behavioral metrics aggregated per user-day' },
              { num: '05', name: 'Adaptive Profiling', desc: 'EWMA dynamic baseline: (1-a)*b(t-1) + a*x(t)' },
              { num: '06', name: 'Isolation Forest', desc: 'Unsupervised tree ensemble anomaly scores' },
              { num: '07', name: 'Progressive Risk', desc: 'Temporal accumulation: decay*risk + gain*anomaly' },
              { num: '08', name: 'Risk Classification', desc: 'Tier assignment (LOW, MEDIUM, HIGH, CRITICAL)' },
              { num: '09', name: 'SHAP Explainability', desc: 'TreeExplainer additive feature attributions' },
              { num: '10', name: 'MySQL Storage', desc: 'Saves run metadata, scores, and explanations' },
              { num: '11', name: 'API Response', desc: 'Sanitized JSON delivery with zero identity leaks' },
            ].map((step, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2.5 p-2 rounded-lg bg-slate-950/40 border border-slate-800/60"
              >
                <span className="font-mono text-cyan-400 font-bold shrink-0">{step.num}</span>
                <div>
                  <div className="font-medium text-slate-200">{step.name}</div>
                  <div className="text-[10px] text-slate-500">{step.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Pipeline Execution Results Modal/Card */}
      {loading && (
        <LoadingState
          message="Running 11-Stage Threat Detection Pipeline..."
          subMessage="Executing feature engineering, training Isolation Forest, evaluating progressive risk, and generating SHAP values..."
        />
      )}

      {result && !loading && (
        <div className="p-6 rounded-xl bg-slate-900 border border-cyan-500/40 space-y-4 shadow-lg">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <h3 className="text-base font-bold text-slate-100">
                Pipeline Run Complete &mdash; {result.analysis_run_id}
              </h3>
            </div>
            <span className="text-xs px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-mono">
              STATUS: {result.analysis_status.toUpperCase()}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-slate-500 block">Total Records</span>
              <span className="text-lg font-bold text-slate-200">{result.number_of_records}</span>
            </div>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-slate-500 block">Analyzed Users</span>
              <span className="text-lg font-bold text-slate-200">{result.number_of_users}</span>
            </div>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-slate-500 block">Outlier Anomalies</span>
              <span className="text-lg font-bold text-rose-400">{result.number_of_anomalies}</span>
            </div>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-slate-500 block">Critical Tiers</span>
              <span className="text-lg font-bold text-rose-400">{result.critical_risk_user_count}</span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 text-xs text-slate-400">
            <div>
              <span>Date Range: </span>
              <strong className="text-slate-200 font-mono">
                {result.date_range.start} &rarr; {result.date_range.end}
              </strong>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => onNavigate('dashboard')}
                className="px-3.5 py-1.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 transition cursor-pointer"
              >
                View Dashboard
              </button>
              <button
                onClick={() => onNavigate('alerts')}
                className="px-3.5 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 transition cursor-pointer"
              >
                Inspect Critical Alerts
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
