import type {
  Job,
  JobAnalysis,
  JobStats,
  MarketInsights,
  SavedJob,
  SearchFilters,
  SourcesStatus,
} from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010";

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export function getSources(): Promise<SourcesStatus> {
  return fetch(`${API_URL}/api/sources`, { credentials: "include" }).then(json<SourcesStatus>);
}

export function analyzeJob(job: Job, country: string): Promise<JobAnalysis> {
  return fetch(`${API_URL}/api/analyze`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job, country }),
  }).then(json<JobAnalysis>);
}

export function listSavedJobs(): Promise<SavedJob[]> {
  return fetch(`${API_URL}/api/jobs`, { credentials: "include" }).then(json<SavedJob[]>);
}

export function getJobStats(): Promise<JobStats> {
  return fetch(`${API_URL}/api/jobs/stats`, { credentials: "include" }).then(json<JobStats>);
}

export function saveJob(job: Job, country: string): Promise<SavedJob> {
  return fetch(`${API_URL}/api/jobs`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job, country }),
  }).then(json<SavedJob>);
}

export function updateSavedJob(id: string, fields: Partial<SavedJob>): Promise<SavedJob> {
  return fetch(`${API_URL}/api/jobs/${id}`, {
    method: "PATCH",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(fields),
  }).then(json<SavedJob>);
}

export function deleteSavedJob(id: string): Promise<void> {
  return fetch(`${API_URL}/api/jobs/${id}`, {
    method: "DELETE",
    credentials: "include",
  }).then(() => undefined);
}

export function buildSearchUrl(prompt: string, filters: SearchFilters): string {
  const params = new URLSearchParams({
    prompt,
    country: filters.country,
    job_type: filters.jobType === "Todos" ? "" : filters.jobType,
    salary_min: String(filters.salaryMin || 0),
    currency: filters.currency,
    experience: filters.experience === "Cualquier nivel" ? "" : filters.experience,
  });
  return `${API_URL}/api/search?${params.toString()}`;
}

export interface SearchStreamHandlers {
  onUpdate: (jobs: Job[]) => void;
  onDone: (jobs: Job[], market: MarketInsights | null) => void;
  onError: (message: string) => void;
}

export function runSearchStream(
  prompt: string,
  filters: SearchFilters,
  handlers: SearchStreamHandlers,
): () => void {
  const es = new EventSource(buildSearchUrl(prompt, filters), { withCredentials: true });

  es.addEventListener("update", (ev) => {
    const jobs = JSON.parse((ev as MessageEvent).data) as Job[];
    handlers.onUpdate(jobs);
  });

  es.addEventListener("done", (ev) => {
    const payload = JSON.parse((ev as MessageEvent).data) as {
      jobs: Job[];
      market: MarketInsights | null;
    };
    handlers.onDone(payload.jobs, payload.market);
    es.close();
  });

  es.addEventListener("error", (ev) => {
    const data = (ev as MessageEvent).data;
    if (data) {
      try {
        handlers.onError(JSON.parse(data));
      } catch {
        handlers.onError(String(data));
      }
    } else {
      handlers.onError("Se perdió la conexión con el servidor de búsqueda.");
    }
    es.close();
  });

  return () => es.close();
}
