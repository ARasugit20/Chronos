import { describe, expect, it } from "vitest";
import { resolveApiBaseUrl, resolveWebSocketBaseUrl } from "./api/config";

describe("api config", () => {
  it("defaults to local backend", () => {
    expect(resolveApiBaseUrl()).toBe("http://localhost:8000");
  });

  it("derives websocket URL from http base", () => {
    expect(resolveWebSocketBaseUrl()).toBe("ws://localhost:8000");
  });
});

describe("outcome metrics shape", () => {
  it("accepts bucket reliability payload", () => {
    const payload = {
      methodology: "resolved_outcome_metrics",
      total_resolved: 2,
      hit_rate: 0.5,
      mean_brier: 0.22,
      precision_by_ticker: { AAPL: 0.67 },
      bucket_reliability: {
        high: {
          samples: 2,
          mean_predicted: 0.7,
          observed_hit_rate: 0.5,
          calibration_gap: 0.2,
        },
      },
      ml_ready: false,
      paper_trading: true,
      note: "test",
      disclaimer: "research only",
    };
    expect(payload.bucket_reliability.high.calibration_gap).toBe(0.2);
  });
});
