export type AgeCategory = '18-29' | '30-39' | '40-49' | '50-59' | '60+';
export type ExperienceLevel = 'Beginner' | 'Intermediate' | 'Advanced' | 'Elite';
export type PerceivedEffort = 'Very easy' | 'Easy' | 'Moderate' | 'Hard' | 'Very hard' | 'Not sure';

export interface ProvenanceField<T> {
  value: T;
  source: 'video_metadata' | 'computer_vision' | 'pose_analysis' | 'user' | 'historical_baseline' | 'calibration';
  confidence: number;
  user_confirmed?: boolean;
  user_corrected?: boolean;
  detected_at?: string;
}

export interface DetectedVideoContext {
  duration_sec: number;
  fps: number;
  resolution: string;
  video_format: string;
  quality_status: string;
  
  runner_count: ProvenanceField<number>;
  full_body_visible: ProvenanceField<boolean>;
  camera_view: ProvenanceField<string>;
  camera_stability: ProvenanceField<string>;
  observed_movement: ProvenanceField<string>;
  surface: ProvenanceField<string>;
  running_pace_status: ProvenanceField<string>;
  pace_estimation_mode: string;
  historical_baseline_status: string;
}

export interface OptionalUserContext {
  training_goal?: string;
  known_pace?: string;
  perceived_effort?: PerceivedEffort;
  previous_injury?: string;
  
  age_category?: AgeCategory;
  experience_level?: ExperienceLevel;
  height_cm?: number;
  weight_kg?: number;
  bmi?: number;
  weekly_volume_km?: number;
}

export interface AnalysisContext {
  video_id: string;
  detected: DetectedVideoContext;
  optional: OptionalUserContext;
  has_missing_context: boolean;
  context_notice: string;
}

export interface SuitabilityCheckItem {
  name: string;
  passed: boolean;
  rating: 'Optimal' | 'Acceptable' | 'Warning' | 'Critical';
  message: string;
}

export interface VideoMetadata {
  filename: string;
  file_size_bytes: number;
  duration_sec: number;
  fps: number;
  width: number;
  height: number;
  frame_count: number;
  format: string;
}

export interface VideoSuitabilityReport {
  overall_status: 'Ready for analysis' | 'Analysis may be unreliable' | 'Unsuitable for analysis';
  suitability_score: number;
  checks: SuitabilityCheckItem[];
  warnings: string[];
  recommendations: string[];
}

export interface VideoUploadResponse {
  video_id: string;
  metadata: VideoMetadata;
  suitability: VideoSuitabilityReport;
  detected_context: DetectedVideoContext;
}

export type AnalysisStatus = 'uploaded' | 'validating' | 'processing' | 'completed' | 'failed';

export interface AnalysisStatusResponse {
  analysis_id: string;
  status: AnalysisStatus;
  progress_percentage: number;
  current_step: string;
  error_message?: string;
}

export interface StandardMetricItem {
  key: string;
  name: string;
  value: string;
  unit: string;
  confidence: 'High' | 'Medium' | 'Low';
  status: 'Optimal' | 'Normal' | 'Attention' | 'Observed' | 'Estimated';
  description: string;
  limitations?: string;
}

export interface FormObservationItem {
  title: string;
  category: string;
  observation: string;
  supporting_metrics: string[];
  confidence: 'High' | 'Medium' | 'Low';
  scientific_note: string;
}

export interface GaitEventItem {
  frame_idx: number;
  timestamp_s: number;
  side: 'left' | 'right' | string;
  event_type: string;
  confidence: number;
}

export interface WaveformPoint {
  timestamp_s: number;
  pelvis_y: number;
  left_ankle_y: number;
  right_ankle_y: number;
}

export interface RunningTypeContext {
  distance_category: string;
  surface_category: string;
  intensity_category: string;
  experience_level: string;
  runner_profile_summary: string;
}

export interface MetricConfidenceItem {
  metric_key: string;
  confidence_level: 'High' | 'Medium' | 'Low';
  confidence_score: number;
  contributing_factors: string[];
}

