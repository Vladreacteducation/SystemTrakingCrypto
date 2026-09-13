export function seriesColorVar(source: string): string {
  switch (source) {
    case "bybit":
      return "var(--series-bybit)";
    case "mexc":
      return "var(--series-mexc)";
    case "defillama":
      return "var(--series-defillama)";
    case "stakingrewards":
      return "var(--series-stakingrewards)";
    default:
      return "var(--muted)";
  }
}

export function formatApr(apr: number): string {
  return `${apr.toFixed(2)}%`;
}

export function formatDuration(days: number | null): string {
  if (!days) return "Flexible";
  return `${days}d`;
}

export function formatRelativeTime(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const minutes = Math.round(diffMs / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  return `${days}d ago`;
}
