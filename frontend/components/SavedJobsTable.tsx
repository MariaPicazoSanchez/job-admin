"use client";

import type { SavedJob } from "@/lib/types";

const ESTADO_STYLES: Record<string, string> = {
  Aceptada: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300",
  Rechazada: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
  Ghosted: "bg-zinc-200 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
};

const INTERES_STYLES: Record<string, string> = {
  Alto: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300",
  Medio: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300",
  Bajo: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
};

interface Props {
  jobs: SavedJob[];
  selectedId: string | null;
  onSelect: (job: SavedJob) => void;
}

export default function SavedJobsTable({ jobs, selectedId, onSelect }: Props) {
  return (
    <div className="overflow-x-auto rounded-xl border border-zinc-200 dark:border-zinc-800">
      <table className="w-full min-w-[720px] text-sm">
        <thead className="bg-zinc-50 text-left text-xs uppercase tracking-wide text-zinc-500 dark:bg-zinc-900">
          <tr>
            <th className="px-3 py-2">Empresa</th>
            <th className="px-3 py-2">Puesto</th>
            <th className="px-3 py-2">Localidad</th>
            <th className="px-3 py-2">Experiencia</th>
            <th className="px-3 py-2">Estado</th>
            <th className="px-3 py-2">Interés</th>
            <th className="px-3 py-2">Aplicado</th>
            <th className="px-3 py-2">Observaciones</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr
              key={job.id}
              onClick={() => onSelect(job)}
              className={`cursor-pointer border-t border-zinc-100 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-800/50 ${
                selectedId === job.id ? "bg-zinc-50 dark:bg-zinc-800/70" : ""
              }`}
            >
              <td className="px-3 py-2">{job.company}</td>
              <td className="px-3 py-2 font-medium">{job.title}</td>
              <td className="px-3 py-2">{job.location}</td>
              <td className="px-3 py-2">{job.seniority}</td>
              <td className="px-3 py-2">
                <span className={`rounded-full px-2 py-0.5 text-xs ${ESTADO_STYLES[job.status] ?? "bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-300"}`}>
                  {job.status}
                </span>
              </td>
              <td className="px-3 py-2">
                <span className={`rounded-full px-2 py-0.5 text-xs ${INTERES_STYLES[job.interest] ?? ""}`}>
                  {job.interest}
                </span>
              </td>
              <td className="px-3 py-2 text-zinc-500">{job.applied_date || "—"}</td>
              <td className="max-w-[220px] truncate px-3 py-2 text-zinc-500">{job.notes || "—"}</td>
            </tr>
          ))}
          {jobs.length === 0 && (
            <tr>
              <td colSpan={8} className="px-3 py-8 text-center text-zinc-400">
                Todavía no has guardado ninguna oferta.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
