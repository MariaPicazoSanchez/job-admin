"use client";

import { useCallback, useEffect, useState } from "react";
import { deleteSavedJob, getJobStats, listSavedJobs, updateSavedJob } from "@/lib/api";
import type { JobStats, SavedJob } from "@/lib/types";
import StatsBar from "@/components/StatsBar";
import SavedJobsTable from "@/components/SavedJobsTable";
import KanbanBoard from "@/components/KanbanBoard";
import JobEditPanel from "@/components/JobEditPanel";

type ViewMode = "table" | "kanban";

export default function MisOfertasPage() {
  const [jobs, setJobs] = useState<SavedJob[]>([]);
  const [stats, setStats] = useState<JobStats | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("table");
  const [selected, setSelected] = useState<SavedJob | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const [jobsData, statsData] = await Promise.all([listSavedJobs(), getJobStats()]);
    setJobs(jobsData);
    setStats(statsData);
  }, []);

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, [refresh]);

  async function handleSaveEdit(fields: Partial<SavedJob>) {
    if (!selected) return;
    const updated = await updateSavedJob(selected.id, fields);
    setSelected(updated);
    await refresh();
  }

  async function handleDelete() {
    if (!selected) return;
    await deleteSavedJob(selected.id);
    setSelected(null);
    await refresh();
  }

  async function handleMove(job: SavedJob, newStatus: string) {
    await updateSavedJob(job.id, { status: newStatus });
    await refresh();
  }

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-4 p-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Mis Ofertas</h1>
        <div className="flex rounded-full border border-zinc-300 p-0.5 text-sm dark:border-zinc-700">
          {(["table", "kanban"] as ViewMode[]).map((mode) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={`rounded-full px-3 py-1 ${
                viewMode === mode
                  ? "bg-zinc-900 text-white dark:bg-white dark:text-zinc-900"
                  : "text-zinc-500"
              }`}
            >
              {mode === "table" ? "Tabla" : "Kanban"}
            </button>
          ))}
        </div>
      </div>

      {stats && <StatsBar stats={stats} />}

      {loading ? (
        <p className="text-sm text-zinc-500">Cargando…</p>
      ) : (
        <div className="flex flex-1 gap-4">
          <div className="min-w-0 flex-1">
            {viewMode === "table" ? (
              <SavedJobsTable jobs={jobs} selectedId={selected?.id ?? null} onSelect={setSelected} />
            ) : (
              <KanbanBoard jobs={jobs} onSelect={setSelected} onMove={handleMove} />
            )}
          </div>

          {selected && (
            <JobEditPanel
              job={selected}
              onClose={() => setSelected(null)}
              onSave={handleSaveEdit}
              onDelete={handleDelete}
            />
          )}
        </div>
      )}
    </div>
  );
}
