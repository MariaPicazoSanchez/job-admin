"use client";

import { useEffect, useState } from "react";
import { analyzeJob, saveJob } from "@/lib/api";
import type { Job, JobAnalysis, MarketInsights } from "@/lib/types";

const SIGNAL_STYLES: Record<string, string> = {
  danger: "border-red-200 bg-red-50 dark:border-red-900/50 dark:bg-red-950/40",
  warning: "border-amber-200 bg-amber-50 dark:border-amber-900/50 dark:bg-amber-950/40",
  positive: "border-emerald-200 bg-emerald-50 dark:border-emerald-900/50 dark:bg-emerald-950/40",
  info: "border-sky-200 bg-sky-50 dark:border-sky-900/50 dark:bg-sky-950/40",
};

interface Props {
  job: Job;
  country: string;
  market: MarketInsights | null;
  onClose: () => void;
  isSaved: boolean;
  onSaved: () => void;
}

export default function JobDetailPanel({ job, country, market, onClose, isSaved, onSaved }: Props) {
  const [analysis, setAnalysis] = useState<JobAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(isSaved);

  useEffect(() => {
    setAnalysis(null);
    setLoading(true);
    setSaved(isSaved);
    analyzeJob(job, country)
      .then(setAnalysis)
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [job.url, job.title, country]);

  async function handleSave() {
    setSaving(true);
    try {
      await saveJob(job, country);
      setSaved(true);
      onSaved();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex h-full w-full flex-col overflow-y-auto rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900 lg:w-[460px] lg:shrink-0">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold leading-snug">{job.title}</h2>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            {job.company} · {job.location}
          </p>
        </div>
        <button
          onClick={onClose}
          className="rounded-full p-1 text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800"
          aria-label="Cerrar"
        >
          ×
        </button>
      </div>

      {loading && <p className="text-sm text-zinc-500">Analizando oferta…</p>}

      {analysis && (
        <div className="flex flex-col gap-5">
          <div className="flex flex-wrap gap-1.5">
            {job.job_type && (
              <span className="rounded-full bg-sky-100 px-2 py-0.5 text-xs text-sky-800 dark:bg-sky-900/40 dark:text-sky-300">
                {{ remote: "Remoto", hybrid: "Híbrido", onsite: "Presencial" }[job.job_type]}
              </span>
            )}
            {analysis.seniority_detail && (
              <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-xs text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300">
                {analysis.seniority_detail}
              </span>
            )}
            {analysis.company_type && (
              <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
                {analysis.company_type}
              </span>
            )}
          </div>

          <section>
            <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-zinc-500">
              Análisis rápido
            </h3>
            <p className="text-sm leading-relaxed">{analysis.ai_summary}</p>
          </section>

          {analysis.salary_estimate && (
            <section className="rounded-lg border border-zinc-200 p-3 dark:border-zinc-800">
              <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-zinc-500">
                Estimación salarial
              </h3>
              <p className="text-base font-semibold">
                {analysis.salary_estimate.low.toLocaleString()} – {analysis.salary_estimate.high.toLocaleString()}{" "}
                {analysis.salary_estimate.currency}
              </p>
              <p className="text-xs text-zinc-500">{analysis.salary_estimate.basis}</p>
              {analysis.salary_estimate.comparison && (
                <p
                  className={`mt-1 text-xs font-medium ${
                    analysis.salary_estimate.comparison_kind === "positive"
                      ? "text-emerald-600"
                      : analysis.salary_estimate.comparison_kind === "negative"
                        ? "text-red-600"
                        : "text-zinc-500"
                  }`}
                >
                  {analysis.salary_estimate.comparison}
                </p>
              )}
            </section>
          )}

          {analysis.signals.length > 0 && (
            <section>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">
                Señales detectadas
              </h3>
              <div className="flex flex-col gap-2">
                {analysis.signals.map((s, i) => (
                  <div key={i} className={`rounded-lg border p-2.5 ${SIGNAL_STYLES[s.kind]}`}>
                    <p className="text-sm font-medium">{s.label}</p>
                    <p className="text-xs text-zinc-600 dark:text-zinc-400">{s.detail}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {(analysis.hard_skills.length > 0 || analysis.soft_skills.length > 0) && (
            <section>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">
                Skills
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {analysis.hard_skills.map((s) => (
                  <span key={s} className="rounded-full bg-zinc-900 px-2 py-0.5 text-xs text-white dark:bg-white dark:text-zinc-900">
                    {s}
                  </span>
                ))}
                {analysis.soft_skills.map((s) => (
                  <span
                    key={s}
                    className="rounded-full border border-zinc-300 px-2 py-0.5 text-xs text-zinc-600 dark:border-zinc-700 dark:text-zinc-400"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </section>
          )}

          {market && market.total > 1 && (
            <section className="rounded-lg border border-zinc-200 p-3 dark:border-zinc-800">
              <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-zinc-500">
                Insights de mercado ({market.total} ofertas)
              </h3>
              {market.median_salary && (
                <p className="text-sm">
                  Salario mediano: <strong>{market.median_salary.toLocaleString()} {market.salary_currency}</strong>
                </p>
              )}
              {market.avg_years != null && (
                <p className="text-sm">Media de experiencia requerida: {market.avg_years} años</p>
              )}
              {market.top_skills.length > 0 && (
                <div className="mt-2 flex flex-col gap-1">
                  {market.top_skills.map(([skill, pct]) => (
                    <div key={skill} className="flex items-center gap-2 text-xs">
                      <span className="w-24 shrink-0 truncate">{skill}</span>
                      <div className="h-1.5 flex-1 rounded-full bg-zinc-100 dark:bg-zinc-800">
                        <div className="h-1.5 rounded-full bg-zinc-900 dark:bg-white" style={{ width: `${pct}%` }} />
                      </div>
                      <span className="w-8 text-right text-zinc-500">{pct}%</span>
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}

          <section>
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">
              Descripción
            </h3>
            {Object.keys(analysis.description_blocks).length > 0 ? (
              <div className="flex flex-col gap-3">
                {Object.entries(analysis.description_blocks).map(([label, body]) => (
                  <div key={label}>
                    <p className="text-sm font-semibold">{label}</p>
                    <p className="whitespace-pre-line text-sm text-zinc-600 dark:text-zinc-400">{body}</p>
                  </div>
                ))}
              </div>
            ) : analysis.clean_description ? (
              <p className="whitespace-pre-line text-sm text-zinc-600 dark:text-zinc-400">
                {analysis.clean_description.slice(0, 1200)}
              </p>
            ) : (
              <p className="text-sm text-zinc-400">Descripción no disponible.</p>
            )}
          </section>

          <div className="sticky bottom-0 mt-2 flex gap-2 border-t border-zinc-200 bg-white pt-3 dark:border-zinc-800 dark:bg-zinc-900">
            <button
              onClick={handleSave}
              disabled={saved || saving}
              className="flex-1 rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60 dark:bg-white dark:text-zinc-900"
            >
              {saved ? "Guardada en Mis Ofertas" : saving ? "Guardando…" : "Guardar oferta"}
            </button>
            <a
              href={job.url}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-800"
            >
              Ver oferta completa
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
