"use client";

import { useEffect, useState } from "react";
import { ESTADOS, INTERES } from "@/lib/constants";
import type { SavedJob } from "@/lib/types";

interface Props {
  job: SavedJob;
  onClose: () => void;
  onSave: (fields: Partial<SavedJob>) => Promise<void>;
  onDelete: () => Promise<void>;
}

export default function JobEditPanel({ job, onClose, onSave, onDelete }: Props) {
  const [form, setForm] = useState({
    status: job.status,
    interest: job.interest,
    applied_date: job.applied_date,
    interview_date: job.interview_date,
    salary_offered: job.salary_offered,
    contact: job.contact,
    notes: job.notes,
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setForm({
      status: job.status,
      interest: job.interest,
      applied_date: job.applied_date,
      interview_date: job.interview_date,
      salary_offered: job.salary_offered,
      contact: job.contact,
      notes: job.notes,
    });
  }, [job]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleSave() {
    setSaving(true);
    try {
      await onSave(form);
    } finally {
      setSaving(false);
    }
  }

  const today = () => new Date().toISOString().slice(0, 10);

  return (
    <div className="flex h-full w-full flex-col gap-5 overflow-y-auto border-l border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900 lg:w-[420px] lg:shrink-0">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold leading-snug">{job.title}</h2>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            {job.company} · {job.location}
          </p>
        </div>
        <button onClick={onClose} className="rounded-full p-1 text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800" aria-label="Cerrar">
          ×
        </button>
      </div>

      <section>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">Datos de la oferta</h3>
        <p className="text-sm">{job.salary_display}</p>
        {job.salary_estimate && <p className="text-xs text-zinc-500">Estimación: {job.salary_estimate}</p>}
        {job.seniority && <p className="text-xs text-zinc-500">Seniority: {job.seniority}</p>}
        {job.skills.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {job.skills.map((s) => (
              <span key={s} className="rounded-full bg-zinc-900 px-2 py-0.5 text-xs text-white dark:bg-white dark:text-zinc-900">
                {s}
              </span>
            ))}
          </div>
        )}
      </section>

      <section className="flex flex-col gap-3">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Seguimiento</h3>

        <div>
          <label className="mb-1 block text-xs text-zinc-500">Estado</label>
          <select
            value={form.status}
            onChange={(e) => setForm({ ...form, status: e.target.value })}
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800"
          >
            {ESTADOS.map((e) => (
              <option key={e} value={e}>
                {e}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs text-zinc-500">Nivel de interés</label>
          <select
            value={form.interest}
            onChange={(e) => setForm({ ...form, interest: e.target.value })}
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800"
          >
            {INTERES.map((i) => (
              <option key={i} value={i}>
                {i}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs text-zinc-500">Fecha de solicitud</label>
          <div className="flex gap-2">
            <input
              type="date"
              value={form.applied_date}
              onChange={(e) => setForm({ ...form, applied_date: e.target.value })}
              className="flex-1 rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800"
            />
            <button
              onClick={() => setForm({ ...form, applied_date: today() })}
              className="rounded-lg border border-zinc-300 px-3 text-sm dark:border-zinc-700"
            >
              Hoy
            </button>
          </div>
        </div>

        <div>
          <label className="mb-1 block text-xs text-zinc-500">Fecha de entrevista</label>
          <div className="flex gap-2">
            <input
              type="date"
              value={form.interview_date}
              onChange={(e) => setForm({ ...form, interview_date: e.target.value })}
              className="flex-1 rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800"
            />
            <button
              onClick={() => setForm({ ...form, interview_date: today() })}
              className="rounded-lg border border-zinc-300 px-3 text-sm dark:border-zinc-700"
            >
              Hoy
            </button>
          </div>
        </div>

        <div>
          <label className="mb-1 block text-xs text-zinc-500">Salario ofrecido</label>
          <input
            type="text"
            value={form.salary_offered}
            onChange={(e) => setForm({ ...form, salary_offered: e.target.value })}
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800"
          />
        </div>

        <div>
          <label className="mb-1 block text-xs text-zinc-500">Persona de contacto</label>
          <input
            type="text"
            value={form.contact}
            onChange={(e) => setForm({ ...form, contact: e.target.value })}
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800"
          />
        </div>

        <div>
          <label className="mb-1 block text-xs text-zinc-500">Observaciones</label>
          <textarea
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            rows={3}
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800"
          />
        </div>
      </section>

      {job.timeline.length > 0 && (
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">Historial</h3>
          <ul className="flex flex-col gap-1">
            {job.timeline.slice(-8).reverse().map((ev, i) => (
              <li key={i} className="text-xs text-zinc-500">
                <span className="font-medium text-zinc-700 dark:text-zinc-300">{ev.date}</span> — {ev.event}
              </li>
            ))}
          </ul>
        </section>
      )}

      <div className="sticky bottom-0 mt-auto flex gap-2 border-t border-zinc-200 bg-white pt-3 dark:border-zinc-800 dark:bg-zinc-900">
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex-1 rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60 dark:bg-white dark:text-zinc-900"
        >
          {saving ? "Guardando…" : "Guardar cambios"}
        </button>
        <button
          onClick={onDelete}
          className="rounded-lg border border-red-300 px-3 text-sm font-medium text-red-600 hover:bg-red-50 dark:border-red-900 dark:text-red-400 dark:hover:bg-red-950/40"
        >
          Eliminar
        </button>
      </div>
    </div>
  );
}
