import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../../api/client";

interface HealthResponse {
  status: string;
  db: boolean;
  redis: boolean;
  worker: boolean;
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

  const checks = [
    { label: "Database", ok: data.db },
    { label: "Redis", ok: data.redis },
    { label: "Worker", ok: data.worker },
  ];

  return (
    <section
      className="flex flex-wrap items-center gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3"
      aria-label="System health"
    >
      <span className="text-sm font-semibold">System</span>
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
    </section>
  );
}
