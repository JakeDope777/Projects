import Fastify from "fastify";
import cors from "@fastify/cors";
import { z } from "zod";
import {
  RiskPresetSchema,
  type HealthResponse,
  type RiskPreset
} from "@xbot/shared-contracts";
import {
  CONSERVATIVE_PRESET,
  evaluateRisk,
  estimateOrderNotional
} from "@xbot/shared-risk";
import { createRiskStore } from "./store.js";

const server = Fastify({ logger: true });
await server.register(cors, { origin: true });

const policies = {
  defaultAutonomyGateWindowDays: 30,
  hardStopOnCriticalViolation: true,
  allowLiveMode: true
};

const seedPresets = new Map<string, RiskPreset>([
  ["conservative", CONSERVATIVE_PRESET],
  [
    "balanced",
    {
      name: "balanced",
      max_per_market_exposure_pct: 0.05,
      max_total_open_exposure_pct: 0.25,
      max_daily_loss_pct: 0.03,
      max_concurrent_positions: 6,
      hard_halt_on_breach: true,
      updated_at: new Date().toISOString()
    }
  ],
  [
    "aggressive",
    {
      name: "aggressive",
      max_per_market_exposure_pct: 0.1,
      max_total_open_exposure_pct: 0.4,
      max_daily_loss_pct: 0.06,
      max_concurrent_positions: 12,
      hard_halt_on_breach: true,
      updated_at: new Date().toISOString()
    }
  ]
]);

const defaultActivePresetKey = process.env.RISK_PRESET ?? "conservative";
const { store, state } = await createRiskStore({
  presets: seedPresets,
  activePresetKey: defaultActivePresetKey
});
const presets = state.presets;
let activePresetKey = state.activePresetKey;

server.get("/health", async () => {
  const persistenceHealthy = await store.isHealthy();
  const payload: HealthResponse = {
    status: persistenceHealthy ? "healthy" : "degraded",
    version: "0.1.0",
    timestamp: new Date().toISOString(),
    checks: {
      policy_store: "healthy",
      persistence: persistenceHealthy ? "healthy" : "degraded",
      store_backend: store.backend
    }
  };
  return payload;
});

server.get("/v1/risk/policies", async () => {
  return {
    policies,
    active_preset: activePresetKey
  };
});

server.get("/v1/risk/presets", async () => {
  return {
    active: activePresetKey,
    presets: Array.from(presets.values())
  };
});

server.put("/v1/risk/presets/:name", async (request, reply) => {
  const { name } = request.params as { name: string };
  const parsed = RiskPresetSchema.safeParse(request.body);
  if (!parsed.success) {
    return reply.code(400).send({
      error: "invalid_preset",
      details: parsed.error.issues
    });
  }
  const persistedPreset = {
    ...parsed.data,
    updated_at: new Date().toISOString()
  };
  presets.set(name, persistedPreset);
  await store.savePreset(name, persistedPreset);
  activePresetKey = name;
  await store.setActivePreset(name);
  return {
    active: activePresetKey,
    preset: presets.get(name)
  };
});

server.post("/v1/risk/evaluate", async (request, reply) => {
  const body = z
    .object({
      deployableCapital: z.number().positive(),
      openExposureValue: z.number().nonnegative(),
      concurrentPositions: z.number().int().nonnegative(),
      dailyLossPct: z.number(),
      marketOpenExposureValue: z.number().nonnegative(),
      order: z.object({
        request_id: z.string(),
        correlation_id: z.string(),
        market_id: z.string(),
        side: z.enum(["buy", "sell"]),
        quantity: z.number().positive(),
        limit_price: z.number().positive(),
        strategy_id: z.string(),
        confidence: z.number().min(0).max(1),
        requires_approval: z.boolean(),
        requested_at: z.string(),
        metadata: z.record(z.any()).default({})
      })
    })
    .parse(request.body);

  const preset = presets.get(activePresetKey);
  if (!preset) {
    return reply.code(500).send({ error: "active_preset_missing" });
  }

  const result = evaluateRisk({
    deployableCapital: body.deployableCapital,
    openExposureValue: body.openExposureValue,
    newOrderNotional: estimateOrderNotional(body.order),
    concurrentPositions: body.concurrentPositions,
    dailyLossPct: body.dailyLossPct,
    activePreset: preset,
    marketOpenExposureValue: body.marketOpenExposureValue
  });

  return {
    active_preset: activePresetKey,
    evaluation: result
  };
});

const port = Number(process.env.PORT ?? "4004");
await server.listen({ host: "0.0.0.0", port });
