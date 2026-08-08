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
  action: "buy" | "hold" | "skip" | "paper_buy" | string;
  amount_usd: string;
  pct_cash: number;
  expires_at: string;
  reason: string;
  status: string;
  disclaimer: string;
  created_at: string;
  model_version: string;
  theme_bucket?: string | null;
  regime?: string | null;
  regime_flags?: string[];
  calibrated_p?: number | null;
  thesis?: string | null;
  invalidate_if?: string | null;
  evidence?: string[];
  rank_score?: number | null;
  kelly_half_pct?: number | null;
  adjustment_reason?: string | null;
}

export interface AuditTrail {
  recommendation: Recommendation;
  signal: Signal;
  event: Record<string, unknown>;
  outcome: Record<string, unknown> | null;
}
