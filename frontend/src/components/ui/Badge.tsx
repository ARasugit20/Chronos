type BadgeVariant = "live" | "historical" | "mock" | "default";

const styles: Record<BadgeVariant, string> = {
  live: "bg-emerald-100 text-emerald-800",
  historical: "bg-slate-100 text-slate-700",
  mock: "bg-amber-100 text-amber-800",
  default: "bg-gray-100 text-gray-700",
};

export function Badge({ label, variant = "default" }: { label: string; variant?: BadgeVariant }) {
  return (
    <span
      className={`inline-flex rounded px-2 py-0.5 text-xs font-semibold uppercase ${styles[variant]}`}
      aria-label={`Data source: ${label}`}
    >
      {label}
    </span>
  );
}

export function dataSourceVariant(source: string): BadgeVariant {
  if (source.includes("mock")) return "mock";
  if (source === "manual") return "live";
  return "historical";
}
