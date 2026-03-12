import { randomUUID } from "node:crypto";
import Fastify from "fastify";
import cors from "@fastify/cors";
import { z } from "zod";
import { createEventEnvelope, InMemoryEventBus, JsonlLedger } from "@xbot/shared-events";
import { evaluateAutonomyGate } from "@xbot/shared-risk";
import type {
  AutonomyGateMetrics,
  AutonomyMode,
  HealthResponse
} from "@xbot/shared-contracts";
import { createOrchestratorStore } from "./store.js";

const server = Fastify({ logger: true });
await server.register(cors, { origin: true });

const events = new InMemoryEventBus();
const ledger = new JsonlLedger(
  process.env.LEDGER_PATH ?? "/tmp/xbot-decision-ledger.jsonl"
);
const urls = {
  aiDecision: process.env.AI_DECISION_URL ?? "http://localhost:8001",
  risk: process.env.RISK_URL ?? "http://localhost:4004",
  execution: process.env.EXECUTION_URL ?? "http://localhost:4003"
};

let autonomyMode: AutonomyMode = "approval_required";

const defaultMetrics: AutonomyGateMetrics = {
  window_days: 30,
  sharpe_like_ratio: 0.0,
  cumulative_return_pct: 0.0,
  max_drawdown_pct: 0.0,
  critical_violations: 0,
  evaluated_at: new Date().toISOString()
};
const { store, state } = await createOrchestratorStore({
  mode: autonomyMode,
  metrics: defaultMetrics
});
autonomyMode = state.mode;
let latestMetrics: AutonomyGateMetrics = state.metrics;

server.get("/health", async () => {
  const persistenceHealthy = await store.isHealthy();
  const payload: HealthResponse = {
    status: persistenceHealthy ? "healthy" : "degraded",
    version: "0.1.0",
    timestamp: new Date().toISOString(),
    checks: {
      strategy_engine: "healthy",
      persistence: persistenceHealthy ? "healthy" : "degraded",
      store_backend: store.backend
    }
  };
  return payload;
});

server.get("/v1/autonomy/mode", async () => {
  return { mode: autonomyMode };
});

async function persistAndBroadcastModeChange(mode: AutonomyMode) {
  autonomyMode = mode;
  await store.setMode(autonomyMode);
  await fetch(`${urls.execution}/v1/internal/autonomy-mode`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode: autonomyMode })
  }).catch(() => null);

  await events.publish(
    createEventEnvelope(
      "trading-orchestrator",
      "autonomy.state_changed.v1",
      randomUUID(),
      "risk-policy-v1",
      { mode: autonomyMode }
    )
  );
  await ledger.append(
    createEventEnvelope(
      "trading-orchestrator",
      "autonomy.state_changed.v1",
      randomUUID(),
      "risk-policy-v1",
      { mode: autonomyMode }
    )
  );
}

server.put("/v1/autonomy/mode", async (request, reply) => {
  const body = z.object({ mode: z.enum(["approval_required", "paper_autonomous", "live_autonomous", "halted"]) }).parse(request.body);

  if (body.mode === "live_autonomous") {
    const gate = evaluateAutonomyGate(latestMetrics);
    if (!gate.passed) {
      return reply.code(409).send({
        error: "autonomy_gate_not_passed",
        failures: gate.failures
      });
    }
  }

  await persistAndBroadcastModeChange(body.mode);
  return { mode: autonomyMode };
});

server.post("/v1/autonomy/kill-switch", async (request) => {
  const body = z
    .object({
      reason: z.string().min(3).default("manual_kill_switch")
    })
    .parse(request.body);

  await persistAndBroadcastModeChange("halted");

  await events.publish(
    createEventEnvelope(
      "trading-orchestrator",
      "risk.alert.v1",
      randomUUID(),
      "risk-policy-v1",
      {
        reason: body.reason,
        action: "kill_switch_activated"
      }
    )
  );
  await ledger.append(
    createEventEnvelope(
      "trading-orchestrator",
      "risk.alert.v1",
      randomUUID(),
      "risk-policy-v1",
      {
        reason: body.reason,
        action: "kill_switch_activated"
      }
    )
  );

  return {
    mode: autonomyMode,
    reason: body.reason,
    status: "halted"
  };
});

