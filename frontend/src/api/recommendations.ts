import { apiClient } from "./client";
import type { AuditTrail, Recommendation } from "../types/domain";

interface CursorPage<T> {
  data: T[];
  next_cursor: string | null;
  has_more: boolean;
}

export async function fetchRecommendations(status = "pending", limit = 10): Promise<Recommendation[]> {
  const { data } = await apiClient.get<CursorPage<Recommendation>>("/api/v1/recommendations", {
    params: { status, limit },
  });
  return data.data;
}

export async function approveRecommendation(id: string): Promise<Recommendation> {
  const { data } = await apiClient.post<Recommendation>(`/api/v1/recommendations/${id}/approve`);
  return data;
}

export async function skipRecommendation(id: string): Promise<Recommendation> {
  const { data } = await apiClient.post<Recommendation>(`/api/v1/recommendations/${id}/skip`);
  return data;
}

export async function fetchAuditTrail(id: string): Promise<AuditTrail> {
  const { data } = await apiClient.get<AuditTrail>(`/api/v1/audit/${id}`);
  return data;
}
