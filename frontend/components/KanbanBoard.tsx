"use client";

import { ESTADOS } from "@/lib/constants";
import type { SavedJob } from "@/lib/types";

interface Props {
  jobs: SavedJob[];
  onSelect: (job: SavedJob) => void;
  onMove: (job: SavedJob, newStatus: string) => void;
}

export default function KanbanBoard({ jobs, onSelect, onMove }: Props) {
  return (
    <div className="flex gap-3 overflow-x-auto pb-3">
      {ESTADOS.map((estado, colIndex) => {
        const items = jobs.filter((j) => j.status === estado);
        return (
          <div key={estado} className="flex w-64 shrink-0 flex-col gap-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
              {estado} <span className="text-zinc-400">({items.length})</span>
            </p>
            <div className="flex flex-col gap-2">
              {items.map((job) => (
                <div
                  key={job.id}
                  className="cursor-pointer rounded-lg border border-zinc-200 bg-white p-2.5 text-sm hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700"
                  onClick={() => onSelect(job)}
                >
                  <p className="font-medium leading-snug">{job.title}</p>
                  <p className="text-xs text-zinc-500">{job.company}</p>
                  <div className="mt-2 flex justify-between">
                    <button
                      disabled={colIndex === 0}
                      onClick={(e) => {
                        e.stopPropagation();
                        onMove(job, ESTADOS[colIndex - 1]);
                      }}
                      className="rounded px-2 text-xs text-zinc-500 hover:bg-zinc-100 disabled:opacity-30 dark:hover:bg-zinc-800"
                    >
                      ◀
                    </button>
                    <button
                      disabled={colIndex === ESTADOS.length - 1}
                      onClick={(e) => {
                        e.stopPropagation();
                        onMove(job, ESTADOS[colIndex + 1]);
                      }}
                      className="rounded px-2 text-xs text-zinc-500 hover:bg-zinc-100 disabled:opacity-30 dark:hover:bg-zinc-800"
                    >
                      ▶
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
