import { useOutcomeMetrics } from "../../hooks/useOutcomeMetrics";

function pct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function ResearchQuality() {
  const { data, isLoading, isError } = useOutcomeMetrics();

  if (isLoading) {
    return <div className="h-36 animate-pulse rounded-lg bg-slate-200" aria-busy="true" />;
  }
  if (isError || !data) {
    return (
      <section className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        Outcome metrics unavailable. Metrics appear after recommendations resolve.
      </section>
    );
  }

  const topTickers = Object.entries(data.precision_by_ticker)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);

  return (
    <section className="space-y-4 rounded-lg border border-slate-200 bg-white p-4" aria-labelledby="research-quality-heading">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="research-quality-heading" className="text-xl font-semibold">
          Research Quality
        </h2>
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-700">
          {data.methodology.replaceAll("_", " ")}
        </span>
      </div>
      <p className="text-xs text-slate-500">{data.note}</p>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Resolved outcomes" value={String(data.total_resolved)} />
        <MetricCard label="Hit rate" value={pct(data.hit_rate)} />
        <MetricCard label="Mean Brier" value={data.mean_brier.toFixed(3)} />
        <MetricCard
          label="Model ready"
          value={data.ml_ready ? "Yes" : "Collecting data"}
          highlight={data.ml_ready}
        />
      </div>

      {Object.keys(data.bucket_reliability).length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-semibold">Confidence bucket reliability</h3>
          <div className="overflow-x-auto rounded border">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-100">
                <tr>
                  <th className="p-2">Bucket</th>
                  <th className="p-2">Samples</th>
                  <th className="p-2">Predicted</th>
                  <th className="p-2">Observed</th>
                  <th className="p-2">Gap</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(data.bucket_reliability).map(([bucket, stats]) => (
                  <tr key={bucket} className="border-t">
                    <td className="p-2 font-medium capitalize">{bucket}</td>
                    <td className="p-2">{stats.samples}</td>
                    <td className="p-2">{pct(stats.mean_predicted)}</td>
                    <td className="p-2">{pct(stats.observed_hit_rate)}</td>
                    <td className="p-2">{pct(stats.calibration_gap)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {topTickers.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-semibold">Ticker precision (n≥3)</h3>
          <ul className="flex flex-wrap gap-2">
            {topTickers.map(([ticker, precision]) => (
              <li key={ticker} className="rounded-full bg-indigo-50 px-3 py-1 text-xs text-indigo-900">
                {ticker}: {pct(precision)}
              </li>
            ))}
          </ul>
        </div>
      )}

      {data.paper_trading && (
        <p className="text-xs text-slate-500">Paper trading mode is active — outcomes use the shadow approval track.</p>
      )}
    </section>
  );
}

function MetricCard({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className={`rounded-lg border p-3 ${highlight ? "border-emerald-200 bg-emerald-50" : "border-slate-200"}`}>
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </div>
  );
}
