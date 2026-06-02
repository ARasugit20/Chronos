import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { fetchAuditTrail } from "../api/recommendations";

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

  return (
    <article className="space-y-4">
      <Link className="text-sm text-indigo-600 underline" to="/">
        ← Dashboard
      </Link>
      <h1 className="text-2xl font-bold">Audit Trail</h1>
      <div className="overflow-x-auto rounded border">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-100">
            <tr>
              <th className="p-2">Field</th>
              <th className="p-2">Value</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="p-2 font-medium">Recommendation</td>
              <td className="p-2">{data.recommendation.reason}</td>
            </tr>
            <tr>
              <td className="p-2 font-medium">Ticker</td>
              <td className="p-2">{data.signal.ticker}</td>
            </tr>
            <tr>
              <td className="p-2 font-medium">Event</td>
              <td className="p-2">{String(data.event.title)}</td>
            </tr>
            <tr>
              <td className="p-2 font-medium">Disclaimer</td>
              <td className="p-2">{data.recommendation.disclaimer}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <pre className="overflow-x-auto rounded bg-slate-900 p-4 text-xs text-slate-100">
        {JSON.stringify(data, null, 2)}
      </pre>
    </article>
  );
}
