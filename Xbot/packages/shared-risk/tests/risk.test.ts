import { describe, expect, it } from "vitest";
import {
  CONSERVATIVE_PRESET,
  evaluateAutonomyGate,
  evaluateRisk
} from "../src/index.js";

describe("risk evaluation", () => {
  it("allows order under limits", () => {
    const result = evaluateRisk({
      deployableCapital: 10000,
      openExposureValue: 500,
      newOrderNotional: 150,
      concurrentPositions: 1,
      dailyLossPct: -0.001,
      activePreset: CONSERVATIVE_PRESET,
      marketOpenExposureValue: 0
    });
    expect(result.allowed).toBe(true);
    expect(result.reasons).toHaveLength(0);
  });

  it("blocks order above per-market exposure", () => {
    const result = evaluateRisk({
      deployableCapital: 10000,
      openExposureValue: 1000,
      newOrderNotional: 500,
      concurrentPositions: 1,
      dailyLossPct: -0.001,
      activePreset: CONSERVATIVE_PRESET,
      marketOpenExposureValue: 0
    });
    expect(result.allowed).toBe(false);
    expect(result.reasons).toContain("max_per_market_exposure_pct breached");
  });
});

describe("autonomy gate", () => {
  it("passes with healthy metrics", () => {
    const outcome = evaluateAutonomyGate({
      window_days: 30,
      sharpe_like_ratio: 1.2,
      cumulative_return_pct: 0.03,
      max_drawdown_pct: -0.01,
      critical_violations: 0,
      evaluated_at: new Date().toISOString()
    });
    expect(outcome.passed).toBe(true);
  });

  it("fails when critical violations exist", () => {
    const outcome = evaluateAutonomyGate({
      window_days: 30,
      sharpe_like_ratio: 1.2,
      cumulative_return_pct: 0.03,
      max_drawdown_pct: -0.01,
      critical_violations: 1,
      evaluated_at: new Date().toISOString()
    });
    expect(outcome.passed).toBe(false);
    expect(outcome.failures).toContain("critical_violations_present");
  });
});

