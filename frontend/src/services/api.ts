/**
 * API Service for communicating with the Flask backend, MySQL database layer,
 * and Demonstration Activity-Log Dataset endpoints.
 */

export interface HealthResponse {
  status: string;
  service?: string;
  version?: string;
  timestamp?: string;
  error?: string;
}

export interface DatabaseStatusResponse {
  connected: boolean;
  status: string;
  message: string;
  error?: string | null;
  connection_details: {
    dialect: string;
    driver: string;
    host: string;
    port: string;
    database: string;
    user: string;
    has_password: boolean;
    configured_via_url: boolean;
  };
  defined_models: string[];
  schema_tables_defined: string[];
  configuration_guide: {
    mysql_service_required: boolean;
    target_url: string;
    hint: string;
  };
}

export interface TableColumn {
  name: string;
  type: string;
  primary_key: boolean;
  nullable: boolean;
  foreign_keys?: string[] | null;
}

export interface DatabaseSchemaResponse {
  status: string;
  total_tables: number;
  tables: Record<string, TableColumn[]>;
}

export interface ActivityRecord {
  user_id: string;
  date: string;
  login_count: number;
  after_hours_login: number;
  file_access_count: number;
  sensitive_file_access: number;
  email_count: number;
  external_email_count: number;
  web_upload_volume: number;
  average_session_minutes: number;
}

export interface GenerateSampleResponse {
  status: string;
  message: string;
  number_of_records: number;
  number_of_users: number;
  date_range: {
    start_date: string;
    end_date: string;
    total_days: number;
  };
  file_location: string;
  columns: string[];
  sample_preview: ActivityRecord[];
}

export interface SamplePreviewResponse {
  status: string;
  total_records: number;
  limit: number;
  offset: number;
  records: ActivityRecord[];
  unique_users: string[];
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

/**
 * Fetches the backend health check status from GET /api/health.
 */
export async function fetchHealth(): Promise<HealthResponse> {
  const endpoint = `${API_BASE_URL}/health`;
  try {
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Server returned status code: ${response.status} (${response.statusText})`);
    }

    const data: HealthResponse = await response.json();
    return data;
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Unknown network error';
    throw new Error(`Failed to connect to Flask backend at ${endpoint}: ${message}`);
  }
}

/**
 * Fetches MySQL database connectivity status and configuration diagnostic from GET /api/database/status.
 */
export async function fetchDatabaseStatus(): Promise<DatabaseStatusResponse> {
  const endpoint = `${API_BASE_URL}/database/status`;
  const response = await fetch(endpoint, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Server returned status code: ${response.status} (${response.statusText})`);
  }

  return await response.json();
}

/**
 * Fetches schema definitions for all 8 SQLAlchemy models from GET /api/database/schema.
 */
