import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../../api/client";

interface MonitoringPayload {
  status: string;
  environment: string;
  worker: boolean;
  ingest_stale: boolean;
  last_ingest_at: string | null;
  news_source: string;
  price_source: string;
  mock_price_mode: boolean;
  mock_news_mode: boolean;
  live_price_ready: boolean;
  live_news_ready: boolean;
  paper_trading_mode: boolean;
  alerts: string[];
}

interface HealthResponse {
  status: string;
  db: boolean;
  redis: boolean;
  worker: boolean;
  monitoring?: MonitoringPayload;
}

export function SystemStatus() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const { data: health } = await apiClient.get<HealthResponse>("/api/v1/health");
      return health;
    },
    refetchInterval: 30_000,
  });

  if (isLoading) {
    return <div className="h-10 animate-pulse rounded bg-slate-200" aria-busy="true" />;
  }
  if (isError || !data) {
    return (
      <p className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900" role="status">
        API unreachable — start backend with <code className="text-xs">make up</code>
      </p>
    );
  }

  const monitoring = data.monitoring;
  const checks = [
    { label: "Database", ok: data.db },
    { label: "Redis", ok: data.redis },
    { label: "Worker", ok: data.worker },
  ];

  return (
    <section className="space-y-2 rounded-lg border border-slate-200 bg-white px-4 py-3" aria-label="System health">
      <div className="flex flex-wrap items-center gap-3">
        <span className="text-sm font-semibold">System</span>
        <span
          className={`rounded-full px-2 py-0.5 text-xs ${
            data.status === "ok" ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-900"
          }`}
        >
          {data.status}
        </span>
        {checks.map((c) => (
          <span
            key={c.label}
            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs ${
              c.ok ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"
            }`}
            aria-label={`${c.label} ${c.ok ? "healthy" : "down"}`}
          >
            <span className={`h-2 w-2 rounded-full ${c.ok ? "bg-emerald-500" : "bg-red-500"}`} />
            {c.label}
          </span>
        ))}
      </div>

      {monitoring && (
        <div className="flex flex-wrap gap-2 text-xs text-slate-600">
          <Badge label={`News: ${monitoring.news_source}`} warn={monitoring.mock_news_mode} />
          <Badge label={`Prices: ${monitoring.price_source}`} warn={monitoring.mock_price_mode} />
          {monitoring.paper_trading_mode && <Badge label="Paper trading" warn />}
          {monitoring.last_ingest_at && (
            <span>Last ingest: {new Date(monitoring.last_ingest_at).toLocaleString()}</span>
          )}
        </div>
      )}

      {monitoring?.alerts?.length ? (
        <ul className="flex flex-wrap gap-2 text-xs" role="list">
          {monitoring.alerts.map((alert) => (
            <li key={alert} className="rounded bg-amber-100 px-2 py-0.5 text-amber-900">
              {alert.replace(/_/g, " ")}
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}

function Badge({ label, warn = false }: { label: string; warn?: boolean }) {
  return (
    <span className={`rounded-full px-2 py-0.5 ${warn ? "bg-amber-100 text-amber-900" : "bg-slate-100 text-slate-700"}`}>
      {label}
    </span>
  );
}
