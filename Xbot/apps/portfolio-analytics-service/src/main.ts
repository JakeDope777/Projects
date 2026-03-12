import { randomUUID } from "node:crypto";
import Fastify from "fastify";
import cors from "@fastify/cors";
import { z } from "zod";
import type { HealthResponse, Position } from "@xbot/shared-contracts";
import { createAnalyticsStore } from "./store.js";

const server = Fastify({ logger: true });
await server.register(cors, { origin: true });
const store = await createAnalyticsStore();

function summarizePnl(currentPositions: Position[]) {
  const unrealized = currentPositions.reduce((acc, p) => acc + p.unrealized_pnl, 0);
  const realized = currentPositions.reduce((acc, p) => acc + p.realized_pnl, 0);
  return {
    unrealized,
    realized,
    total: unrealized + realized
  };
}

server.get("/health", async () => {
  const persistenceHealthy = await store.isHealthy();
  const payload: HealthResponse = {
    status: persistenceHealthy ? "healthy" : "degraded",
    version: "0.1.0",
    timestamp: new Date().toISOString(),
    checks: {
      analytics: "healthy",
      persistence: persistenceHealthy ? "healthy" : "degraded",
      store_backend: store.backend
    }
  };
  return payload;
});

server.get("/v1/positions", async () => {
  const items = await store.listPositions();
  return {
    count: items.length,
    items
  };
});

server.post("/v1/positions/upsert", async (request) => {
  const body = z
    .object({
      position_id: z.string().optional(),
      market_id: z.string(),
      side: z.enum(["buy", "sell"]),
      quantity: z.number(),
      average_entry_price: z.number(),
      mark_price: z.number(),
      unrealized_pnl: z.number(),
      realized_pnl: z.number()
    })
    .parse(request.body);

  const positionId = body.position_id ?? randomUUID();
  const now = new Date().toISOString();
  const existing = (await store.listPositions()).find(
    (item) => item.position_id === positionId
  );
  const position: Position = {
    position_id: positionId,
    market_id: body.market_id,
    side: body.side,
    quantity: body.quantity,
    average_entry_price: body.average_entry_price,
    mark_price: body.mark_price,
    unrealized_pnl: body.unrealized_pnl,
    realized_pnl: body.realized_pnl,
    opened_at: existing?.opened_at ?? now,
    updated_at: now
  };
  await store.upsertPosition(position);
  return {
    position
  };
});

server.get("/v1/portfolio/pnl", async () => {
  const currentPositions = await store.listPositions();
  const summary = summarizePnl(currentPositions);
  return {
    positions_count: currentPositions.length,
    ...summary,
    timestamp: new Date().toISOString()
  };
});

server.get("/v1/analytics/overview", async () => {
  const currentPositions = await store.listPositions();
  const pnl = summarizePnl(currentPositions);
  const exposure = currentPositions.reduce(
    (acc, p) => acc + Math.abs(p.quantity * p.mark_price),
    0
  );
  return {
    active_positions: currentPositions.length,
    pnl,
    exposure,
    kpi: {
      risk_adjusted_return_target: "positive",
      critical_breaches: 0
    },
    timestamp: new Date().toISOString()
  };
});

server.get("/v1/analytics/pnl", async () => {
  const currentPositions = await store.listPositions();
  return {
    pnl: summarizePnl(currentPositions),
    timestamp: new Date().toISOString()
  };
});

server.get("/v1/analytics/risk", async () => {
  const currentPositions = await store.listPositions();
  const grossExposure = currentPositions.reduce(
    (acc, p) => acc + Math.abs(p.quantity * p.mark_price),
    0
  );
  return {
    gross_exposure: grossExposure,
    positions: currentPositions.length,
    timestamp: new Date().toISOString()
  };
});

const port = Number(process.env.PORT ?? "4005");
await server.listen({ host: "0.0.0.0", port });
