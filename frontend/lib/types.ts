export interface Job {
  title: string;
  company: string;
  location: string;
  url: string;
  source: string;
  salary_min: number | null;
  salary_max: number | null;
  currency: string;
  job_type: string;
  description: string;
  posted: string;
  tags: string[];
  seniority_level: string;
  seniority_score: number;
  years_required: number | null;
  role_category: string;
}

export interface Signal {
  emoji: string;
  label: string;
  detail: string;
  kind: "danger" | "warning" | "positive" | "info";
}

export interface SalaryEstimate {
  low: number;
  high: number;
  currency: string;
  basis: string;
  comparison: string;
  comparison_kind: string;
  mid_eur: number;
}

export interface JobAnalysis {
  hard_skills: string[];
  soft_skills: string[];
  company_type: string;
  signals: Signal[];
  junior_trap: boolean;
  seniority_detail: string;
  ai_summary: string;
  clean_description: string;
  has_rich_description: boolean;
  description_blocks: Record<string, string>;
  salary_estimate: SalaryEstimate | null;
}

export interface MarketInsights {
  total: number;
  top_skills: [string, number][];
  avg_years: number | null;
  median_salary: number | null;
  salary_currency: string;
}

export interface SourcesStatus {
  linkedin: boolean;
  remotive: boolean;
  arbeitnow: boolean;
  computrabajo: boolean;
  adzuna: boolean;
}

export interface TimelineEvent {
  date: string;
  event: string;
}

export interface SavedJob {
  id: string;
  title: string;
  company: string;
  location: string;
  url: string;
  source: string;
  job_type: string;
  salary_display: string;
  salary_estimate: string;
  description: string;
  skills: string[];
  signals: Signal[];
  seniority: string;
  saved_at: string;
  status: string;
  applied_date: string;
  salary_offered: string;
  contact: string;
  interview_date: string;
  notes: string;
  interest: string;
  timeline: TimelineEvent[];
}

export interface JobStats {
  total: number;
  enviadas: number;
  entrevistas: number;
  activas: number;
  ratio: number;
  top_companies: [string, number][];
  top_skills: [string, number][];
}

export interface SearchFilters {
  country: string;
  jobType: string;
  salaryMin: number;
  currency: string;
  experience: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  suggestedKeywords?: string[];
}
