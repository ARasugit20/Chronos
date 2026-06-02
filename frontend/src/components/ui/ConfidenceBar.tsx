export function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="w-full" aria-label={`Confidence ${pct} percent`}>
      <div className="mb-1 flex justify-between text-xs text-slate-600">
        <span>Calibrated</span>
        <span>{pct}%</span>
      </div>
      <div className="h-2 w-full rounded bg-slate-200">
        <div className="h-2 rounded bg-indigo-500 transition-all" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
