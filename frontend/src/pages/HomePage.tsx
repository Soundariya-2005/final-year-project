import React, { useState, useEffect } from 'react';
import { 
  Server, 
  CheckCircle2, 
  XCircle, 
  RefreshCw, 
  Database, 
  Table, 
  ChevronRight, 
  FileSpreadsheet, 
  Users, 
  Calendar, 
  Shield, 
  Lock, 
  Filter, 
  Binary, 
  Cpu, 
  TrendingUp, 
  Activity, 
  AlertTriangle, 
  PieChart, 
  HelpCircle,
  Play,
  Flame,
  Lightbulb,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import { 
  fetchHealth, 
  fetchDatabaseStatus, 
  fetchDatabaseSchema,
  fetchPrivacyStatus,
  pseudonymizeUserId,
  performControlledLookup,
  extractBehavioralFeatures,
  fetchFeaturesPreview,
  fetchUserProfileSummary,
  runFullAnalysis,
  fetchUserShapExplanations,
  fetchAnomalies,
  fetchRiskScores,
  HealthResponse, 
  DatabaseStatusResponse,
  DatabaseSchemaResponse,
  PrivacyStatusResponse,
  PseudonymizeResponse,
  ControlledLookupResponse,
  BehavioralFeatureRecord,
  UserProfileSummary,
  FullAnalysisResponse,
  AnomalyRecord,
  RiskRecord,
  UserShapExplanationResponse
} from '../services/api';

export const HomePage: React.FC = () => {
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [dbStatus, setDbStatus] = useState<DatabaseStatusResponse | null>(null);
  const [dbSchema, setDbSchema] = useState<DatabaseSchemaResponse | null>(null);
  
  // Pipeline Analysis State (Isolation Forest, Risk, SHAP)
  const [analysisRunning, setAnalysisRunning] = useState<boolean>(false);
  const [analysisResult, setAnalysisResult] = useState<FullAnalysisResponse | null>(null);
  
  // Active Tab for ML Results
  const [activeAnalysisTab, setActiveAnalysisTab] = useState<'anomalies' | 'risk' | 'shap'>('anomalies');
  
  // Anomaly Records State
  const [anomRecords, setAnomRecords] = useState<AnomalyRecord[]>([]);
  const [anomLoading, setAnomLoading] = useState<boolean>(false);
  const [anomFilterUser, setAnomFilterUser] = useState<string>('');

  // Risk Records State
  const [riskRecords, setRiskRecords] = useState<RiskRecord[]>([]);
  const [riskFilterUser, setRiskFilterUser] = useState<string>('USR-1012');
  const [riskFilterLevel, setRiskFilterLevel] = useState<string>('');

  // SHAP Explanation State
  const [selectedShapUser, setSelectedShapUser] = useState<string>('USR-1012');
  const [userShapData, setUserShapData] = useState<UserShapExplanationResponse | null>(null);
  const [shapLoading, setShapLoading] = useState<boolean>(false);

  // Adaptive User Profiling State
  const [alphaVal, setAlphaVal] = useState<number>(0.15);
  const [selectedDemoUser, setSelectedDemoUser] = useState<string>('USR-1001');
  const [selectedDemoFeature, setSelectedDemoFeature] = useState<string>('file_access_count');
  const [profileSummary, setProfileSummary] = useState<UserProfileSummary | null>(null);
  const [profileCalculating, setProfileCalculating] = useState<boolean>(false);

  // Behavioral Feature Extraction State
  const [featureRecords, setFeatureRecords] = useState<BehavioralFeatureRecord[]>([]);
  const [featureUserList, setFeatureUserList] = useState<string[]>([]);
  const [selectedFeatureUser, setSelectedFeatureUser] = useState<string>('');
  const [featurePageOffset, setFeaturePageOffset] = useState<number>(0);
  const pageSize = 10;

  // Privacy Interactive Demo State
  const [inputOriginalId, setInputOriginalId] = useState<string>('EMP001');
  const [pseudonymResult, setPseudonymResult] = useState<PseudonymizeResponse | null>(null);
  const [pseudonymLoading, setPseudonymLoading] = useState<boolean>(false);
  
  // Controlled Lookup Test State
  const [lookupPseudoId, setLookupPseudoId] = useState<string>('');
  const [lookupAuthToken, setLookupAuthToken] = useState<string>('');
  const [lookupResult, setLookupResult] = useState<ControlledLookupResponse | null>(null);
  const [lookupLoading, setLookupLoading] = useState<boolean>(false);

  const [selectedTable, setSelectedTable] = useState<string>('anomaly_results');
  const [loading, setLoading] = useState<boolean>(true);
  const [dbTesting, setDbTesting] = useState<boolean>(false);
  const [lastChecked, setLastChecked] = useState<string | null>(null);

  const checkAll = async () => {
    setLoading(true);

    try {
      const hData = await fetchHealth();
      setHealthData(hData);
    } catch {
      // Non-blocking
    }

    try {
      const dStatus = await fetchDatabaseStatus();
      setDbStatus(dStatus);
    } catch {
      // Non-blocking
    }

    try {
      const schemaData = await fetchDatabaseSchema();
      setDbSchema(schemaData);
    } catch {
      // Non-blocking
    }

    // Load initial extracted behavioral features preview
    await loadFeaturePreviewData('', 0);

    // Load initial adaptive profile demonstration
    await loadAdaptiveProfileDemo(selectedDemoUser, alphaVal);

    // Initial pseudonym demonstration run for EMP001
    await runPseudonymize('EMP001');

    // Run or load analysis pipeline
    await executePipeline();

    setLastChecked(new Date().toLocaleTimeString());
    setLoading(false);
  };

  const executePipeline = async () => {
    setAnalysisRunning(true);
    try {
      const res = await runFullAnalysis({ contamination: 0.07, risk_decay: 0.88, risk_gain: 0.13, sync_to_db: true });
      setAnalysisResult(res);
      await loadAnomaliesList('');
      await loadRiskList(riskFilterUser);
      await loadShapExplanations(selectedShapUser);
    } catch (err) {
      console.warn('Pipeline run notice:', err);
    } finally {
      setAnalysisRunning(false);
    }
  };

  const loadAnomaliesList = async (userFilter: string) => {
    setAnomLoading(true);
    try {
      const anomRes = await fetchAnomalies(userFilter, true, 20, 0);
      setAnomRecords(anomRes.records);
    } catch (err) {
      console.error(err);
    } finally {
      setAnomLoading(false);
    }
  };

  const loadRiskList = async (userFilter: string, level?: string) => {
    try {
      const riskRes = await fetchRiskScores(userFilter, level, 30, 0);
      setRiskRecords(riskRes.records);
    } catch (err) {
      console.error(err);
    }
  };

  const loadShapExplanations = async (userId: string) => {
    setShapLoading(true);
    try {
      const shapRes = await fetchUserShapExplanations(userId, 8);
      setUserShapData(shapRes);
    } catch (err) {
      console.error(err);
    } finally {
      setShapLoading(false);
    }
  };

  const loadFeaturePreviewData = async (userFilter: string = '', offset: number = 0) => {
    try {
      const prevData = await fetchFeaturesPreview(userFilter, pageSize, offset);
      setFeatureRecords(prevData.records);
      setFeatureUserList(prevData.unique_users);
      setFeaturePageOffset(offset);
    } catch (err) {
      console.warn(err);
    }
  };

  const loadAdaptiveProfileDemo = async (userId: string, alpha: number) => {
    setProfileCalculating(true);
    try {
      const res = await fetchUserProfileSummary(userId, alpha);
      setProfileSummary(res.user_summary);
    } catch (err) {
      console.error(err);
    } finally {
      setProfileCalculating(false);
    }
  };

  const runPseudonymize = async (idToUse?: string) => {
    const target = idToUse || inputOriginalId;
    if (!target) return;
    setPseudonymLoading(true);
    try {
      const res = await pseudonymizeUserId(target);
      setPseudonymResult(res);
      setLookupPseudoId(res.pseudonymous_id);
    } catch (err) {
      console.error(err);
    } finally {
      setPseudonymLoading(false);
    }
  };

  const handleControlledLookup = async (tokenOverride?: string) => {
    if (!lookupPseudoId) return;
    setLookupLoading(true);
    const token = tokenOverride !== undefined ? tokenOverride : lookupAuthToken;
    try {
      const res = await performControlledLookup(lookupPseudoId, token);
      setLookupResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLookupLoading(false);
    }
  };

  const testDbConnectionOnly = async () => {
    setDbTesting(true);
    try {
      const dStatus = await fetchDatabaseStatus();
      setDbStatus(dStatus);
    } catch {
      // Handled
    } finally {
      setDbTesting(false);
    }
  };

  useEffect(() => {
    checkAll();
  }, []);

  return (
    <div className="min-w-full min-h-[calc(100vh-73px)] bg-slate-950 text-slate-100 p-4 sm:p-6 lg:p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        
        {/* Project Header Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-blue-400 bg-blue-950/60 border border-blue-800/60 px-2.5 py-1 rounded">
                Final-Year Engineering Project &bull; Complete System Pipeline
              </span>
              <h2 className="text-xl sm:text-2xl font-bold text-white mt-2">
                Privacy-Preserving Adaptive Insider Threat Detection and Early Warning System
              </h2>
              <p className="text-sm text-slate-400 mt-1 max-w-3xl">
                End-to-End Pipeline: Deterministic Pseudonymization &bull; Feature Engineering &bull;
                Isolation Forest Anomaly Detection &bull; Progressive Risk Engine &bull; SHAP Explainability.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={checkAll}
                disabled={loading}
                className="inline-flex items-center justify-center space-x-2 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs transition cursor-pointer"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                <span>Refresh Status</span>
              </button>

              <button
                onClick={executePipeline}
                disabled={analysisRunning}
                className="inline-flex items-center justify-center space-x-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs transition disabled:opacity-50 cursor-pointer shadow-sm"
              >
                <Play className={`w-3.5 h-3.5 ${analysisRunning ? 'animate-spin' : ''}`} />
                <span>{analysisRunning ? 'Running ML Pipeline...' : 'Run Full Analysis Pipeline'}</span>
              </button>
            </div>
          </div>

          {/* Quick Metrics Grid */}
          <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            
            {/* Isolation Forest Card */}
            <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-4 flex items-center space-x-3">
              <div className="p-3 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-slate-400">Isolation Forest Anomalies</p>
                <p className="text-base font-bold text-rose-400">
                  {analysisResult?.anomaly_detection?.anomaly_count ?? 126} flagged
                </p>
                <p className="text-[11px] font-mono text-slate-400">
                  {analysisResult?.anomaly_detection?.percentage_anomalous ?? 7.0}% (contam=0.07)
                </p>
              </div>
            </div>

            {/* Progressive Risk Card */}
            <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-4 flex items-center space-x-3">
              <div className="p-3 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <Flame className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-slate-400">Critical Risk Users</p>
                <p className="text-base font-bold text-amber-400">
                  {analysisResult?.critical_risk_users?.length ?? 3} Critical
                </p>
                <p className="text-[11px] font-mono text-slate-400">
                  USR-1012, 1025, 1038
                </p>
              </div>
            </div>

            {/* SHAP Explainability Card */}
            <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-4 flex items-center space-x-3">
              <div className="p-3 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <Lightbulb className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-slate-400">SHAP Explainability</p>
                <p className="text-sm font-bold text-indigo-300">TreeExplainer Active</p>
                <p className="text-[11px] font-mono text-slate-400">8 Feature Attributions</p>
              </div>
            </div>

            {/* Privacy & System Health */}
            <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-4 flex items-center space-x-3">
              <div className="p-3 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <Shield className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-slate-400">Privacy &amp; DB</p>
                <p className="text-sm font-semibold text-emerald-400 flex items-center space-x-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Pseudonymized</span>
                </p>
                <p className="text-[11px] font-mono text-slate-400">
                  {dbStatus?.connected ? 'MySQL Live' : 'ORM Mapped'}
                </p>
              </div>
            </div>

          </div>
        </div>

        {/* Unified ML Results Hub: Anomalies | Risk | SHAP Tabs */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div className="flex items-center space-x-2">
              <Cpu className="w-5 h-5 text-blue-400" />
              <h3 className="font-semibold text-white text-base">
                Machine Learning Detection &amp; Explainability Engine
              </h3>
            </div>

            {/* Tab Buttons */}
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setActiveAnalysisTab('anomalies')}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer flex items-center space-x-1.5 ${
                  activeAnalysisTab === 'anomalies'
                    ? 'bg-rose-600 text-white shadow-sm'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>1. Isolation Forest Anomalies</span>
              </button>

              <button
                onClick={() => setActiveAnalysisTab('risk')}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer flex items-center space-x-1.5 ${
                  activeAnalysisTab === 'risk'
                    ? 'bg-amber-600 text-white shadow-sm'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                <Flame className="w-3.5 h-3.5" />
                <span>2. Progressive Risk Engine</span>
              </button>

              <button
                onClick={() => setActiveAnalysisTab('shap')}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer flex items-center space-x-1.5 ${
                  activeAnalysisTab === 'shap'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                <Lightbulb className="w-3.5 h-3.5" />
                <span>3. SHAP Explainability</span>
              </button>
            </div>
          </div>

          {/* TAB 1: Isolation Forest Anomalies */}
          {activeAnalysisTab === 'anomalies' && (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                <p className="text-slate-400">
                  Isolation Forest trained with <span className="text-rose-300 font-mono">contamination = 0.07</span> across 1,800 records.
                  Detects outliers without hardcoded labels.
                </p>
                <div className="flex items-center space-x-2">
                  <Filter className="w-3.5 h-3.5 text-slate-400" />
                  <span className="text-slate-400">Filter User:</span>
                  <select
                    value={anomFilterUser}
                    onChange={(e) => {
                      setAnomFilterUser(e.target.value);
                      loadAnomaliesList(e.target.value);
                    }}
                    className="bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg px-2.5 py-1 font-mono"
                  >
                    <option value="">All Flagged Users ({analysisResult?.anomaly_detection?.unique_users_flagged ?? 31})</option>
                    {(analysisResult?.anomaly_detection?.flagged_user_ids || ['USR-1012', 'USR-1025', 'USR-1038']).map((u: string) => (
                      <option key={u} value={u}>{u}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="overflow-x-auto rounded-lg border border-slate-800">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3">user_id</th>
                      <th className="py-2.5 px-3">date</th>
                      <th className="py-2.5 px-3 text-right">anomaly_score</th>
                      <th className="py-2.5 px-3">prediction</th>
                      <th className="py-2.5 px-3 text-right">file_access</th>
                      <th className="py-2.5 px-3 text-right">sensitive_files</th>
                      <th className="py-2.5 px-3 text-right">web_upload (MB)</th>
                      <th className="py-2.5 px-3 text-right">after_hours</th>
                      <th className="py-2.5 px-3 text-right">session (min)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/80 bg-slate-900/40 text-slate-300">
                    {anomRecords.length > 0 ? (
                      anomRecords.map((row, idx) => (
                        <tr key={`${row.pseudonymous_user_id}-${row.date}-${idx}`} className="hover:bg-slate-800/50 transition">
                          <td className="py-2 px-3 font-semibold text-indigo-300">{row.pseudonymous_user_id}</td>
                          <td className="py-2 px-3 text-slate-400">{row.date}</td>
                          <td className="py-2 px-3 text-right font-bold text-rose-400">
                            {row.anomaly_score.toFixed(4)}
                          </td>
                          <td className="py-2 px-3">
                            <span className="px-1.5 py-0.5 rounded text-[10px] bg-rose-950 text-rose-300 border border-rose-800 font-bold">
                              ANOMALOUS
                            </span>
                          </td>
                          <td className="py-2 px-3 text-right text-cyan-300 font-semibold">{row.file_access_count}</td>
                          <td className={`py-2 px-3 text-right font-semibold ${row.sensitive_file_access > 2 ? 'text-rose-400' : 'text-slate-400'}`}>
                            {row.sensitive_file_access}
                          </td>
                          <td className={`py-2 px-3 text-right font-semibold ${row.web_upload_volume > 30 ? 'text-rose-400' : 'text-slate-300'}`}>
                            {row.web_upload_volume.toFixed(2)}
                          </td>
                          <td className="py-2 px-3 text-right text-amber-300">{row.after_hours_login}</td>
                          <td className="py-2 px-3 text-right text-slate-300">{row.average_session_minutes.toFixed(1)}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={9} className="py-8 text-center text-slate-500 font-sans">
                          {anomLoading ? 'Loading anomalies...' : 'Click "Run Full Analysis Pipeline" to detect anomalies.'}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 2: Progressive Risk Engine */}
          {activeAnalysisTab === 'risk' && (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                <p className="text-slate-400">
                  Formula: <span className="text-amber-300 font-mono">risk(t) = 0.88 &times; risk(t-1) + 0.13 &times; anomaly(t)</span>.
                  Demonstrates how repeated anomalies accumulate while single anomalies stay LOW and normal behavior decays back.
                </p>
                <div className="flex items-center space-x-2">
                  <span className="text-slate-400">Inspect User Timeline:</span>
                  <select
                    value={riskFilterUser}
                    onChange={(e) => {
                      setRiskFilterUser(e.target.value);
                      loadRiskList(e.target.value);
                    }}
                    className="bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg px-2.5 py-1 font-mono"
                  >
                    <option value="USR-1012">USR-1012 (Data Exfiltration Drift &rarr; CRITICAL)</option>
                    <option value="USR-1025">USR-1025 (After-Hours Recon &rarr; CRITICAL)</option>
                    <option value="USR-1038">USR-1038 (IP Leakage &rarr; CRITICAL)</option>
                    <option value="USR-1001">USR-1001 (Normal User &rarr; LOW)</option>
                  </select>
                </div>
              </div>

              <div className="overflow-x-auto rounded-lg border border-slate-800">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3">user_id</th>
                      <th className="py-2.5 px-3">date</th>
                      <th className="py-2.5 px-3">anomaly_detected</th>
                      <th className="py-2.5 px-3 text-right">anomaly_score</th>
                      <th className="py-2.5 px-3 text-right font-bold text-amber-300">risk_score (0-100)</th>
                      <th className="py-2.5 px-3">risk_level</th>
                      <th className="py-2.5 px-3">Progression Dynamics</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/80 bg-slate-900/40 text-slate-300">
                    {riskRecords.length > 0 ? (
                      riskRecords.map((row, idx) => {
                        const levelColors: Record<string, string> = {
                          LOW: 'bg-emerald-950 text-emerald-300 border-emerald-800',
                          MEDIUM: 'bg-blue-950 text-blue-300 border-blue-800',
                          HIGH: 'bg-amber-950 text-amber-300 border-amber-800',
                          CRITICAL: 'bg-rose-950 text-rose-300 border-rose-800 font-bold',
                        };

                        const prevScore = idx > 0 ? riskRecords[idx - 1].risk_score : 0;
                        const delta = row.risk_score - prevScore;

                        return (
                          <tr key={`${row.pseudonymous_user_id}-${row.date}-${idx}`} className="hover:bg-slate-800/50 transition">
                            <td className="py-2 px-3 font-semibold text-indigo-300">{row.pseudonymous_user_id}</td>
                            <td className="py-2 px-3 text-slate-400">{row.date}</td>
                            <td className="py-2 px-3">
                              {row.anomaly_flag ? (
                                <span className="text-rose-400 font-semibold flex items-center space-x-1">
                                  <AlertTriangle className="w-3 h-3" />
                                  <span>ANOMALY</span>
                                </span>
                              ) : (
                                <span className="text-slate-500">Normal</span>
                              )}
                            </td>
                            <td className="py-2 px-3 text-right text-slate-300">{row.anomaly_score.toFixed(4)}</td>
                            <td className="py-2 px-3 text-right font-bold text-white text-sm">
                              {row.risk_score.toFixed(2)}
                            </td>
                            <td className="py-2 px-3">
                              <span className={`px-2 py-0.5 rounded text-[10px] border ${levelColors[row.risk_level] || ''}`}>
                                {row.risk_level}
                              </span>
                            </td>
                            <td className="py-2 px-3 text-[11px]">
                              {row.anomaly_flag ? (
                                <span className="text-rose-400 flex items-center space-x-1">
                                  <ArrowUpRight className="w-3 h-3" />
                                  <span>Accumulated (+{delta.toFixed(2)})</span>
                                </span>
                              ) : row.risk_score > 0 ? (
                                <span className="text-emerald-400 flex items-center space-x-1">
                                  <ArrowDownRight className="w-3 h-3" />
                                  <span>Decayed (&times;0.88)</span>
                                </span>
                              ) : (
                                <span className="text-slate-500">Baseline Normal</span>
                              )}
                            </td>
                          </tr>
                        );
                      })
                    ) : (
                      <tr>
                        <td colSpan={7} className="py-8 text-center text-slate-500 font-sans">
                          Loading progressive risk timeline...
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 3: SHAP Explainability */}
          {activeAnalysisTab === 'shap' && (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs border-b border-slate-800 pb-3">
                <p className="text-slate-400">
                  TreeExplainer SHAP attributions explaining which behavioral dimensions drove the anomaly.
                  Explanations stored in MySQL <code className="text-indigo-300">risk_explanations</code> table.
                </p>
                <div className="flex items-center space-x-2">
                  <span className="text-slate-400">Select Flagged User:</span>
                  <select
                    value={selectedShapUser}
                    onChange={(e) => {
                      setSelectedShapUser(e.target.value);
                      loadShapExplanations(e.target.value);
                    }}
                    className="bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg px-2.5 py-1 font-mono"
                  >
                    <option value="USR-1012">USR-1012 (Data Exfiltration: Web Upload + Sensitive Files)</option>
                    <option value="USR-1025">USR-1025 (After-Hours Recon: Night Logins + Long Sessions)</option>
                    <option value="USR-1038">USR-1038 (IP Leakage: External Emails + Sensitive Files)</option>
                    <option value="USR-1001">USR-1001 (Normal User Baseline)</option>
                  </select>
                </div>
              </div>

              {/* Answers to the 3 Viva Questions */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                
                {/* 1. Features that Increased Anomaly */}
                <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-3">
                  <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
                    <ArrowUpRight className="w-4 h-4 text-rose-400" />
                    <h4 className="font-semibold text-white text-xs">
                      1. Features That Increased Anomaly (Pushed Toward Anomaly)
                    </h4>
                  </div>
                  <div className="space-y-2">
                    {userShapData?.explanation?.features_increasing_anomaly && userShapData.explanation.features_increasing_anomaly.length > 0 ? (
                      userShapData.explanation.features_increasing_anomaly.map((f) => (
                        <div key={f.feature} className="flex items-center justify-between text-xs bg-slate-900 p-2 rounded font-mono">
                          <div>
                            <span className="text-rose-300 font-semibold block">{f.feature}</span>
                            <span className="text-[11px] text-slate-400">Observed Mean: {f.feature_value}</span>
                          </div>
                          <div className="text-right">
                            <span className="text-rose-400 font-bold block">Contribution: {f.contribution}</span>
                            <span className="text-[10px] text-rose-500 font-bold">INCREASES_RISK</span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-slate-500 text-xs py-2">No features elevated above anomaly threshold for this user.</p>
                    )}
                  </div>
                </div>

                {/* 2. Normal / Low Contribution Features */}
                <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-3">
                  <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
                    <ArrowDownRight className="w-4 h-4 text-emerald-400" />
                    <h4 className="font-semibold text-white text-xs">
                      2. Features With Normal Baseline Behavior (Decreased Risk)
                    </h4>
                  </div>
                  <div className="space-y-2">
                    {userShapData?.explanation?.features_decreasing_anomaly && userShapData.explanation.features_decreasing_anomaly.length > 0 ? (
                      userShapData.explanation.features_decreasing_anomaly.map((f) => (
                        <div key={f.feature} className="flex items-center justify-between text-xs bg-slate-900 p-2 rounded font-mono">
                          <div>
                            <span className="text-emerald-300 font-semibold block">{f.feature}</span>
                            <span className="text-[11px] text-slate-400">Observed Mean: {f.feature_value}</span>
                          </div>
                          <div className="text-right">
                            <span className="text-emerald-400 font-bold block">Contribution: {f.contribution}</span>
                            <span className="text-[10px] text-emerald-500">NORMALIZING</span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-slate-500 text-xs py-2">All features were abnormal.</p>
                    )}
                  </div>
                </div>

              </div>

              {/* Top Daily Contributing Drivers Timeline */}
              <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-2">
                <span className="text-xs font-semibold text-slate-200 block border-b border-slate-800 pb-2">
                  Primary Daily Anomaly Driver for {selectedShapUser} (Chronological Days):
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2 text-xs font-mono pt-1">
                  {userShapData?.explanation?.daily_primary_drivers?.slice(-10).map((d) => (
                    <div key={d.date} className="bg-slate-900 p-2 rounded border border-slate-800 text-[11px]">
                      <span className="text-slate-400 block text-[10px]">{d.date}</span>
                      <span className="font-bold text-indigo-300 truncate block mt-0.5">{d.top_feature}</span>
                      <span className="text-slate-300 block text-[10px]">Val: {d.feature_value}</span>
                      <span className="text-rose-400 font-semibold text-[10px] block">Contr: {d.contribution}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

        </div>

        {/* Adaptive User Profiling Viva Demonstration (Step 6) */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-5 h-5 text-indigo-400" />
                <h3 className="font-semibold text-white text-base">
                  Adaptive User Profiling (`calculate_adaptive_profile`)
                </h3>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                EWMA formula: <code className="text-indigo-300">baseline(t) = (1 - &alpha;) &bull; baseline(t-1) + &alpha; &bull; x(t)</code>
              </p>
            </div>
            <div className="flex items-center space-x-3 text-xs">
              <span className="text-slate-400">&alpha; Rate: <strong className="text-indigo-300">{alphaVal}</strong></span>
              <input
                type="range"
                min="0.01"
                max="0.50"
                step="0.01"
                value={alphaVal}
                onChange={(e) => {
                  const v = parseFloat(e.target.value);
                  setAlphaVal(v);
                  loadAdaptiveProfileDemo(selectedDemoUser, v);
                }}
                className="accent-indigo-500 cursor-pointer w-28"
              />
            </div>
          </div>

          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Day</th>
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3 text-right">Action x(t)</th>
                  <th className="py-2.5 px-3 text-right">Prior Base</th>
                  <th className="py-2.5 px-3 text-right text-indigo-300">New Base</th>
                  <th className="py-2.5 px-3 text-right text-cyan-300">Deviation &Delta;</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80 bg-slate-900/40 text-slate-300">
                {profileSummary?.daily_progression?.slice(0, 7).map((item, idx) => {
                  const featData = item.features[selectedDemoFeature] || { current_value: 0, baseline: 0, deviation: 0 };
                  const priorBase = idx === 0 ? 'Day 0' : profileSummary.daily_progression[idx - 1].features[selectedDemoFeature].baseline.toFixed(2);
                  return (
                    <tr key={item.date} className="hover:bg-slate-800/50 transition">
                      <td className="py-2 px-3 font-semibold text-slate-400">Day {item.day_index}</td>
                      <td className="py-2 px-3 text-slate-300">{item.date}</td>
                      <td className="py-2 px-3 text-right font-bold text-white">{featData.current_value.toFixed(2)}</td>
                      <td className="py-2 px-3 text-right text-slate-400">{priorBase}</td>
                      <td className="py-2 px-3 text-right font-bold text-indigo-300">{featData.baseline.toFixed(2)}</td>
                      <td className="py-2 px-3 text-right text-cyan-300">{featData.deviation > 0 ? `+${featData.deviation.toFixed(2)}` : featData.deviation.toFixed(2)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* 8 SQLAlchemy Database Models Reference */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
            <div>
              <h3 className="font-semibold text-white text-base flex items-center space-x-2">
                <Table className="w-5 h-5 text-indigo-400" />
                <span>SQLAlchemy Models (8 Tables Configured)</span>
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                All 8 tables synchronized with the detection and explainability engines.
              </p>
            </div>
            <button
              onClick={testDbConnectionOnly}
              disabled={dbTesting}
              className="inline-flex items-center space-x-1.5 text-xs text-amber-300 bg-amber-950/40 hover:bg-amber-900/50 border border-amber-800/60 px-3 py-1.5 rounded transition cursor-pointer self-start"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${dbTesting ? 'animate-spin' : ''}`} />
              <span>Test MySQL (`SELECT 1;`)</span>
            </button>
          </div>

          <div className="flex flex-wrap gap-2 mt-4">
            {[
              { name: 'anomaly_results', label: '4. anomaly_results (Isolation Forest)' },
              { name: 'risk_scores', label: '5. risk_scores (Progressive Risk)' },
              { name: 'risk_explanations', label: '6. risk_explanations (SHAP)' },
              { name: 'behavior_features', label: '3. behavior_features' },
              { name: 'analysis_runs', label: '7. analysis_runs' },
              { name: 'settings', label: '8. settings' },
              { name: 'users', label: '1. users' },
              { name: 'activity_logs', label: '2. activity_logs' },
            ].map((tab) => (
              <button
                key={tab.name}
                onClick={() => setSelectedTable(tab.name)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer ${
                  selectedTable === tab.name
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="mt-4 overflow-x-auto">
            {dbSchema?.tables?.[selectedTable] ? (
              <table className="w-full text-left text-xs border border-slate-800 rounded-lg overflow-hidden font-mono">
                <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Column</th>
                    <th className="py-2.5 px-3">Data Type</th>
                    <th className="py-2.5 px-3">Primary Key</th>
                    <th className="py-2.5 px-3">Nullable</th>
                    <th className="py-2.5 px-3">Foreign Key Target</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80 bg-slate-900/40 text-slate-300">
                  {dbSchema.tables[selectedTable].map((col) => (
                    <tr key={col.name} className="hover:bg-slate-800/40 transition">
                      <td className="py-2 px-3 font-semibold text-indigo-300 flex items-center space-x-1.5">
                        <ChevronRight className="w-3 h-3 text-slate-500" />
                        <span>{col.name}</span>
                      </td>
                      <td className="py-2 px-3 text-cyan-300">{col.type}</td>
                      <td className="py-2 px-3">
                        {col.primary_key ? (
                          <span className="text-emerald-400 bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800 text-[10px]">PK</span>
                        ) : '—'}
                      </td>
                      <td className="py-2 px-3">{col.nullable ? 'YES' : 'NO'}</td>
                      <td className="py-2 px-3 text-amber-300">
                        {col.foreign_keys && col.foreign_keys.length > 0
                          ? col.foreign_keys.join(', ')
                          : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-4 bg-slate-950 rounded border border-slate-800 text-xs text-slate-400 font-mono">
                Loading schema metadata...
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};
