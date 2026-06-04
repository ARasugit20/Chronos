import { apiClient } from "./client";
import type { Signal } from "../types/domain";

interface CursorPage<T> {
  data: T[];
  next_cursor: string | null;
  has_more: boolean;
}

export async function fetchLiveSignals(suppressed = false, limit = 50): Promise<Signal[]> {
  const { data } = await apiClient.get<CursorPage<Signal>>("/api/v1/signals/live", {
    params: { suppressed, limit },
  });
  return data.data;
}
