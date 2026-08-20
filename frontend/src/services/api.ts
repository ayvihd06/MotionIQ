import axios from 'axios';
import type {
  VideoUploadResponse,
  AnalysisStatusResponse,
  AnalysisResultResponse,
  DetectedVideoContext,
  OptionalUserContext,
  AnalysisContext,
  User,
  UserProfile,
  AuthResponse,
  FormEvolutionData,
  LiveAnalysisSavePayload,
  MilestonesResponse,
  MilestoneItem,
  GoalResponse,
  GoalUpdateRequest,
  AnalysisComparisonResponse,
  PersonalFocusResponse,
  PersonalizedRecommendationResponse,
  PersonalizedWeeklySummaryResponse
} from '../types';

const API_BASE = '/api';

// Support cookies for session-based auth
axios.defaults.withCredentials = true;

// Optional: attach token from sessionStorage if present
const token = sessionStorage.getItem('motioniq_token');
if (token) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

export const setAuthHeader = (token: string | null) => {
  if (token) {
    sessionStorage.setItem('motioniq_token', token);
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    sessionStorage.removeItem('motioniq_token');
    delete axios.defaults.headers.common['Authorization'];
  }
};

export const api = {
  // Authentication & Profile Services
  async register(email: string, password: string, displayName?: string): Promise<AuthResponse> {
    const response = await axios.post<AuthResponse>(`${API_BASE}/auth/register`, {
      email,
      password,
      display_name: displayName
    });
    setAuthHeader(response.data.access_token);
    return response.data;
  },

  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await axios.post<AuthResponse>(`${API_BASE}/auth/login`, {
      email,
      password
    });
    setAuthHeader(response.data.access_token);
    return response.data;
  },

  async logout(): Promise<void> {
    try {
      await axios.post(`${API_BASE}/auth/logout`);
    } finally {
      setAuthHeader(null);
    }
  },

  async getMe(): Promise<User> {
    const response = await axios.get<User>(`${API_BASE}/auth/me`);
    return response.data;
  },

  async updateProfile(profileData: Partial<UserProfile>): Promise<UserProfile> {
    const response = await axios.put<UserProfile>(`${API_BASE}/auth/profile`, profileData);
    return response.data;
  },

  async deleteAccount(): Promise<void> {
    await axios.delete(`${API_BASE}/auth/account`);
    setAuthHeader(null);
  },

  // Personal Form Evolution Services
  async getFormEvolution(): Promise<FormEvolutionData> {
    const response = await axios.get<FormEvolutionData>(`${API_BASE}/evolution`);
    return response.data;
  },

  // Video Upload & Initial Suitability Assessment
  async uploadVideo(file: File, onProgress?: (percent: number) => void): Promise<VideoUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post<VideoUploadResponse>(`${API_BASE}/videos/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percentCompleted);
        }
      },
    });
    return response.data;
  },

  // Create Full Analysis Session
  async createAnalysis(
    videoId: string,
    detectedContext: DetectedVideoContext,
    optionalContext?: OptionalUserContext
  ): Promise<AnalysisStatusResponse> {
    const response = await axios.post<AnalysisStatusResponse>(`${API_BASE}/analyses`, {
      video_id: videoId,
      detected_context: detectedContext,
      optional_context: optionalContext,
    });
    return response.data;
  },

  // Polling Pipeline Analysis Status
  async getAnalysisStatus(analysisId: string): Promise<AnalysisStatusResponse> {
    const response = await axios.get<AnalysisStatusResponse>(`${API_BASE}/analyses/${analysisId}/status`);
    return response.data;
  },

  // Retrieve Full Biomechanical Analysis Results
  async getAnalysisResult(analysisId: string): Promise<AnalysisResultResponse> {
    const response = await axios.get<AnalysisResultResponse>(`${API_BASE}/analyses/${analysisId}`);
    return response.data;
  },

  // Delete Individual Analysis
  async deleteAnalysis(analysisId: string): Promise<void> {
    await axios.delete(`${API_BASE}/analyses/${analysisId}`);
  },

  // List Past Analyses
  async listAnalyses(): Promise<any[]> {
    const response = await axios.get<any[]>(`${API_BASE}/analyses`);
    return response.data;
  },

  // 1-Click Demo Mode Analysis
  async getDemoAnalysis(): Promise<AnalysisResultResponse> {
    const response = await axios.get<AnalysisResultResponse>(`${API_BASE}/analyses/demo/sample`);
    return response.data;
  },

  // PDF Report Download URL
  getPdfReportUrl(analysisId: string): string {
    return `${API_BASE}/analyses/${analysisId}/report.pdf`;
  },

  // Context Management
  async getAnalysisContext(analysisId: string): Promise<AnalysisContext> {
    const response = await axios.get<AnalysisContext>(`${API_BASE}/analyses/${analysisId}/context`);
    return response.data;
  },

  async updateOptionalContext(analysisId: string, optionalContext: OptionalUserContext): Promise<AnalysisContext> {
    const response = await axios.patch<AnalysisContext>(
      `${API_BASE}/analyses/${analysisId}/context`,
      optionalContext
    );
    return response.data;
  },

  async reanalyzeContext(analysisId: string): Promise<DetectedVideoContext> {
    const response = await axios.post<DetectedVideoContext>(
      `${API_BASE}/analyses/${analysisId}/context/analyze`
    );
    return response.data;
  },

  // Save Live Camera Analysis Session
  async saveLiveAnalysis(payload: LiveAnalysisSavePayload): Promise<AnalysisResultResponse> {
    const response = await axios.post<AnalysisResultResponse>(`${API_BASE}/analyses/live`, payload);
    return response.data;
  },

  // Personal Milestones
  async getMilestones(): Promise<MilestonesResponse> {
    const response = await axios.get<MilestonesResponse>(`${API_BASE}/milestones`);
    return response.data;
  },

  async getSessionCelebration(analysisId: string): Promise<{ analysis_id: string; has_celebration: boolean; new_personal_bests: MilestoneItem[] }> {
    const response = await axios.get<{ analysis_id: string; has_celebration: boolean; new_personal_bests: MilestoneItem[] }>(`${API_BASE}/milestones/celebration/${analysisId}`);
    return response.data;
  },

  // Personal Goals
  async getUserGoal(): Promise<GoalResponse> {
    const response = await axios.get<GoalResponse>(`${API_BASE}/profile/goal`);
    return response.data;
  },

  async updateUserGoal(payload: GoalUpdateRequest): Promise<GoalResponse> {
    const response = await axios.put<GoalResponse>(`${API_BASE}/profile/goal`, payload);
    return response.data;
  },

  async completeUserGoal(): Promise<GoalResponse> {
    const response = await axios.patch<GoalResponse>(`${API_BASE}/profile/goal/complete`);
    return response.data;
  },

  // What Changed — Session-over-session comparison
  async getAnalysisComparison(analysisId: string): Promise<AnalysisComparisonResponse> {
    const response = await axios.get<AnalysisComparisonResponse>(`${API_BASE}/analyses/${analysisId}/comparison`);
    return response.data;
  },

  // Personal Focus Area
  async getPersonalFocus(): Promise<PersonalFocusResponse> {
    const response = await axios.get<PersonalFocusResponse>(`${API_BASE}/profile/focus`);
    return response.data;
  },

  // Personalized Recommendations
  async getPersonalizedRecommendations(): Promise<PersonalizedRecommendationResponse> {
    const response = await axios.get<PersonalizedRecommendationResponse>(`${API_BASE}/profile/recommendations`);
    return response.data;
  },

  // Personalized Weekly Running Summary
  async getWeeklySummary(weekOffset: number = 0): Promise<PersonalizedWeeklySummaryResponse> {
    const response = await axios.get<PersonalizedWeeklySummaryResponse>(`${API_BASE}/profile/weekly-summary?week_offset=${weekOffset}`);
    return response.data;
  },
};
