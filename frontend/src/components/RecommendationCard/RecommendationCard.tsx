import { Link } from "react-router-dom";
import type { Recommendation } from "../../types/domain";
import { useRecommendations } from "../../hooks/useRecommendations";
import { ConfidenceBar } from "../ui/ConfidenceBar";

export function RecommendationCard({ rec }: { rec: Recommendation }) {
  const { approve, skip } = useRecommendations();
  const busy = approve.isPending || skip.isPending;
  const isPaper = rec.action === "paper_buy";

  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-lg font-semibold uppercase">{rec.action}</p>
            {isPaper && (
              <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800">
                Paper / Research
              </span>
            )}
          </div>
          <p className="text-2xl font-bold">${Number(rec.amount_usd).toFixed(2)}</p>
          {rec.rank_score != null && (
            <p className="text-xs text-slate-500">Rank score {rec.rank_score.toFixed(4)}</p>
          )}
        </div>
        <div className="text-right text-xs text-slate-500">
          <p>Expires {new Date(rec.expires_at).toLocaleString()}</p>
          <p className="mt-1 font-mono">Audit {rec.id.slice(0, 8)}</p>
        </div>
      </div>

      {rec.thesis && <p className="mt-2 text-sm font-medium text-slate-800">{rec.thesis}</p>}
      <p className="mt-2 text-sm text-slate-700">{rec.reason}</p>

      <dl className="mt-3 grid gap-1 text-xs text-slate-600 sm:grid-cols-2">
        {rec.theme_bucket && (
          <>
            <dt className="font-medium">Theme</dt>
            <dd>{rec.theme_bucket}</dd>
          </>
        )}
        {rec.regime && (
          <>
            <dt className="font-medium">Regime</dt>
            <dd>{rec.regime}</dd>
          </>
        )}
        {rec.calibrated_p != null && (
          <>
            <dt className="font-medium">Calibrated p</dt>
            <dd>{(rec.calibrated_p * 100).toFixed(1)}%</dd>
          </>
        )}
        {rec.kelly_half_pct != null && (
          <>
            <dt className="font-medium">Half-Kelly</dt>
            <dd>{(rec.kelly_half_pct * 100).toFixed(1)}%</dd>
          </>
        )}
        {rec.adjustment_reason && (
          <>
            <dt className="font-medium">Sizing note</dt>
            <dd>{rec.adjustment_reason}</dd>
          </>
        )}
        {rec.invalidate_if && (
          <>
            <dt className="font-medium sm:col-span-2">Invalidate if</dt>
            <dd className="sm:col-span-2">{rec.invalidate_if}</dd>
          </>
        )}
      </dl>

      {rec.evidence && rec.evidence.length > 0 && (
        <ul className="mt-2 list-inside list-disc text-xs text-slate-500">
          {rec.evidence.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}

      <p className="mt-2 text-xs text-slate-500">{rec.disclaimer}</p>
      <div className="mt-3">
        <ConfidenceBar value={rec.calibrated_p ?? rec.pct_cash} />
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

  const sorted = [...data].sort((a, b) => (b.rank_score ?? 0) - (a.rank_score ?? 0));

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {sorted.map((rec) => (
        <RecommendationCard key={rec.id} rec={rec} />
      ))}
    </div>
  );
}
