import { Link } from "react-router-dom";
import type { Recommendation } from "../../types/domain";
import { useRecommendations } from "../../hooks/useRecommendations";
import { ConfidenceBar } from "../ui/ConfidenceBar";

export function RecommendationCard({ rec }: { rec: Recommendation }) {
  const { approve, skip } = useRecommendations();
  const busy = approve.isPending || skip.isPending;

  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-lg font-semibold uppercase">{rec.action}</p>
          <p className="text-2xl font-bold">${Number(rec.amount_usd).toFixed(2)}</p>
        </div>
        <p className="text-xs text-slate-500">Expires {new Date(rec.expires_at).toLocaleString()}</p>
      </div>
      <p className="mt-2 text-sm text-slate-700">{rec.reason}</p>
      <p className="mt-2 text-xs text-slate-500">{rec.disclaimer}</p>
      <div className="mt-3">
        <ConfidenceBar value={rec.pct_cash} />
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          disabled={busy}
          className="rounded bg-emerald-600 px-3 py-1.5 text-sm text-white disabled:opacity-50"
          onClick={() => approve.mutate(rec.id)}
        >
          Approve
        </button>
        <button
          type="button"
          disabled={busy}
          className="rounded bg-slate-600 px-3 py-1.5 text-sm text-white disabled:opacity-50"
          onClick={() => skip.mutate(rec.id)}
        >
          Skip
        </button>
        <Link className="rounded border px-3 py-1.5 text-sm" to={`/audit/${rec.id}`}>
          Audit
        </Link>
      </div>
    </article>
  );
}

export function RecommendationList() {
  const { data, isLoading, isError, refetch } = useRecommendations("pending");

  if (isLoading) {
    return (
      <div className="grid gap-3 md:grid-cols-2">
        {[1, 2].map((i) => (
          <div key={i} className="h-40 animate-pulse rounded-lg bg-slate-200" />
        ))}
      </div>
    );
  }
  if (isError) {
    return (
      <div className="rounded border border-red-200 bg-red-50 p-4" role="alert">
        <p>Failed to load recommendations.</p>
        <button type="button" className="mt-2 underline" onClick={() => refetch()}>
          Retry
        </button>
      </div>
    );
  }
  if (!data?.length) {
    return <p className="text-slate-600">No pending recommendations.</p>;
  }
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {data.map((rec) => (
        <RecommendationCard key={rec.id} rec={rec} />
      ))}
    </div>
  );
}
