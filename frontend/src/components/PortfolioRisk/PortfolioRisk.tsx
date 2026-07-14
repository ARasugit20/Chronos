import { usePortfolio } from "../../hooks/usePortfolio";

function pct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function PortfolioRisk() {
  const { data, isLoading, isError } = usePortfolio();

  if (isLoading) {
    return <div className="h-36 animate-pulse rounded-lg bg-slate-200" aria-busy="true" />;
  }
  if (isError || !data) {
    return (
      <section className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        Portfolio snapshot unavailable.
      </section>
    );
  }

  const sectorRows = Object.entries(data.sector_exposure);

  return (
    <section
      className="space-y-4 rounded-lg border border-slate-200 bg-white p-4"
      aria-labelledby="portfolio-risk-heading"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="portfolio-risk-heading" className="text-xl font-semibold">
          Portfolio & Risk
        </h2>
        <span className="text-xs text-slate-500">{data.open_recommendations} open positions</span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Available cash" value={`$${data.available_cash.toFixed(2)}`} />
        <MetricCard label="Deployed" value={`$${data.total_deployed.toFixed(2)} (${pct(data.pct_deployed)})`} />
        <MetricCard label="Largest position" value={pct(data.largest_position_pct)} />
        <MetricCard label="Concentration HHI" value={data.concentration_hhi.toFixed(3)} />
      </div>

      {data.ticker_exposure.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-semibold">Ticker exposure</h3>
          <div className="overflow-x-auto rounded border">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-100">
                <tr>
                  <th className="p-2">Ticker</th>
                  <th className="p-2">Sector</th>
                  <th className="p-2">Amount</th>
                  <th className="p-2">% Portfolio</th>
                  <th className="p-2">Cap used</th>
                  <th className="p-2">Headroom</th>
                </tr>
              </thead>
              <tbody>
                {data.ticker_exposure.map((row) => (
                  <tr key={row.ticker} className="border-t">
                    <td className="p-2 font-medium">{row.ticker}</td>
                    <td className="p-2 capitalize">{row.sector.replace(/_/g, " ")}</td>
                    <td className="p-2">${row.amount_usd.toFixed(2)}</td>
                    <td className="p-2">{pct(row.pct_portfolio)}</td>
                    <td className="p-2">
                      <CapBar value={Math.min(row.pct_ticker_cap, 1)} />
                    </td>
                    <td className="p-2">${row.headroom_usd.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {sectorRows.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-semibold">Sector exposure</h3>
          <ul className="flex flex-wrap gap-2">
            {sectorRows.map(([sector, exposure]) => (
              <li key={sector} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-800">
                {sector.replace(/_/g, " ")}: {pct(exposure)}
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="text-xs text-slate-500">
        Limits: {pct(data.max_ticker_pct)} per ticker · {pct(data.sector_cap_pct)} per sector
        {data.paper_trading_mode ? " · paper mode" : ""}
      </p>
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 p-3">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </div>
  );
}

function CapBar({ value }: { value: number }) {
  const width = `${Math.round(value * 100)}%`;
  const tone = value >= 0.9 ? "bg-red-500" : value >= 0.7 ? "bg-amber-500" : "bg-emerald-500";
  return (
    <div className="h-2 w-24 rounded bg-slate-200" aria-hidden="true">
      <div className={`h-2 rounded ${tone}`} style={{ width }} />
    </div>
  );
}
