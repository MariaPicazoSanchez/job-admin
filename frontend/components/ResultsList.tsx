"use client";

import { useEffect, useRef, useState } from "react";
import type { Job } from "@/lib/types";
import JobCard from "./JobCard";

const BATCH = 10;

interface Props {
  jobs: Job[];
  selectedJob: Job | null;
  onSelect: (job: Job) => void;
}

export default function ResultsList({ jobs, selectedJob, onSelect }: Props) {
  const [visibleCount, setVisibleCount] = useState(BATCH);
  const sentinelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setVisibleCount((prev) => Math.min(Math.max(prev, BATCH), Math.max(jobs.length, BATCH)));
  }, [jobs.length]);

  useEffect(() => {
    const el = sentinelRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          setVisibleCount((prev) => Math.min(prev + BATCH, jobs.length));
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [jobs.length]);

  const visible = jobs.slice(0, visibleCount);
  const remaining = jobs.length - visible.length;

  return (
    <div className="flex flex-col gap-3">
      {visible.map((job) => (
        <JobCard
          key={`${job.source}-${job.url}`}
          job={job}
          selected={selectedJob?.url === job.url}
          onClick={() => onSelect(job)}
        />
      ))}
      {remaining > 0 && (
        <div ref={sentinelRef} className="py-4 text-center text-sm text-zinc-400">
          ↓ {remaining} ofertas más
        </div>
      )}
    </div>
  );
}
