import { apiClient } from "./client";
import type { Signal } from "../types/domain";

export async function fetchLiveSignals(suppressed = false, limit = 20): Promise<Signal[]> {
  const { data } = await apiClient.get<Signal[]>("/api/v1/signals/live", {
    params: { suppressed, limit },
  });
  return data;
}
