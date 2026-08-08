function pct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function ReliabilityBar({
  predicted,
  observed,
  label,
}: {
  predicted: number;
  observed: number;
  label: string;
}) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-slate-600">
        <span>{label}</span>
        <span>
          pred {pct(predicted)} · obs {pct(observed)}
        </span>
      </div>
      <div className="relative h-2 w-full rounded bg-slate-200">
        <div
          className="absolute h-2 rounded bg-indigo-400"
          style={{ width: `${Math.min(100, predicted * 100)}%` }}
        />
        <div
          className="absolute top-0 h-2 rounded border border-emerald-600 bg-emerald-300/60"
          style={{ width: `${Math.min(100, observed * 100)}%` }}
        />
      </div>
    </div>
  );
}