export async function fetchDatabaseSchema(): Promise<DatabaseSchemaResponse> {
  const endpoint = `${API_BASE_URL}/database/schema`;
  const response = await fetch(endpoint, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Server returned status code: ${response.status} (${response.statusText})`);
  }

  return await response.json();
}

/**
 * Generates sample activity-log data (POST /api/generate-sample).
 */
export async function generateSampleData(params?: {
  num_users?: number;
  num_days?: number;
  seed?: number;
}): Promise<GenerateSampleResponse> {
  const endpoint = `${API_BASE_URL}/generate-sample`;
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(params || {}),
  });

  if (!response.ok) {
    throw new Error(`Failed to generate sample data: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Retrieves sample data records and user list from GET /api/sample-data/preview.
 */
export async function fetchSamplePreview(
  userId?: string,
  limit: number = 20,
  offset: number = 0
): Promise<SamplePreviewResponse> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (userId) {
    params.append('user_id', userId);
  }

  const endpoint = `${API_BASE_URL}/sample-data/preview?${params.toString()}`;
  const response = await fetch(endpoint, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to retrieve sample records: ${response.statusText}`);
  }

  return await response.json();
}

export interface PrivacyStatusResponse {
  status: string;
  mechanism: string;
  hash_algorithm: string;
  pseudonym_format: string;
  total_pseudonymized_users: number;
  data_minimization_enforced: boolean;
  controlled_lookup_enabled: boolean;
}

export interface PseudonymizeResponse {
  status: string;
  pseudonymous_id: string;
  original_id_hash: string;
  created_at: string;
  note?: string;
}

export interface ControlledLookupResponse {
  status: string;
  message?: string;
  error?: string;
  access_granted: boolean;
  record?: {
    pseudonymous_id: string;
    original_id: string;
    original_id_hash: string;
    audit_timestamp: string;
    access_granted: boolean;
  };
}

/**
 * Fetches privacy subsystem status from GET /api/privacy/status.
 */
export async function fetchPrivacyStatus(): Promise<PrivacyStatusResponse> {
  const endpoint = `${API_BASE_URL}/privacy/status`;
  const response = await fetch(endpoint, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`Server returned status: ${response.status}`);
  }
  return await response.json();
}

/**
 * Pseudonymizes an employee identifier via POST /api/privacy/pseudonymize.
 * Original ID is converted into a deterministic pseudonymous ID and NOT returned.
 */
export async function pseudonymizeUserId(originalId: string): Promise<PseudonymizeResponse> {
  const endpoint = `${API_BASE_URL}/privacy/pseudonymize`;
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({ original_id: originalId }),
  });
  if (!response.ok) {
    throw new Error(`Pseudonymization failed with status: ${response.status}`);
  }
  return await response.json();
}

/**
 * Performs controlled identity lookup requiring compliance audit token via POST /api/privacy/lookup.
 */
export async function performControlledLookup(
  pseudonymousId: string,
  authToken: string
): Promise<ControlledLookupResponse> {
  const endpoint = `${API_BASE_URL}/privacy/lookup`;
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({
      pseudonymous_id: pseudonymousId,
      auth_token: authToken,
    }),
  });

  return await response.json();
}

export interface BehavioralFeatureRecord {
  pseudonymous_user_id: string;
  date: string;
  login_count: number;
  after_hours_login: number;
  file_access_count: number;
  sensitive_file_access: number;
  email_count: number;
  external_email_count: number;
  web_upload_volume: number;
  average_session_minutes: number;
}

export interface ExtractFeaturesResponse {
  status: string;
  message: string;
  number_of_users: number;
  number_of_user_day_records: number;
  date_range: {
    start_date: string;
    end_date: string;
    total_days: number;
  };
  columns: string[];
  feature_dataframe_preview: BehavioralFeatureRecord[];
  database_sync?: {
    synced: boolean;
    status: string;
    message?: string;
    records_stored?: number;
    error?: string;
  };
}

export interface FeaturesPreviewResponse {
  status: string;
  total_records: number;
  limit: number;
  offset: number;
  records: BehavioralFeatureRecord[];
  unique_users: string[];
}

/**
 * Triggers user-day behavioral feature extraction via POST /api/features/extract.
 */
export async function extractBehavioralFeatures(options?: {
  file_path?: string;
  records?: Record<string, unknown>[];
  sync_to_db?: boolean;
}): Promise<ExtractFeaturesResponse> {
  const endpoint = `${API_BASE_URL}/features/extract`;
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(options || { sync_to_db: true }),
  });

  if (!response.ok) {
    throw new Error(`Feature extraction failed with status: ${response.status}`);
  }

  return await response.json();
}

/**
 * Retrieves paginated behavioral features from GET /api/features/preview.
 */
export async function fetchFeaturesPreview(
  userId?: string,
  limit: number = 20,
  offset: number = 0
): Promise<FeaturesPreviewResponse> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (userId) {
    params.append('user_id', userId);
  }

  const endpoint = `${API_BASE_URL}/features/preview?${params.toString()}`;
  const response = await fetch(endpoint, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to retrieve feature records: ${response.statusText}`);
  }

  return await response.json();
}

export interface DayFeatureProgression {
  current_value: number;
  baseline: number;
  deviation: number;
}

export interface DailyProgressionItem {
  day_index: number;
  date: string;
  features: Record<string, DayFeatureProgression>;
}

export interface UserProfileSummary {
  user_id: string;
  total_days: number;
  start_date: string;
  end_date: string;
  daily_progression: DailyProgressionItem[];
}

export interface AdaptiveProfileRecord {
  pseudonymous_user_id: string;
  date: string;
  login_count: number;
  login_count_baseline: number;
  login_count_deviation: number;
  after_hours_login: number;
  after_hours_login_baseline: number;
  after_hours_login_deviation: number;
  file_access_count: number;
  file_access_count_baseline: number;
  file_access_count_deviation: number;
  sensitive_file_access: number;
  sensitive_file_access_baseline: number;
  sensitive_file_access_deviation: number;
  email_count: number;
  email_count_baseline: number;
  email_count_deviation: number;
  external_email_count: number;
  external_email_count_baseline: number;
  external_email_count_deviation: number;
  web_upload_volume: number;
  web_upload_volume_baseline: number;
  web_upload_volume_deviation: number;
  average_session_minutes: number;
  average_session_minutes_baseline: number;
  average_session_minutes_deviation: number;
}

