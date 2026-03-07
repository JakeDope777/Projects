// ── Chat Types ──────────────────────────────────────────────

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  module_used?: string;
  tokens_used?: number;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  context?: Record<string, unknown>;
}

export interface ChatResponse {
  reply: string;
  conversation_id: string;
  module_used?: string;
  tokens_used?: number;
}

// ── Auth Types ──────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  role: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
}

// ── Dashboard Types ─────────────────────────────────────────

export interface DashboardMetrics {
  total_leads: number;
  new_leads_period: number;
  total_spend: number;
  conversions: number;
  conversion_rate: number;
  cac: number;
  ltv: number;
  roas: number;
  ctr: number;
  impressions: number;
  clicks: number;
  email_open_rate: number;
  email_click_rate: number;
}

export interface ChartData {
  id: string;
  type: 'line' | 'bar' | 'funnel';
  title: string;
  data: {
    x?: string[];
    y?: number[];
    labels?: string[];
    values?: number[];
  };
  layout?: Record<string, string>;
}

export interface DashboardData {
  metrics: DashboardMetrics;
  charts: ChartData[];
}

// ── Analysis Types ──────────────────────────────────────────

export interface AnalysisResponse {
  insights?: Array<Record<string, unknown>>;
  analysis?: Record<string, unknown>;
  personas?: Array<Record<string, unknown>>;
  sources?: string[];
}

// ── Creative Types ──────────────────────────────────────────

export interface CreativeResponse {
  content?: string;
  alternatives?: string[];
  image_url?: string;
  schedule?: Array<Record<string, unknown>>;
}

// ── CRM Types ───────────────────────────────────────────────

export interface Lead {
  id: string;
  name?: string;
  email?: string;
  status?: string;
  created_at?: string;
}

export interface Campaign {
  id: string;
  name: string;
  channel: string;
  status: string;
  created_at?: string;
}

// ── Navigation ──────────────────────────────────────────────

export interface NavItem {
  label: string;
  path: string;
  icon: string;
}
