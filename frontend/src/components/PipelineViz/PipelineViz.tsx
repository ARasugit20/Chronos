const STEPS = ["Ingest", "Dedup", "Theme Map", "Score", "Calibrate", "Allocate", "Recommend"];

export function PipelineViz() {
  return (
    <section aria-label="Pipeline visualization" className="overflow-x-auto rounded-lg border bg-white p-4">
      <ol className="flex min-w-max gap-4">
        {STEPS.map((step, index) => (
          <li key={step} className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600 text-sm text-white">
              {index + 1}
            </span>
            <span className="text-sm font-medium">{step}</span>
            {index < STEPS.length - 1 && <span className="text-slate-300">→</span>}
          </li>
        ))}
      </ol>
    </section>
  );
}
