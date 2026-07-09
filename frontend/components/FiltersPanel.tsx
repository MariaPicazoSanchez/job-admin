"use client";

import { DEFAULT_FILTERS, EXPERIENCIA, MONEDAS, PAISES, TIPOS_TRABAJO } from "@/lib/constants";
import type { SearchFilters } from "@/lib/types";
import SourceBadges from "./SourceBadges";

interface Props {
  filters: SearchFilters;
  onChange: (filters: SearchFilters) => void;
}

export default function FiltersPanel({ filters, onChange }: Props) {
  const set = <K extends keyof SearchFilters>(key: K, value: SearchFilters[K]) =>
    onChange({ ...filters, [key]: value });

  return (
    <aside className="flex w-full flex-col gap-5 rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900 lg:w-72 lg:shrink-0">
      <div>
        <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-zinc-500">
          País
        </label>
        <select
          value={filters.country}
          onChange={(e) => set("country", e.target.value)}
          className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800"
        >
          {PAISES.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-zinc-500">
          Tipo de trabajo
        </label>
        <div className="flex flex-wrap gap-1.5">
          {TIPOS_TRABAJO.map((t) => (
            <button
              key={t}
              onClick={() => set("jobType", t)}
              className={`rounded-full px-3 py-1 text-sm transition-colors ${
                filters.jobType === t
                  ? "bg-zinc-900 text-white dark:bg-white dark:text-zinc-900"
                  : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-400"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-zinc-500">
          Experiencia
        </label>
        <select
          value={filters.experience}
          onChange={(e) => set("experience", e.target.value)}
          className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800"
        >
          {EXPERIENCIA.map((e) => (
            <option key={e} value={e}>
              {e}
            </option>
          ))}
        </select>
      </div>

      <div>
        <div className="mb-1 flex items-center justify-between">
          <label className="block text-xs font-medium uppercase tracking-wide text-zinc-500">
            Salario mínimo
          </label>
          <select
            value={filters.currency}
            onChange={(e) => set("currency", e.target.value)}
            className="rounded border border-zinc-300 bg-white px-1.5 py-0.5 text-xs dark:border-zinc-700 dark:bg-zinc-800"
          >
            {MONEDAS.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>
        <input
          type="range"
          min={0}
          max={150000}
          step={5000}
          value={filters.salaryMin}
          onChange={(e) => set("salaryMin", Number(e.target.value))}
          className="w-full accent-zinc-900 dark:accent-white"
        />
        <p className="text-right text-sm text-zinc-600 dark:text-zinc-400">
          {filters.salaryMin > 0 ? `${filters.salaryMin.toLocaleString()} ${filters.currency}` : "Sin mínimo"}
        </p>
      </div>

      <button
        onClick={() => onChange({ ...DEFAULT_FILTERS })}
        className="rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-600 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-400 dark:hover:bg-zinc-800"
      >
        Limpiar filtros
      </button>

      <SourceBadges />
    </aside>
  );
}
