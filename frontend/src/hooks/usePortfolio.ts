import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";

export interface TickerExposure {
  ticker: string;
  sector: string;
  amount_usd: number;
  pct_portfolio: number;
  pct_ticker_cap: number;
}

export interface PortfolioSnapshot {
  portfolio_cash: number;
  portfolio_value: number;
  available_cash: number;
  total_deployed: number;
  pct_deployed: number;
  sector_cap_pct: number;
  max_ticker_pct: number;
  open_recommendations: number;
  ticker_exposure: TickerExposure[];
  sector_exposure: Record<string, number>;
  paper_trading_mode: boolean;
  disclaimer: string;
}

export function usePortfolio() {
  return useQuery({
    queryKey: ["portfolio"],
    queryFn: async () => {
      const { data } = await apiClient.get<PortfolioSnapshot>("/api/v1/portfolio");
      return data;
    },
    refetchInterval: 30_000,
  });
}
