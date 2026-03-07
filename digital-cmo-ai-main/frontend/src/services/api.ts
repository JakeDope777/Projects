import axios from 'axios';
import type {
  ChatRequest,
  ChatResponse,
  AuthTokens,
  DashboardData,
  AnalysisResponse,
  CreativeResponse,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Attach auth token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Auth ────────────────────────────────────────────────────

export const authService = {
  async signup(email: string, password: string): Promise<AuthTokens> {
    const { data } = await api.post<AuthTokens>('/auth/signup', { email, password });
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    return data;
  },

  async login(email: string, password: string): Promise<AuthTokens> {
    const { data } = await api.post<AuthTokens>('/auth/login', { email, password });
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    return data;
  },

  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  },
};

// ── Chat ────────────────────────────────────────────────────

export const chatService = {
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const { data } = await api.post<ChatResponse>('/chat', request);
    return data;
  },

  async getConversation(conversationId: string) {
    const { data } = await api.get(`/chat/${conversationId}`);
    return data;
  },

  async clearConversation(conversationId: string) {
    const { data } = await api.delete(`/chat/${conversationId}`);
    return data;
  },
};

// ── Dashboard / Analytics ───────────────────────────────────

export const analyticsService = {
  async getDashboard(): Promise<DashboardData> {
    const { data } = await api.get<DashboardData>('/analytics/dashboard');
    return data;
  },

  async getForecast(metric: string, horizon: number = 30) {
    const { data } = await api.post('/analytics/forecast', { metric, horizon });
    return data;
  },

  async recordExperiment(experimentId: string, variants: Array<Record<string, unknown>>) {
    const { data } = await api.post('/analytics/experiment', {
      experiment_id: experimentId,
      variants,
    });
    return data;
  },
};

// ── Business Analysis ───────────────────────────────────────

export const analysisService = {
  async marketResearch(query: string): Promise<AnalysisResponse> {
    const { data } = await api.post<AnalysisResponse>('/analysis/market', { query });
    return data;
  },

  async swotAnalysis(subject: string): Promise<AnalysisResponse> {
    const { data } = await api.post<AnalysisResponse>('/analysis/swot', { subject });
    return data;
  },

  async pestelAnalysis(subject: string): Promise<AnalysisResponse> {
    const { data } = await api.post<AnalysisResponse>('/analysis/pestel', { subject });
    return data;
  },

  async competitorAnalysis(companyNames: string[]): Promise<AnalysisResponse> {
    const { data } = await api.post<AnalysisResponse>('/analysis/competitors', {
      company_names: companyNames,
    });
    return data;
  },

  async createPersonas(dataSource: string = 'general', numPersonas: number = 3): Promise<AnalysisResponse> {
    const { data } = await api.post<AnalysisResponse>('/analysis/personas', {
      data_source: dataSource,
      num_personas: numPersonas,
    });
    return data;
  },
};

// ── Creative ────────────────────────────────────────────────

export const creativeService = {
  async generateCopy(brief: string, tone?: string, length?: number): Promise<CreativeResponse> {
    const { data } = await api.post<CreativeResponse>('/creative/generate', { brief, tone, length });
    return data;
  },

  async generateImage(description: string, style?: string): Promise<CreativeResponse> {
    const { data } = await api.post<CreativeResponse>('/creative/image', { description, style });
    return data;
  },

  async suggestABTests(baseCopy: string): Promise<CreativeResponse> {
    const { data } = await api.post<CreativeResponse>('/creative/ab-test', { base_copy: baseCopy });
    return data;
  },
};

// ── CRM ─────────────────────────────────────────────────────

export const crmService = {
  async getLeads() {
    const { data } = await api.get('/crm/leads');
    return data;
  },

  async getCampaigns() {
    const { data } = await api.get('/crm/campaigns');
    return data;
  },

  async createLead(leadId: string, attributes: Record<string, unknown>) {
    const { data } = await api.post('/crm/lead', { lead_id: leadId, attributes });
    return data;
  },

  async createCampaign(name: string, channel: string = 'email') {
    const { data } = await api.post('/crm/campaign', { name, channel });
    return data;
  },

  async checkCompliance(message: string, channel: string = 'email') {
    const { data } = await api.post('/crm/compliance', { message, channel });
    return data;
  },
};

export default api;
