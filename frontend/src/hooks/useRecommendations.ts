import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  approveRecommendation,
  fetchRecommendations,
  skipRecommendation,
} from "../api/recommendations";

const POLL_MS = 60_000;

export function useRecommendations(status = "pending") {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["recommendations", status],
    queryFn: () => fetchRecommendations(status, 10),
    refetchInterval: POLL_MS,
  });

  const approve = useMutation({
    mutationFn: approveRecommendation,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["recommendations"] }),
  });

  const skip = useMutation({
    mutationFn: skipRecommendation,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["recommendations"] }),
  });

  return { ...query, approve, skip };
}
