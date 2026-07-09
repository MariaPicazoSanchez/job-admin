"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { listSavedJobs, runSearchStream } from "@/lib/api";
import { DEFAULT_FILTERS } from "@/lib/constants";
import type { Job, MarketInsights, SearchFilters } from "@/lib/types";
import SearchBar from "@/components/SearchBar";
import FiltersPanel from "@/components/FiltersPanel";
import ResultsList from "@/components/ResultsList";
import JobDetailPanel from "@/components/JobDetailPanel";
import ChatPanel from "@/components/ChatPanel";

type SortOrder = "relevance" | "salary_desc" | "salary_asc";

function sortJobs(jobs: Job[], order: SortOrder): Job[] {
  if (order === "relevance") return jobs;
  const withSalary = (j: Job) => j.salary_max ?? j.salary_min ?? 0;
  return [...jobs].sort((a, b) =>
    order === "salary_desc" ? withSalary(b) - withSalary(a) : withSalary(a) - withSalary(b),
  );
}

const jobKey = (job: Job) => `${job.source}-${job.url}`;

// Mantiene la posición de las ofertas ya mostradas (para no reordenar mientras
// la persona las está leyendo) y añade las nuevas al final de la lista.
function mergeKeepOrder(prev: Job[], incoming: Job[]): Job[] {
  const incomingByKey = new Map(incoming.map((j) => [jobKey(j), j]));
  const prevKeys = new Set(prev.map(jobKey));
  const kept = prev.map((j) => incomingByKey.get(jobKey(j)) ?? j);
  const added = incoming.filter((j) => !prevKeys.has(jobKey(j)));
  return [...kept, ...added];
}

export default function SearchPage() {
  const [prompt, setPrompt] = useState("");
  const [queryText, setQueryText] = useState("");
  const [chatOpen, setChatOpen] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({
    country: DEFAULT_FILTERS.country,
    jobType: DEFAULT_FILTERS.jobType,
    salaryMin: DEFAULT_FILTERS.salaryMin,
    currency: DEFAULT_FILTERS.currency,
    experience: DEFAULT_FILTERS.experience,
  });
  const [sortOrder, setSortOrder] = useState<SortOrder>("relevance");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [market, setMarket] = useState<MarketInsights | null>(null);
  const [searching, setSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [savedUrls, setSavedUrls] = useState<Set<string>>(new Set());

  const stopStreamRef = useRef<(() => void) | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const refreshSavedUrls = useCallback(() => {
    listSavedJobs()
      .then((saved) => setSavedUrls(new Set(saved.map((s) => s.url))))
      .catch(() => {});
  }, []);

  useEffect(() => {
    refreshSavedUrls();
  }, [refreshSavedUrls]);

  const runSearch = useCallback(
    (searchPrompt: string, searchFilters: SearchFilters) => {
      if (!searchPrompt.trim()) return;
      stopStreamRef.current?.();
      setSearching(true);
      setHasSearched(true);
      setError(null);
      setJobs([]);
      setMarket(null);
      setSelectedJob(null);

      stopStreamRef.current = runSearchStream(searchPrompt, searchFilters, {
        onUpdate: (partial) => setJobs((prev) => mergeKeepOrder(prev, partial)),
        onDone: (finalJobs, finalMarket) => {
          setJobs((prev) => mergeKeepOrder(prev, finalJobs));
          setMarket(finalMarket);
          setSearching(false);
        },
        onError: (message) => {
          setError(message);
          setSearching(false);
        },
      });
    },
    [],
  );

  function handleSearch(newPrompt: string) {
    setPrompt(newPrompt);
    setQueryText(newPrompt);
    runSearch(newPrompt, filters);
  }

  function handleSelectKeyword(keyword: string) {
    setQueryText((prev) => (prev.trim() ? `${prev.trim()} ${keyword}` : keyword));
    setSelectedJob(null);
  }

  function handleFiltersChange(next: SearchFilters) {
    setFilters(next);
    if (!prompt.trim()) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => runSearch(prompt, next), 700);
  }

  useEffect(() => {
    return () => {
      stopStreamRef.current?.();
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  const sortedJobs = sortJobs(jobs, sortOrder);

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-4 p-4">
      <div className="flex flex-col gap-3">
        <div className="flex gap-2">
          <div className="flex-1">
            <SearchBar value={queryText} onChange={setQueryText} onSearch={handleSearch} searching={searching} />
          </div>
          <button
            onClick={() => {
              setChatOpen((v) => !v);
              setSelectedJob(null);
            }}
            className={`shrink-0 rounded-lg px-4 py-2.5 text-sm font-medium ${
              chatOpen
                ? "bg-zinc-900 text-white dark:bg-white dark:text-zinc-900"
                : "border border-zinc-300 text-zinc-600 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-400 dark:hover:bg-zinc-800"
            }`}
          >
            💬 Asistente
          </button>
        </div>
      </div>

      <div className="flex flex-1 flex-col gap-4 lg:flex-row lg:items-start">
        <FiltersPanel filters={filters} onChange={handleFiltersChange} />

        <div className="flex flex-1 flex-col gap-3 min-w-0">
          {hasSearched && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-zinc-500">
                {searching ? "Buscando…" : `${jobs.length} ofertas encontradas`}
              </p>
              <select
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value as SortOrder)}
                className="rounded-lg border border-zinc-300 bg-white px-2 py-1 text-sm dark:border-zinc-700 dark:bg-zinc-900"
              >
                <option value="relevance">Relevancia</option>
                <option value="salary_desc">Salario (mayor)</option>
                <option value="salary_asc">Salario (menor)</option>
              </select>
            </div>
          )}

          {error && (
            <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
              {error}
            </p>
          )}

          {!hasSearched && !error && (
            <div className="flex flex-1 items-center justify-center rounded-xl border border-dashed border-zinc-300 p-16 text-center text-zinc-400 dark:border-zinc-700">
              Escribe una búsqueda en lenguaje natural para empezar.
            </div>
          )}

          {hasSearched && !searching && jobs.length === 0 && !error && (
            <div className="flex flex-1 items-center justify-center rounded-xl border border-dashed border-zinc-300 p-16 text-center text-zinc-400 dark:border-zinc-700">
              No se encontraron ofertas con estos filtros.
            </div>
          )}

          <ResultsList
            jobs={sortedJobs}
            selectedJob={selectedJob}
            onSelect={(job) => {
              setSelectedJob(job);
              setChatOpen(false);
            }}
          />
        </div>

        {selectedJob && (
          <JobDetailPanel
            job={selectedJob}
            country={filters.country}
            market={market}
            onClose={() => setSelectedJob(null)}
            isSaved={savedUrls.has(selectedJob.url)}
            onSaved={refreshSavedUrls}
          />
        )}

        {chatOpen && <ChatPanel onClose={() => setChatOpen(false)} onSelectKeyword={handleSelectKeyword} />}
      </div>
    </div>
  );
}
