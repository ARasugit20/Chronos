import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../../api/client";

interface BucketReliability {
  samples: number;
  mean_predicted: number;
  observed_hit_rate: number;
  calibration_gap: number;
}

export interface OutcomeMetrics {
  methodology: string;
  total_resolved: number;
  hit_rate: number;
  mean_brier: number;
  precision_by_ticker: Record<string, number>;
  bucket_reliability: Record<string, BucketReliability>;
  ml_ready: boolean;
  paper_trading: boolean;
  note: string;
  disclaimer: string;
}

export function useOutcomeMetrics() {
  return useQuery({
    queryKey: ["outcome-metrics"],
    queryFn: async () => {
      const { data } = await apiClient.get<OutcomeMetrics>("/api/v1/outcome-metrics");
      return data;
    },
    refetchInterval: 60_000,
  });
}