export interface MetricConfidenceBreakdown {
  cadence_confidence: MetricConfidenceItem;
  symmetry_confidence: MetricConfidenceItem;
  trunk_lean_confidence: MetricConfidenceItem;
  foot_strike_confidence: MetricConfidenceItem;
  overstride_confidence: MetricConfidenceItem;
  vertical_movement_confidence: MetricConfidenceItem;
  overall_confidence: 'High' | 'Medium' | 'Low';
  overall_score: number;
}

export interface ContextAwareInsight {
  title: string;
  category: string;
  severity: 'positive' | 'neutral' | 'monitor';
  description: string;
  supporting_metrics: string[];
  confidence: 'High' | 'Medium' | 'Low';
  why_flagged: string[];
  recommended_action: string;
  limitations: string;
}

export interface OverallSummaryReport {
  headline: string;
  strongest_positive_observations: string[];
  areas_to_monitor: string[];
  form_consistency_score: number;
  context_summary: string;
  responsible_ai_disclaimer: string;
}

export interface AnalysisResultResponse {
  analysis_id: string;
  video_id: string;
  created_at: string;
  context: AnalysisContext;
  video_metadata: VideoMetadata;
  suitability: VideoSuitabilityReport;
  status: AnalysisStatus;
  annotated_video_url?: string;
  
  // Biomechanical Outputs
  cadence_spm: number;
  step_count: number;
  left_right_symmetry_pct: number;
  trunk_lean_deg: number;
  left_mean_step_time_s: number;
  right_mean_step_time_s: number;
  mean_stride_time_s: number;
  step_time_variability_cv: number;
  mean_elbow_angle_deg: number;
  overstride_risk: string;
  foot_strike_pattern: string;
  relative_vertical_movement_proxy: number;
  form_classification: string;
  overall_confidence: 'High' | 'Medium' | 'Low';
  
  // Phase 4 Context, Confidence & Insights
  running_type_context?: RunningTypeContext;
  confidence_breakdown?: MetricConfidenceBreakdown;
  context_insights?: ContextAwareInsight[];
  overall_summary?: OverallSummaryReport;
  
  gait_events: GaitEventItem[];
  waveform_data?: WaveformPoint[];
  metrics_breakdown: StandardMetricItem[];
  observations: FormObservationItem[];
  recommendations: string[];
  limitations: string[];
}

export interface UserProfile {
  id: string;
  display_name?: string;
  age_category?: string;
  height_cm?: number;
  weight_kg?: number;
  running_experience?: string;
  weekly_running_volume_km?: number;
  typical_easy_pace?: string;
  video_retention_preference: boolean;
  optional_profile_preferences?: {
    primary_running_goal?: string;
    sessions_per_week?: number;
    preferred_surface?: string;
    preferred_training?: string;
    [key: string]: any;
  };
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  email: string;
  is_active: boolean;
  created_at: string;
  last_login_at?: string;
  profile?: UserProfile;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  token_type: string;
  message: string;
}

export interface EvolutionMetricDelta {
  metric_key: string;
  name: string;
  unit: string;
  latest_value: number;
  previous_value?: number;
  baseline_value?: number;
  delta_from_previous?: number;
  delta_from_baseline?: number;
  interpretation: string;
}

export interface EvolutionTrendPoint {
  session_index: number;
  analysis_id: string;
  date_label: string;
  created_at: string;
  cadence_spm: number;
  left_right_symmetry_pct: number;
  trunk_lean_deg: number;
  form_consistency_score: number;
  form_classification: string;
  surface: string;
  intensity: string;
  distance: string;
}

export interface PersonalBaseline {
  cadence_spm: number;
  left_right_symmetry_pct: number;
  trunk_lean_deg: number;
  form_consistency_score: number;
  sessions_averaged: number;
}

