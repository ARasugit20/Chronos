import type { Signal } from "../../types/domain";
import { Badge, dataSourceVariant } from "../ui/Badge";
import { ConfidenceBar } from "../ui/ConfidenceBar";

export function SignalRow({ signal }: { signal: Signal }) {
  const suppressed = signal.suppressed;
  return (
    <article
      className={`grid grid-cols-1 gap-3 rounded-lg border p-4 md:grid-cols-4 ${
        suppressed ? "border-slate-200 bg-slate-50 opacity-70" : "border-slate-200 bg-white"
      }`}
      aria-label={`Signal for ${signal.ticker}`}
    >
      <div>
        <p className="text-lg font-semibold">{signal.ticker}</p>
        <Badge label={signal.data_source} variant={dataSourceVariant(signal.data_source)} />
      </div>
      <div className="md:col-span-2">
        <ConfidenceBar value={signal.probability_calibrated} />
        <p className="mt-2 text-xs text-slate-500">Model {signal.model_version}</p>
      </div>
      <div className="text-sm text-slate-600">
        <p>Bucket: {signal.confidence_bucket}</p>
        {suppressed && signal.suppression_reason && (
          <p className="mt-1 text-slate-500">{signal.suppression_reason}</p>
        )}
      </div>
    </article>
  );
}
