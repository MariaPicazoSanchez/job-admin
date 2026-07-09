"use client";

import type { JobStats } from "@/lib/types";

interface Props {
  stats: JobStats;
}

export default function StatsBar({ stats }: Props) {
  const items = [
    { label: "Guardadas", value: stats.total },
    { label: "Enviadas", value: stats.enviadas },
    { label: "Entrevistas", value: stats.entrevistas },
    { label: "Activas", value: stats.activas },
    { label: "% Respuesta", value: `${stats.ratio}%` },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
      {items.map((item) => (
        <div
          key={item.label}
          className="rounded-xl border border-zinc-200 bg-white p-3 text-center dark:border-zinc-800 dark:bg-zinc-900"
        >
          <p className="text-xl font-semibold">{item.value}</p>
          <p className="text-xs text-zinc-500">{item.label}</p>
        </div>
      ))}
    </div>
  );
}
