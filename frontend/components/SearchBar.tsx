"use client";

interface Props {
  value: string;
  onChange: (value: string) => void;
  onSearch: (prompt: string) => void;
  searching: boolean;
}

export default function SearchBar({ value, onChange, onSearch, searching }: Props) {
  function submit() {
    if (value.trim()) onSearch(value.trim());
  }

  return (
    <div className="flex gap-2">
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && submit()}
        placeholder="Ej: Desarrollador Python senior, remoto, mínimo 60k EUR"
        className="flex-1 rounded-lg border border-zinc-300 bg-white px-4 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-900"
      />
      <button
        onClick={submit}
        disabled={searching}
        className="rounded-lg bg-zinc-900 px-5 py-2.5 text-sm font-medium text-white disabled:opacity-60 dark:bg-white dark:text-zinc-900"
      >
        {searching ? "Buscando…" : "Buscar"}
      </button>
    </div>
  );
}
