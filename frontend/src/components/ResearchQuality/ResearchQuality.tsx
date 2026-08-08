import { useOutcomeMetrics, type BucketReliability } from "../../hooks/useOutcomeMetrics";
import { ReliabilityBar } from "../ui/ReliabilityBar";

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

  const topTickers: [string, number][] = Object.entries(data.precision_by_ticker)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);

  const bucketRows: [string, BucketReliability][] = Object.entries(data.bucket_reliability);

  return (
    <section className="space-y-4 rounded-lg border border-slate-200 bg-white p-4" aria-labelledby="research-quality-heading">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="research-quality-heading" className="text-xl font-semibold">
          Research Quality
        </h2>
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-700">
          {data.methodology.replace(/_/g, " ")}
        </span>
      </div>
      <p className="text-xs text-slate-500">{data.note}</p>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Resolved outcomes" value={String(data.total_resolved)} />
        <MetricCard
          label="Hit rate (95% CI)"
          value={`${pct(data.hit_rate)} · ${pct(data.hit_rate_ci95[0])}–${pct(data.hit_rate_ci95[1])}`}
        />
        <MetricCard label="Mean Brier" value={data.mean_brier.toFixed(3)} />
        <MetricCard
          label="Model ready"
          value={data.ml_ready ? "Yes" : "Collecting data"}
          highlight={data.ml_ready}
        />
        <MetricCard label="Mean return" value={pct(data.mean_return_pct)} />
        <MetricCard label="Return volatility" value={pct(data.return_volatility)} />
        <MetricCard label="Max drawdown" value={pct(data.max_drawdown_pct)} />
        <MetricCard label="Calibration error" value={pct(data.calibration_error)} />
      </div>

      <div>
        <h3 className="mb-2 text-sm font-semibold">Profit Quality</h3>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard label="Expectancy" value={pct(data.expectancy)} />
          <MetricCard label="Profit factor" value={data.profit_factor.toFixed(2)} />
          <MetricCard label="Mean win" value={pct(data.mean_win_pct)} />
          <MetricCard label="Mean loss" value={pct(data.mean_loss_pct)} />
        </div>
      </div>

      <p className="text-xs text-slate-600">
        Rolling 30: {data.rolling_30.samples} outcomes · {pct(data.rolling_30.hit_rate)} hit rate ·{" "}
        {data.rolling_30.mean_brier.toFixed(3)} Brier
      </p>

      {Object.keys(data.bucket_reliability).length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-semibold">Confidence bucket reliability</h3>
          <div className="space-y-3">
            {bucketRows.map(([bucket, stats]) => (
              <ReliabilityBar
                key={bucket}
                label={bucket}
                predicted={stats.mean_predicted}
                observed={stats.observed_hit_rate}
              />
            ))}
          </div>
          <div className="mt-3 overflow-x-auto rounded border">
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
                {bucketRows.map(([bucket, stats]) => (
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

      {Object.keys(data.by_theme_bucket).length > 0 && (
        <BreakdownTable title="By theme bucket" rows={data.by_theme_bucket} />
      )}
      {Object.keys(data.by_regime).length > 0 && (
        <BreakdownTable title="By regime" rows={data.by_regime} />
      )}
      {Object.keys(data.sector_contribution).length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-semibold">Sector contribution</h3>
          <ul className="flex flex-wrap gap-2">
            {Object.entries(data.sector_contribution).map(([sector, value]) => (
              <li key={sector} className="rounded-full bg-slate-100 px-3 py-1 text-xs">
                {sector}: {pct(value)}
              </li>
            ))}
          </ul>
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

function BreakdownTable({
  title,
  rows,
}: {
  title: string;
  rows: Record<string, { samples: number; hit_rate: number; expectancy: number; profit_factor: number }>;
}) {
  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold">{title}</h3>
      <div className="overflow-x-auto rounded border">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-100">
            <tr>
              <th className="p-2">Key</th>
              <th className="p-2">Samples</th>
              <th className="p-2">Hit rate</th>
              <th className="p-2">Expectancy</th>
              <th className="p-2">Profit factor</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(rows).map(([key, stats]) => (
              <tr key={key} className="border-t">
                <td className="p-2 font-medium">{key}</td>
                <td className="p-2">{stats.samples}</td>
                <td className="p-2">{pct(stats.hit_rate)}</td>
                <td className="p-2">{pct(stats.expectancy)}</td>
                <td className="p-2">{stats.profit_factor.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
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
