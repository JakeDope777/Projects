import { z } from "zod";

export type Uuid = string;
export type ISO8601 = string;

export const EventEnvelopeSchema = z.object({
  event_id: z.string(),
  event_type: z.string().endsWith(".v1"),
  correlation_id: z.string(),
  timestamp: z.string(),
  service: z.string(),
  policy_version: z.string(),
  payload: z.record(z.any())
});

export type EventEnvelope = z.infer<typeof EventEnvelopeSchema>;

export const AutonomyModeSchema = z.enum([
  "approval_required",
  "paper_autonomous",
  "live_autonomous",
  "halted"
]);
export type AutonomyMode = z.infer<typeof AutonomyModeSchema>;

export const RiskPresetSchema = z.object({
  name: z.enum(["conservative", "balanced", "aggressive", "custom"]),
  max_per_market_exposure_pct: z.number().min(0).max(1),
  max_total_open_exposure_pct: z.number().min(0).max(1),
  max_daily_loss_pct: z.number().min(0).max(1),
  max_concurrent_positions: z.number().int().positive(),
  hard_halt_on_breach: z.boolean(),
  updated_at: z.string()
});

export type RiskPreset = z.infer<typeof RiskPresetSchema>;

export const OrderSideSchema = z.enum(["buy", "sell"]);
export type OrderSide = z.infer<typeof OrderSideSchema>;

export const OrderRequestSchema = z.object({
  request_id: z.string(),
  correlation_id: z.string(),
  market_id: z.string(),
  side: OrderSideSchema,
  quantity: z.number().positive(),
  limit_price: z.number().positive(),
  strategy_id: z.string(),
  confidence: z.number().min(0).max(1),
  requires_approval: z.boolean(),
  requested_at: z.string(),
  metadata: z.record(z.any()).default({})
});
export type OrderRequest = z.infer<typeof OrderRequestSchema>;

export const OrderStatusSchema = z.enum([
  "created",
  "pending_approval",
  "approved",
  "rejected",
  "submitted",
  "filled",
  "cancelled",
  "failed",
  "blocked_by_risk"
]);
export type OrderStatus = z.infer<typeof OrderStatusSchema>;

export const ApprovalDecisionSchema = z.object({
  approval_id: z.string(),
  request_id: z.string(),
  approved: z.boolean(),
  actor_id: z.string(),
  reason: z.string().optional(),
  decided_at: z.string()
});
export type ApprovalDecision = z.infer<typeof ApprovalDecisionSchema>;

export const PositionSchema = z.object({
  position_id: z.string(),
  market_id: z.string(),
  side: OrderSideSchema,
  quantity: z.number(),
  average_entry_price: z.number(),
  mark_price: z.number(),
  unrealized_pnl: z.number(),
  realized_pnl: z.number(),
  opened_at: z.string(),
  updated_at: z.string()
});
export type Position = z.infer<typeof PositionSchema>;

export const AutonomyGateMetricsSchema = z.object({
  window_days: z.number().int().positive(),
  sharpe_like_ratio: z.number(),
  cumulative_return_pct: z.number(),
  max_drawdown_pct: z.number(),
  critical_violations: z.number().int().min(0),
  evaluated_at: z.string()
});
export type AutonomyGateMetrics = z.infer<typeof AutonomyGateMetricsSchema>;

export const HealthResponseSchema = z.object({
  status: z.enum(["healthy", "degraded", "unhealthy"]),
  version: z.string(),
  timestamp: z.string(),
  checks: z.record(z.string())
});
export type HealthResponse = z.infer<typeof HealthResponseSchema>;

