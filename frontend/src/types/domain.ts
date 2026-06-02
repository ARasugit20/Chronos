export interface Signal {
  id: string;
  event_id: string;
  ticker: string;
  probability_raw: number;
  probability_calibrated: number;
  horizon_hours: number;
  model_version: string;
  confidence_bucket: "high" | "medium" | "low" | string;
  suppressed: boolean;
  suppression_reason: string | null;
  created_at: string;
  data_source: string;
}

export interface Recommendation {
  id: string;
  signal_id: string;
  action: "buy" | "hold" | "skip" | string;
  amount_usd: string;
  pct_cash: number;
  expires_at: string;
  reason: string;
  status: string;
  disclaimer: string;
  created_at: string;
  model_version: string;
}

export interface AuditTrail {
  recommendation: Recommendation;
  signal: Signal;
  event: Record<string, unknown>;
  outcome: Record<string, unknown> | null;
}
