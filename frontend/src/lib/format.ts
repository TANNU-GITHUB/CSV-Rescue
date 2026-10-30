export function formatNumber(n: number | undefined | null): string {
  if (n === undefined || n === null || Number.isNaN(n)) return "—";
  return new Intl.NumberFormat("en-IN").format(n);
}

export function formatPercent(n: number): string {
  return `${n.toFixed(1)}%`;
}

export function relativeTime(iso?: string): string {
  if (!iso) return "";
  const t = new Date(iso).getTime();
  const s = Math.max(0, (Date.now() - t) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`;
  return `${Math.floor(s / 86400)} d ago`;
}

export function visibleWhitespace(str: string): string {
  if (!str) return str;
  return str
    .replace(/^ +| +$/g, (m) => "·".repeat(m.length))
    .replace(/ {2,}/g, (m) => "·".repeat(m.length))
    .replace(/\t/g, "⇥")
    .replace(/\u00a0/g, "⍽");
}
