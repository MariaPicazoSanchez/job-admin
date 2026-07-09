"use client";

import { formatPostedDate } from "@/lib/format";
import type { Job } from "@/lib/types";

function salaryDisplay(job: Job): string {
  if (job.salary_min && job.salary_max) {
    return `${job.salary_min.toLocaleString()} – ${job.salary_max.toLocaleString()} ${job.currency}`;
  }
  if (job.salary_min) return `Desde ${job.salary_min.toLocaleString()} ${job.currency}`;
  if (job.salary_max) return `Hasta ${job.salary_max.toLocaleString()} ${job.currency}`;
  return "Salario no indicado";
}

const SENIORITY_LABEL: Record<string, string> = {
  internship: "Prácticas",
  junior: "Junior",
  mid: "Mid",
  senior: "Senior",
  lead: "Lead",
};

const MODALIDAD_LABEL: Record<string, string> = {
  remote: "Remoto",
  hybrid: "Híbrido",
  onsite: "Presencial",
};

interface Props {
  job: Job;
  selected?: boolean;
  onClick: () => void;
}

export default function JobCard({ job, selected, onClick }: Props) {
  const seniority = SENIORITY_LABEL[job.seniority_level] ?? "";
  const modalidad = MODALIDAD_LABEL[job.job_type] ?? "";
  const posted = formatPostedDate(job.posted);

  return (
    <button
      onClick={onClick}
      className={`w-full rounded-xl border p-4 text-left transition-colors ${
        selected
          ? "border-zinc-900 bg-zinc-50 dark:border-white dark:bg-zinc-800"
          : "border-zinc-200 bg-white hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-semibold leading-snug">{job.title}</h3>
        <span className="shrink-0 rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
          {job.source}
        </span>
      </div>
      <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
        {job.company} · {job.location}
      </p>
      <p className="mt-2 text-sm font-medium">{salaryDisplay(job)}</p>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {seniority && (
          <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-xs text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300">
            {seniority}
          </span>
        )}
        {modalidad && (
          <span className="rounded-full bg-sky-100 px-2 py-0.5 text-xs text-sky-800 dark:bg-sky-900/40 dark:text-sky-300">
            {modalidad}
          </span>
        )}
      </div>
      {posted && <p className="mt-2 text-xs text-zinc-400">{posted}</p>}
    </button>
  );
}
