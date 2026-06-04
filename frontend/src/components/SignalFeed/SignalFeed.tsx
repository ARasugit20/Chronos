import { useSignals } from "../../hooks/useSignals";
import { useSignalWebSocket } from "../../hooks/useSignalWebSocket";
import { StatusDot } from "../ui/StatusDot";
import { SignalRow } from "./SignalRow";

function SkeletonRows() {
  return (
    <div className="space-y-3" aria-busy="true">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-20 animate-pulse rounded-lg bg-slate-200" />
      ))}
    </div>
  );
}

export function SignalFeed() {
  const { connectionStatus } = useSignalWebSocket();
  const { data, isLoading, isError, error, refetch, isFetching, dataUpdatedAt } = useSignals(false);
  const stale = Date.now() - dataUpdatedAt > 5 * 60_000 && !isFetching;
  const connColor =
    connectionStatus === "connected"
      ? "bg-emerald-500"
      : connectionStatus === "reconnecting"
        ? "bg-amber-400"
        : "bg-red-500";

  if (isLoading) return <SkeletonRows />;
  if (isError) {
    return (
      <div className="rounded border border-red-200 bg-red-50 p-4" role="alert">
        <p className="font-medium text-red-800">Failed to load signals</p>
        <p className="text-sm text-red-700">{(error as Error).message}</p>
        <button type="button" className="mt-2 rounded bg-red-700 px-3 py-1 text-white" onClick={() => refetch()}>
          Retry
        </button>
      </div>
    );
  }
  if (!data?.length) {
    return (
      <p className="rounded border border-dashed p-6 text-center text-slate-600">
        No signals above threshold — {new Date().toLocaleString()}
      </p>
    );
  }

  return (
    <section aria-labelledby="signal-feed-heading">
      <div className="mb-3 flex items-center gap-2">
        <h2 id="signal-feed-heading" className="text-xl font-semibold">
          Live Signals
        </h2>
        <span className={`inline-block h-2.5 w-2.5 rounded-full ${connColor}`} title={connectionStatus} />
        <StatusDot stale={stale} />
      </div>
      <div className="space-y-3">
        {data.map((signal) => (
          <SignalRow key={signal.id} signal={signal} />
        ))}
      </div>
    </section>
  );
}