server.post("/v1/autonomy/resume", async (request) => {
  const body = z
    .object({
      mode: z
        .enum(["approval_required", "paper_autonomous", "live_autonomous"])
        .default("approval_required")
    })
    .parse(request.body);

  if (body.mode === "live_autonomous") {
    const gate = evaluateAutonomyGate(latestMetrics);
    if (!gate.passed) {
      return {
        mode: autonomyMode,
        resumed: false,
        failures: gate.failures
      };
    }
  }

  await persistAndBroadcastModeChange(body.mode);
  return {
    mode: autonomyMode,
    resumed: true
  };
});

server.get("/v1/autonomy/gate", async () => {
  const result = evaluateAutonomyGate(latestMetrics);
  return {
    metrics: latestMetrics,
    passed: result.passed,
    failures: result.failures
  };
});

server.put("/v1/autonomy/gate", async (request) => {
  const body = z
    .object({
      window_days: z.number().int().positive(),
      sharpe_like_ratio: z.number(),
      cumulative_return_pct: z.number(),
      max_drawdown_pct: z.number(),
      critical_violations: z.number().int().nonnegative()
    })
    .parse(request.body);

  latestMetrics = {
    ...body,
    evaluated_at: new Date().toISOString()
  };
  await store.setMetrics(latestMetrics);
  return { metrics: latestMetrics };
});

server.post("/v1/signals/generate", async (request, reply) => {
  const body = z
    .object({
      market_id: z.string(),
      strategy_id: z.string().default("hybrid_v1"),
      context: z.record(z.any()).default({})
    })
    .parse(request.body);

  const aiResponse = await fetch(`${urls.aiDecision}/v1/decision/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  }).catch(() => null);

  const aiPayload =
    aiResponse && aiResponse.ok
      ? ((await aiResponse.json()) as {
          side: "buy" | "sell";
          confidence: number;
          limit_price: number;
          quantity: number;
          rationale: string;
        })
      : {
          side: "buy" as const,
          confidence: 0.5,
          limit_price: 0.5,
          quantity: 1,
          rationale: "fallback_decision"
        };

  const orderRequest = {
    market_id: body.market_id,
    side: aiPayload.side,
    quantity: aiPayload.quantity,
    limit_price: aiPayload.limit_price,
    strategy_id: body.strategy_id,
    confidence: aiPayload.confidence,
    requires_approval: autonomyMode !== "live_autonomous",
    autonomy_mode: autonomyMode
  };

  const riskEvaluation = await fetch(`${urls.risk}/v1/risk/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      deployableCapital: body.context.deployableCapital ?? 10000,
      openExposureValue: body.context.openExposureValue ?? 0,
      concurrentPositions: body.context.concurrentPositions ?? 0,
      dailyLossPct: body.context.dailyLossPct ?? 0,
      marketOpenExposureValue: body.context.marketOpenExposureValue ?? 0,
      order: {
        request_id: randomUUID(),
        correlation_id: randomUUID(),
        market_id: orderRequest.market_id,
        side: orderRequest.side,
        quantity: orderRequest.quantity,
        limit_price: orderRequest.limit_price,
        strategy_id: orderRequest.strategy_id,
        confidence: orderRequest.confidence,
        requires_approval: orderRequest.requires_approval,
        requested_at: new Date().toISOString()
      }
    })
  }).catch(() => null);

  const riskPayload =
    riskEvaluation && riskEvaluation.ok
      ? await riskEvaluation.json()
      : { evaluation: { allowed: false, reasons: ["risk_service_unavailable"], hardHalt: true } };

  if (!riskPayload.evaluation.allowed) {
    return reply.code(409).send({
      signal: orderRequest,
      risk: riskPayload.evaluation,
      status: "blocked_by_risk"
    });
  }

  await events.publish(
    createEventEnvelope("trading-orchestrator", "signal.generated.v1", randomUUID(), "risk-policy-v1", {
      market_id: body.market_id,
      strategy_id: body.strategy_id,
      confidence: aiPayload.confidence,
      mode: autonomyMode
    })
  );
  await ledger.append(
    createEventEnvelope("trading-orchestrator", "signal.generated.v1", randomUUID(), "risk-policy-v1", {
      market_id: body.market_id,
      strategy_id: body.strategy_id,
      confidence: aiPayload.confidence,
      mode: autonomyMode
    })
  );

  const execution = await fetch(`${urls.execution}/v1/orders/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(orderRequest)
  });

  const executionPayload = await execution.json();
  return reply.code(execution.status).send({
    signal: {
      ...orderRequest,
      rationale: aiPayload.rationale
    },
    execution: executionPayload
  });
});

const port = Number(process.env.PORT ?? "4002");
await server.listen({ host: "0.0.0.0", port });