export interface FormEvolutionData {
  total_analyses: number;
  baseline_status: 'No history' | 'Baseline unavailable' | 'Early baseline' | 'Personal baseline established';
  baseline_message: string;
  personal_baseline: PersonalBaseline | null;
  latest_analysis: {
    analysis_id: string;
    created_at: string;
    form_classification: string;
    overall_confidence: string;
  } | null;
  previous_analysis: {
    analysis_id: string;
    created_at: string;
    form_classification: string;
    overall_confidence: string;
  } | null;
  change_metrics: EvolutionMetricDelta[];
  trend_series: EvolutionTrendPoint[];
  context_notices: string[];
}

export interface LiveAnalysisSavePayload {
  cadence_spm: number;
  step_count: number;
  left_right_symmetry_pct: number;
  trunk_lean_deg: number;
  duration_sec: number;
  camera_view: string;
  camera_suitability: string;
  tracking_quality_pct: number;
  form_classification?: string;
  overall_confidence?: 'High' | 'Medium' | 'Low';
  observations?: string[];
  optional_context?: OptionalUserContext;
}

export interface MilestoneItem {
  type: string;
  title: string;
  icon: string;
  value: number | null;
  unit: string;
  label: string;
  metric_name: string;
  analysis_id?: string | null;
  comparison_analysis_id?: string | null;
  achieved_at?: string | null;
  previous_value?: number | null;
  current_value?: number | null;
  improvement_delta?: number | null;
  improvement_unit?: string | null;
  description: string;
  motivational_note?: string | null;
}

export interface MilestoneEmptyState {
  title: string;
  subtitle: string;
  message: string;
  action_label: string;
}

export interface MilestonesResponse {
  total_analyses: number;
  has_milestones: boolean;
  is_demo: boolean;
  empty_state?: MilestoneEmptyState;
  milestones: MilestoneItem[];
  recent_achievements: any[];
}

export type GoalType =
  | 'IMPROVE_EFFICIENCY'
  | 'IMPROVE_CADENCE'
  | 'IMPROVE_SYMMETRY'
  | 'IMPROVE_FORM'
  | 'IMPROVE_CONSISTENCY'
  | 'GENERAL_PERFORMANCE';

export type GoalStatus = 'ACTIVE' | 'COMPLETED' | 'PAUSED';

export interface GoalOption {
  type: GoalType;
  title: string;
  explanation: string;
  icon: string;
}

export interface GoalItem {
  type: GoalType;
  title: string;
  description?: string | null;
  status: GoalStatus;
  created_at?: string | null;
  updated_at?: string | null;
  explanation: string;
  icon: string;
}

export interface GoalResponse {
  goal: GoalItem | null;
  available_goals: GoalOption[];
}

export interface GoalUpdateRequest {
  type: GoalType;
  description?: string | null;
  status?: GoalStatus;
}

// ── What Changed — Session-over-session comparison types ──────────────────────

export type ComparisonDirection = 'INCREASED' | 'DECREASED' | 'UNCHANGED' | 'CHANGED' | 'NOT_AVAILABLE';
export type ComparisonCategory = 'NOTABLE_CHANGE' | 'MODERATE_CHANGE' | 'LITTLE_CHANGE' | 'NOT_AVAILABLE';

export interface MetricComparisonItem {
  key: string;
  name: string;
  previous_value: number | string | null;
  current_value: number | string | null;
  previous_display: string;
  current_display: string;
  absolute_change: number | null;
  percentage_change: number | null;
  change_display: string;
  unit: string;
  direction: ComparisonDirection;
  category: ComparisonCategory;
  goal_relevant: boolean;
  observation_text: string;
}

export interface UserGoalContext {
  type: string;
  title: string;
  description?: string | null;
  explanation: string;
}

export interface AnalysisComparisonResponse {
  analysis_id: string;
  has_previous: boolean;
  is_first_analysis: boolean;
  previous_analysis_id: string | null;
  previous_created_at: string | null;
  current_created_at: string | null;
  user_goal: UserGoalContext | null;
  comparison_summary: string;
  metrics: MetricComparisonItem[];
}

// ── Personal Focus Area types ─────────────────────────────────────────────────

export type FocusState =
  | 'ACTIVE_FOCUS'
  | 'NO_GOAL'
  | 'FIRST_ANALYSIS'
  | 'NO_STRONG_FOCUS'
  | 'INSUFFICIENT_DATA';

