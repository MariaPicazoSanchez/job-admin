const RTF = new Intl.RelativeTimeFormat("es", { numeric: "auto" });

const UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
  ["year", 60 * 60 * 24 * 365],
  ["month", 60 * 60 * 24 * 30],
  ["week", 60 * 60 * 24 * 7],
  ["day", 60 * 60 * 24],
  ["hour", 60 * 60],
  ["minute", 60],
];

export function formatPostedDate(posted: string | undefined): string | null {
  if (!posted) return null;
  const date = new Date(posted);
  if (Number.isNaN(date.getTime())) return null;

  const diffSeconds = (date.getTime() - Date.now()) / 1000;
  const absSeconds = Math.abs(diffSeconds);

  if (absSeconds < 60) return "Publicada hace un momento";

  for (const [unit, secondsInUnit] of UNITS) {
    if (absSeconds >= secondsInUnit || unit === "minute") {
      const value = Math.round(diffSeconds / secondsInUnit);
      return `Publicada ${RTF.format(value, unit)}`;
    }
  }
  return null;
}
