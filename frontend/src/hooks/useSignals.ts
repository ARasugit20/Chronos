import { useQuery } from "@tanstack/react-query";
import { fetchLiveSignals } from "../api/signals";

const POLL_MS = 120_000;
const STALE_MS = 5 * 60_000;

export function useSignals(suppressed = false) {
  return useQuery({
    queryKey: ["signals", suppressed],
    queryFn: () => fetchLiveSignals(suppressed, 20),
    refetchInterval: POLL_MS,
    staleTime: STALE_MS,
  });
}
