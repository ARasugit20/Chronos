import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { fetchAuditTrail } from "../api/recommendations";

interface TimelineStep {
  title: string;
  detail: string;
  timestamp?: string;
}

function buildTimeline(data: Awaited<ReturnType<typeof fetchAuditTrail>>): TimelineStep[] {
  const steps: TimelineStep[] = [
    {
      title: "Event ingested",
      detail: `${data.event.source} · ${String(data.event.title)}`,
      timestamp: String(data.event.occurred_at),
    },
    {
      title: "Theme match → signal scored",
      detail: `${data.signal.ticker} · raw ${(data.signal.probability_raw * 100).toFixed(1)}% → calibrated ${(data.signal.probability_calibrated * 100).toFixed(1)}% (${data.signal.confidence_bucket})`,
      timestamp: data.signal.created_at,
    },
    {
      title: "Allocation decision",
      detail: `${data.recommendation.action.toUpperCase()} $${Number(data.recommendation.amount_usd).toFixed(2)} · ${data.recommendation.reason}`,
      timestamp: data.recommendation.created_at,
    },
  ];

  if (data.outcome) {
    steps.push({
      title: "Outcome resolved",
      detail: `Outcome move ${(Number(data.outcome.realized_return_pct) * 100).toFixed(2)}% · Brier ${Number(data.outcome.brier_component).toFixed(3)} · ${data.outcome.hit_boolean ? "Hit" : "Miss"}`,
      timestamp: String(data.outcome.resolved_at),
    });
  }

  return steps;
}

export function AuditTrail() {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["audit", id],
    queryFn: () => fetchAuditTrail(id!),
    enabled: Boolean(id),
  });

  if (isLoading) {
    return <div className="h-48 animate-pulse rounded bg-slate-200" aria-busy="true" />;
  }
  if (isError || !data) {
    return (
      <div className="rounded border border-red-200 bg-red-50 p-4" role="alert">
        <p>Could not load audit trail.</p>
        <button type="button" className="mt-2 underline" onClick={() => refetch()}>
          Retry
        </button>
        <Link className="ml-4 underline" to="/">
          Back
        </Link>
      </div>
    );
  }

  const timeline = buildTimeline(data);

  return (
    <article className="space-y-6">
      <Link className="text-sm text-indigo-600 underline" to="/">
        ← Dashboard
      </Link>
      <h1 className="text-2xl font-bold">Provenance Timeline</h1>
      <p className="text-sm text-slate-600">
        {data.signal.ticker} · {data.recommendation.status} · {data.recommendation.disclaimer}
      </p>

      <ol className="relative space-y-6 border-l border-slate-200 pl-6">
        {timeline.map((step) => (
          <li key={step.title} className="relative">
            <span className="absolute -left-[1.95rem] top-1 h-3 w-3 rounded-full bg-indigo-600" aria-hidden="true" />
            <p className="font-semibold">{step.title}</p>
            <p className="text-sm text-slate-700">{step.detail}</p>
            {step.timestamp && <p className="text-xs text-slate-500">{new Date(step.timestamp).toLocaleString()}</p>}
          </li>
        ))}
      </ol>

      <details className="rounded border border-slate-200 bg-slate-50 p-3">
        <summary className="cursor-pointer text-sm font-medium">Raw audit payload</summary>
        <pre className="mt-3 overflow-x-auto rounded bg-slate-900 p-4 text-xs text-slate-100">
          {JSON.stringify(data, null, 2)}
        </pre>
      </details>
    </article>
  );
}