export interface AdaptiveProfileResponse {
  status: string;
  message: string;
  alpha_used: number;
  formula: string;
  behavioral_features: string[];
  total_users: number;
  total_records: number;
  limit: number;
  offset: number;
  records: AdaptiveProfileRecord[];
  demo_summary?: UserProfileSummary | null;
  unique_users: string[];
}

/**
 * Calculates adaptive EWMA behavioral baselines and deviations via POST /api/profile/adaptive.
 */
export async function calculateAdaptiveProfile(params?: {
  alpha?: number;
  user_id?: string;
  limit?: number;
  offset?: number;
}): Promise<AdaptiveProfileResponse> {
  const endpoint = `${API_BASE_URL}/profile/adaptive`;
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(params || { alpha: 0.15 }),
  });

  if (!response.ok) {
    throw new Error(`Adaptive profile calculation failed with status: ${response.status}`);
  }

  return await response.json();
}

/**
 * Fetches step-by-step day-by-day progression for a single user via GET /api/profile/user/:userId.
 */
export async function fetchUserProfileSummary(
  userId: string,
  alpha: number = 0.15
): Promise<{ status: string; alpha: number; user_summary: UserProfileSummary }> {
  const endpoint = `${API_BASE_URL}/profile/user/${encodeURIComponent(userId)}?alpha=${alpha}`;
  const response = await fetch(endpoint, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch user profile summary: ${response.statusText}`);
  }

  return await response.json();
}

export interface AnomalyRecord {
  pseudonymous_user_id: string;
  date: string;
  anomaly_score: number;
  anomaly_flag: boolean;
  prediction: string;
  raw_decision_score: number;
  file_access_count: number;
  sensitive_file_access: number;
  web_upload_volume: number;
  after_hours_login: number;
  login_count: number;
  email_count: number;
  external_email_count: number;
  average_session_minutes: number;
}

export interface RiskRecord {
  pseudonymous_user_id: string;
  date: string;
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  anomaly_flag: boolean;
  anomaly_score: number;
}

export interface ShapFeatureContribution {
  feature: string;
  feature_value: number;
  shap_value: number;
  contribution: number;
  direction: 'INCREASES_RISK' | 'DECREASES_RISK';
}

export interface UserShapExplanationResponse {
  status: string;
  user_id: string;
  explanation: {
    user_id: string;
    total_days_analyzed: number;
    top_features_overall: ShapFeatureContribution[];
    features_increasing_anomaly: ShapFeatureContribution[];
    features_decreasing_anomaly: ShapFeatureContribution[];
    daily_primary_drivers: {
      date: string;
      top_feature: string;
      feature_value: number;
      contribution: number;
      direction: string;
    }[];
  };
}

export interface PipelineRunResponse {
  analysis_status: string;
  analysis_run_id: string;
  number_of_records: number;
  number_of_users: number;
  number_of_anomalies: number;
  high_risk_user_count: number;
  critical_risk_user_count: number;
  date_range: {
    start: string;
    end: string;
  };
  parameters: {
    alpha: number;
    contamination: number;
    risk_decay: number;
    risk_gain: number;
  };
  pipeline_stages: string[];
  database_sync: {
    connected: boolean;
    records_synced: number;
    status: string;
  };
}

export interface DashboardSummaryResponse {
  status: string;
  total_users: number;
  activity_records: number;
  high_risk_users: number;
  critical_risk_users: number;
  total_anomalies: number;
  risk_level_distribution: {
    LOW: number;
    MEDIUM: number;
    HIGH: number;
    CRITICAL: number;
  };
  date_range: {
    start: string;
    end: string;
  };
  daily_trend: {
    date: string;
    avg_risk: number;
    max_risk: number;
    anomalies: number;
  }[];
  top_contributing_factors: {
    feature: string;
    mean_absolute_shap: number;
  }[];
  last_run_id: string;
  last_run_time: string;
  parameters: {
    alpha: number;
    contamination: number;
    risk_decay: number;
    risk_gain: number;
  };
}

export interface UserSummaryItem {
  pseudonymous_id: string;
  latest_risk_score: number;
  latest_risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  peak_risk_score: number;
  anomaly_count: number;
  last_activity_date: string;
  avg_web_upload_volume: number;
  avg_file_access_count: number;
}

export interface UsersListResponse {
  status: string;
  total_users: number;
  users: UserSummaryItem[];
}

export interface UserDetailResponse {
  status: string;
  pseudonymous_id: string;
  current_risk: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  anomaly_count: number;
  last_activity_date: string;
  risk_history: {
    date: string;
    risk_score: number;
    risk_level: string;
    anomaly_flag: boolean;
    anomaly_score: number;
  }[];
  behavioral_summary: {
    averages: Record<string, number>;
    latest: Record<string, number>;
  };
  anomaly_history: {
    date: string;
    risk_score: number;
    risk_level: string;
    anomaly_flag: boolean;
    anomaly_score: number;
  }[];
  top_shap_factors: ShapFeatureContribution[];
  features_increasing_anomaly: ShapFeatureContribution[];
  features_decreasing_anomaly: ShapFeatureContribution[];
}

export interface UserRiskTrendResponse {
  status: string;
  pseudonymous_id: string;
  trend: {
    date: string;
    risk_score: number;
    risk_level: string;
    anomaly_flag: boolean;
    anomaly_score: number;
    web_upload_deviation?: number;
    file_access_deviation?: number;
    after_hours_deviation?: number;
  }[];
}

export interface AlertItem {
  alert_id: string;
  pseudonymous_id: string;
  risk_level: 'HIGH' | 'CRITICAL';
  risk_score: number;
  anomalous_days_count: number;
  last_incident_date: string;
  primary_threat_vector: string;
  recent_upload_volume_mb: number;
  recent_sensitive_files: number;
  recent_after_hours_logins: number;
  status: string;
}

export interface AlertsResponse {
  status: string;
  total_alerts: number;
  critical_count: number;
  high_count: number;
  alerts: AlertItem[];
}

export interface AnalysisRunItem {
  id: string;
  filename: string;
  record_count: number;
  user_count: number;
  total_anomalies: number;
  high_risk_users: number;
  critical_risk_users: number;
  date_range: {
    start: string;
    end: string;
  };
  parameters: Record<string, number>;
  created_at: string;
  database_sync: Record<string, unknown>;
}

export interface AnalysisRunsResponse {
  status: string;
  total_runs: number;
  runs: AnalysisRunItem[];
}

export interface SettingsResponse {
  status: string;
  parameters: {
    alpha: number;
    contamination: number;
    risk_decay: number;
    risk_gain: number;
  };
  default_parameters: {
    alpha: number;
    contamination: number;
    risk_decay: number;
    risk_gain: number;
  };
}

/**
 * Executes complete unified analysis pipeline (POST /api/analyze).
 */
export async function executePipeline(
  file?: File,
  params?: {
    alpha?: number;
    contamination?: number;
    risk_decay?: number;
    risk_gain?: number;
  }
): Promise<PipelineRunResponse> {
  const endpoint = `${API_BASE_URL}/analyze`;
  let body: BodyInit;
  const headers: HeadersInit = { Accept: 'application/json' };

  if (file) {
    const formData = new FormData();
    formData.append('file', file);
    if (params?.alpha !== undefined) formData.append('alpha', String(params.alpha));
    if (params?.contamination !== undefined) formData.append('contamination', String(params.contamination));
    if (params?.risk_decay !== undefined) formData.append('risk_decay', String(params.risk_decay));
    if (params?.risk_gain !== undefined) formData.append('risk_gain', String(params.risk_gain));
    body = formData;
  } else {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(params || {});
  }

  const response = await fetch(endpoint, {
    method: 'POST',
    headers,
    body,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `Pipeline analysis failed with status: ${response.status}`);
  }

  return await response.json();
}

/**
 * Fetches dashboard summary statistics (GET /api/dashboard-summary).
 */
export async function fetchDashboardSummary(): Promise<DashboardSummaryResponse> {
  const endpoint = `${API_BASE_URL}/dashboard-summary`;
  const response = await fetch(endpoint, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch dashboard summary: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Fetches list of analyzed users with risk tiers and anomaly counts (GET /api/users).
 */
export async function fetchUsersList(levelFilter?: string): Promise<UsersListResponse> {
  const endpoint = levelFilter
    ? `${API_BASE_URL}/users?level=${encodeURIComponent(levelFilter)}`
    : `${API_BASE_URL}/users`;

  const response = await fetch(endpoint, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch users list: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Fetches single user detail (GET /api/users/<pseudonymous_id>).
 */
export async function fetchUserDetail(pseudonymousId: string): Promise<UserDetailResponse> {
  const endpoint = `${API_BASE_URL}/users/${encodeURIComponent(pseudonymousId)}`;
  const response = await fetch(endpoint, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch details for user ${pseudonymousId}: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Fetches single user day-by-day risk trend (GET /api/users/<pseudonymous_id>/risk-trend).
 */
export async function fetchUserRiskTrend(pseudonymousId: string): Promise<UserRiskTrendResponse> {
  const endpoint = `${API_BASE_URL}/users/${encodeURIComponent(pseudonymousId)}/risk-trend`;
  const response = await fetch(endpoint, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch risk trend for user ${pseudonymousId}: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Fetches active high and critical security alerts (GET /api/alerts).
 */
export async function fetchAlerts(): Promise<AlertsResponse> {
  const endpoint = `${API_BASE_URL}/alerts`;
  const response = await fetch(endpoint, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch security alerts: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Fetches history of analysis runs (GET /api/analysis-runs).
 */
export async function fetchAnalysisRuns(): Promise<AnalysisRunsResponse> {
  const endpoint = `${API_BASE_URL}/analysis-runs`;
  const response = await fetch(endpoint, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch analysis runs: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Fetches current hyperparameters (GET /api/settings).
 */
export async function fetchSettings(): Promise<SettingsResponse> {
  const endpoint = `${API_BASE_URL}/settings`;
  const response = await fetch(endpoint, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch settings: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Updates hyperparameters and re-runs pipeline (POST /api/settings).
 */
export async function updateSettings(params: {
  alpha?: number;
  contamination?: number;
  risk_decay?: number;
  risk_gain?: number;
}): Promise<{ status: string; message: string; parameters: SettingsResponse['parameters'] }> {
  const endpoint = `${API_BASE_URL}/settings`;
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    throw new Error(`Failed to update settings: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Fetches SHAP feature explanations for a specific user via GET /api/users/<pseudonymous_id>/explanations.
 */
export async function fetchUserShapExplanations(
  userId: string,
  topN: number = 5
): Promise<UserShapExplanationResponse> {
  const endpoint = `${API_BASE_URL}/users/${encodeURIComponent(userId)}/explanations?top_n=${topN}`;
  const response = await fetch(endpoint, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch SHAP explanations for ${userId}: ${response.statusText}`);
  }

  return await response.json();
}

export interface FullAnalysisResponse {
  status: string;
  message: string;
  anomaly_detection: {
    total_records: number;
    anomaly_count: number;
    normal_count: number;
    percentage_anomalous: number;
    unique_users_flagged: number;
    flagged_user_ids: string[];
  };
  progressive_risk: {
    total_records: number;
    overall_distribution: Record<string, number>;
    latest_snapshot_distribution: Record<string, number>;
    max_risk_score: number;
    critical_users: string[];
  };
  shap_explainability: {
    total_records_explained: number;
    global_feature_importance: { feature: string; mean_absolute_shap: number }[];
    top_feature_overall: string;
  };
  example_anomalous_records: any[];
  critical_risk_users: string[];
  database_sync: Record<string, unknown>;
}

export async function runFullAnalysis(params?: {
  contamination?: number;
  risk_decay?: number;
  risk_gain?: number;
  sync_to_db?: boolean;
}): Promise<FullAnalysisResponse> {
  const endpoint = `${API_BASE_URL}/analyze`;
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(params || {}),
  });

  if (!response.ok) {
    throw new Error(`Analysis execution failed: ${response.statusText}`);
  }

  return await response.json();
}

export async function fetchAnomalies(
  userId?: string,
  flaggedOnly: boolean = true,
  limit: number = 20,
  offset: number = 0
): Promise<{ status: string; total_records: number; records: any[] }> {
  const params = new URLSearchParams({
    flagged_only: String(flaggedOnly),
    limit: String(limit),
    offset: String(offset),
  });
  if (userId) params.append('user_id', userId);

  const endpoint = `${API_BASE_URL}/alerts?${params.toString()}`;
  const response = await fetch(endpoint, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch anomalies: ${response.statusText}`);
  }

  return await response.json();
}

export async function fetchRiskScores(
  userId?: string,
  level?: string,
  limit: number = 20,
  offset: number = 0
): Promise<{ status: string; total_records: number; records: any[]; summary: any }> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (userId) params.append('user_id', userId);
  if (level) params.append('level', level);

  const endpoint = `${API_BASE_URL}/users?${params.toString()}`;
  const response = await fetch(endpoint, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch risk scores: ${response.statusText}`);
  }

  return await response.json();
}





