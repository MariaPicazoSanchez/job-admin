"use client";

import { useEffect, useState } from "react";
import { getSources } from "@/lib/api";
import type { SourcesStatus } from "@/lib/types";

const LABELS: Record<keyof SourcesStatus, string> = {
  linkedin: "LinkedIn",
  remotive: "Remotive",
  arbeitnow: "Arbeitnow",
  computrabajo: "Computrabajo",
  adzuna: "Adzuna",
};

export default function SourceBadges() {
  const [sources, setSources] = useState<SourcesStatus | null>(null);

  useEffect(() => {
    getSources().then(setSources).catch(() => setSources(null));
  }, []);

  if (!sources) return null;

  return (
    <div>
      <p className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500">
        Fuentes activas
      </p>
      <div className="flex flex-wrap gap-1.5">
        {(Object.keys(LABELS) as (keyof SourcesStatus)[]).map((key) => {
          const active = sources[key];
          return (
            <span
              key={key}
              title={key === "adzuna" && !active ? "Sin clave configurada" : undefined}
              className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                active
                  ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300"
                  : "bg-zinc-100 text-zinc-400 line-through dark:bg-zinc-800 dark:text-zinc-600"
              }`}
            >
              {LABELS[key]}
            </span>
          );
        })}
      </div>
    </div>
  );
}