export type FocusConfidence = 'HIGH' | 'MEDIUM' | 'LOW';

export interface FocusAreaItem {
  focus_type: string;
  title: string;
  subtitle: string;
  primary_metric_key: string;
  primary_metric_name: string;
  goal_type: string;
  goal_title: string;
  confidence: FocusConfidence;
  reasoning: string[];
  supporting_observations: string[];
  priority_score: number;
}

export interface PersonalFocusResponse {
  state: FocusState;
  has_goal: boolean;
  total_analyses: number;
  goal: {
    type: string;
    title: string;
    description?: string;
    explanation: string;
  } | null;
  focus: FocusAreaItem | null;
  headline: string;
  message: string;
  action_cta: {
    label: string;
    target: string;
  } | null;
}

// ── Personalized Recommendation types ─────────────────────────────────────────

export type RecommendationCategory =
  | 'OBSERVE'
  | 'PRACTICE'
  | 'CONSISTENCY'
  | 'RECHECK'
  | 'CONTEXT_MATCH'
  | 'LEARN';

export type RecommendationConfidence = 'HIGH' | 'MEDIUM' | 'LOW';

export type RecommendationState =
  | 'ACTIVE_RECOMMENDATION'
  | 'NO_GOAL'
  | 'FIRST_ANALYSIS'
  | 'NO_STRONG_FOCUS'
  | 'LOW_CONFIDENCE'
  | 'INSUFFICIENT_DATA';

export interface RecommendationItem {
  title: string;
  category: RecommendationCategory;
  focus_type: string;
  focus_title: string;
  goal_type: string;
  goal_title: string;
  action_suggestion: string;
  action_bullets: string[];
  rationale: string[];
  confidence: RecommendationConfidence;
  supporting_evidence: string[];
}

export interface PersonalizedRecommendationResponse {
  state: RecommendationState;
  has_goal: boolean;
  total_analyses: number;
  goal: {
    type: string;
    title: string;
    description?: string;
    explanation: string;
  } | null;
  focus_type: string | null;
  recommendation: RecommendationItem | null;
  headline: string;
  message: string;
  action_cta: {
    label: string;
    target: string;
  } | null;
}

// ── Personalized Weekly Running Summary types ─────────────────────────────────

export type WeeklySummaryState = 'ACTIVE_SUMMARY' | 'ONE_SESSION' | 'EMPTY_WEEK';

export interface WeeklyPeriod {
  start_date: string;
  end_date: string;
  label: string;
  week_offset: number;
}

export interface WeeklyMetricItem {
  key: string;
  name: string;
  value_display: string;
  unit: string;
  change_display: string | null;
  is_percentage_points: boolean;
}

export interface WeeklyHighlight {
  headline: string;
  description: string;
  badge: string;
}

export interface PersonalizedWeeklySummaryResponse {
  period: WeeklyPeriod;
  state: WeeklySummaryState;
  total_sessions: number;
  goal: {
    type: string;
    title: string;
    description?: string;
    explanation: string;
  } | null;
  focus: {
    focus_type: string;
    title: string;
    subtitle: string;
    confidence: string;
  } | null;
  highlight: WeeklyHighlight | null;
  metrics: WeeklyMetricItem[];
  changes_summary: string | null;
  milestone: {
    title: string;
    category: string;
    value_display?: string;
    description: string;
  } | null;
  recommendation: {
    title: string;
    category: string;
    action_suggestion: string;
    action_bullets: string[];
    confidence: string;
  } | null;
  insight: string;
  context_notes: string[];
  has_previous_week: boolean;
  action_cta: {
    label: string;
    target: string;
  } | null;
}

export type WorkflowStep =
  | 'landing'
  | 'dashboard'
  | 'upload'
  | 'live'
  | 'detected_context'
  | 'processing'
  | 'results'
  | 'science'
  | 'login'
  | 'register'
  | 'profile'
  | 'evolution'
  | 'milestones'
  | 'privacy';

