export function StatusDot({ stale }: { stale?: boolean }) {
  return (
    <span
      className={`inline-block h-2.5 w-2.5 rounded-full ${stale ? "bg-amber-400" : "bg-emerald-500"}`}
      aria-label={stale ? "Data stale" : "Live"}
      title={stale ? "No update in 5+ minutes" : "Live"}
    />
  );
}
