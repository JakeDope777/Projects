import type {
  AutonomyGateMetrics,
  OrderRequest,
  Position,
  RiskPreset
} from "@xbot/shared-contracts";

export interface RiskEvaluationInput {
  deployableCapital: number;
  openExposureValue: number;
  newOrderNotional: number;
  concurrentPositions: number;
  dailyLossPct: number;
  activePreset: RiskPreset;
  marketOpenExposureValue: number;
}

export interface RiskEvaluationResult {
  allowed: boolean;
  reasons: string[];
  hardHalt: boolean;
}

export const CONSERVATIVE_PRESET: RiskPreset = {
  name: "conservative",
  max_per_market_exposure_pct: 0.02,
  max_total_open_exposure_pct: 0.15,
  max_daily_loss_pct: 0.015,
  max_concurrent_positions: 3,
  hard_halt_on_breach: true,
  updated_at: new Date().toISOString()
};

export function evaluateRisk(input: RiskEvaluationInput): RiskEvaluationResult {
  const reasons: string[] = [];
  const {
    deployableCapital,
    openExposureValue,
    newOrderNotional,
    concurrentPositions,
    dailyLossPct,
    activePreset,
    marketOpenExposureValue
  } = input;

  const nextTotalExposurePct =
    (openExposureValue + newOrderNotional) / deployableCapital;
  const nextMarketExposurePct =
    (marketOpenExposureValue + newOrderNotional) / deployableCapital;

  if (nextTotalExposurePct > activePreset.max_total_open_exposure_pct) {
    reasons.push("max_total_open_exposure_pct breached");
  }
  if (nextMarketExposurePct > activePreset.max_per_market_exposure_pct) {
    reasons.push("max_per_market_exposure_pct breached");
  }
  if (concurrentPositions >= activePreset.max_concurrent_positions) {
    reasons.push("max_concurrent_positions breached");
  }
  if (dailyLossPct <= -activePreset.max_daily_loss_pct) {
    reasons.push("max_daily_loss_pct breached");
  }

  return {
    allowed: reasons.length === 0,
    reasons,
    hardHalt: reasons.length > 0 && activePreset.hard_halt_on_breach
  };
}

export interface AutonomyGatePolicy {
  minWindowDays: number;
  minCumulativeReturnPct: number;
  minSharpeLikeRatio: number;
  maxDrawdownPct: number;
  maxCriticalViolations: number;
}

export const DEFAULT_AUTONOMY_GATE_POLICY: AutonomyGatePolicy = {
  minWindowDays: 30,
  minCumulativeReturnPct: 0,
  minSharpeLikeRatio: 0.5,
  maxDrawdownPct: 0.015,
  maxCriticalViolations: 0
};

export function evaluateAutonomyGate(
  metrics: AutonomyGateMetrics,
  policy: AutonomyGatePolicy = DEFAULT_AUTONOMY_GATE_POLICY
): { passed: boolean; failures: string[] } {
  const failures: string[] = [];
  if (metrics.window_days < policy.minWindowDays) {
    failures.push("insufficient_window_days");
  }
  if (metrics.cumulative_return_pct < policy.minCumulativeReturnPct) {
    failures.push("cumulative_return_below_threshold");
  }
  if (metrics.sharpe_like_ratio < policy.minSharpeLikeRatio) {
    failures.push("risk_adjusted_return_below_threshold");
  }
  if (metrics.max_drawdown_pct < -policy.maxDrawdownPct) {
    failures.push("max_drawdown_breach");
  }
  if (metrics.critical_violations > policy.maxCriticalViolations) {
    failures.push("critical_violations_present");
  }
  return { passed: failures.length === 0, failures };
}

export function estimateOrderNotional(order: OrderRequest): number {
  return order.quantity * order.limit_price;
}

export function computePortfolioExposure(positions: Position[]): number {
  return positions.reduce(
    (acc, item) => acc + Math.abs(item.quantity * item.mark_price),
    0
  );
}
