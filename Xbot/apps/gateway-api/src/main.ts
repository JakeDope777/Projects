import Fastify from "fastify";
import cors from "@fastify/cors";
import websocket from "@fastify/websocket";
import { z } from "zod";
import type { HealthResponse } from "@xbot/shared-contracts";

const server = Fastify({ logger: true });

const urls = {
  orchestrator: process.env.ORCHESTRATOR_URL ?? "http://localhost:4002",
  execution: process.env.EXECUTION_URL ?? "http://localhost:4003",
  risk: process.env.RISK_URL ?? "http://localhost:4004",
  analytics: process.env.ANALYTICS_URL ?? "http://localhost:4005",
  marketData: process.env.MARKET_DATA_URL ?? "http://localhost:8002"
};

await server.register(cors, { origin: true });
await server.register(websocket);

const wsClients = new Set<any>();

function publishChannelEvent(channel: string, data: Record<string, unknown>) {
  const message = JSON.stringify({
    channel,
    timestamp: new Date().toISOString(),
    data
  });
  for (const client of wsClients) {
    client.send(message);
  }
}

server.get("/v1/ws", { websocket: true }, (socket) => {
  wsClients.add(socket);
  socket.send(
    JSON.stringify({
      channel: "connection_established",
      timestamp: new Date().toISOString(),
      data: { status: "ok" }
    })
  );
  socket.on("close", () => wsClients.delete(socket));
});

async function proxyGet(url: string) {
  const response = await fetch(url);
  const payload = await response.json();
  return { status: response.status, payload };
}

async function proxyPost(url: string, body: unknown) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  const payload = await response.json();
  return { status: response.status, payload };
}

async function proxyPut(url: string, body: unknown) {
  const response = await fetch(url, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  const payload = await response.json();
  return { status: response.status, payload };
}

server.get("/health", async () => {
  const checks: Record<string, string> = {};
  for (const [name, url] of Object.entries(urls)) {
    try {
      const res = await fetch(`${url}/health`);
      checks[name] = res.ok ? "healthy" : "degraded";
    } catch {
      checks[name] = "unhealthy";
    }
  }
  const status: HealthResponse = {
    status: Object.values(checks).every((x) => x === "healthy")
      ? "healthy"
      : "degraded",
    version: "0.1.0",
    timestamp: new Date().toISOString(),
    checks
  };
  return status;
});

server.post("/v1/auth/login", async (request, reply) => {
  const body = z
    .object({
      email: z.string().email(),
      password: z.string().min(8)
    })
    .parse(request.body);

  return reply.send({
    user: {
      id: "user_internal_operator",
      email: body.email,
      role: "admin"
    },
    access_token: "dev_access_token",
    refresh_token: "dev_refresh_token",
    expires_in_seconds: 3600
  });
});

server.post("/v1/auth/refresh", async () => {
  return {
    access_token: "dev_access_token_refreshed",
    expires_in_seconds: 3600
  };
});

server.post("/v1/auth/logout", async () => {
  return { ok: true };
});

server.get("/v1/markets", async (_, reply) => {
  const { status, payload } = await proxyGet(`${urls.marketData}/v1/markets`);
  return reply.code(status).send(payload);
});

server.get("/v1/markets/:marketId/orderbook", async (request, reply) => {
  const { marketId } = request.params as { marketId: string };
  const { status, payload } = await proxyGet(
    `${urls.marketData}/v1/markets/${marketId}/orderbook`
  );
  publishChannelEvent("market.tick", payload);
  return reply.code(status).send(payload);
});

server.get("/v1/markets/:marketId/features", async (request, reply) => {
  const { marketId } = request.params as { marketId: string };
  const { status, payload } = await proxyGet(
    `${urls.marketData}/v1/features/${marketId}`
  );
  return reply.code(status).send(payload);
});

server.post("/v1/signals/generate", async (request, reply) => {
  const { status, payload } = await proxyPost(
    `${urls.orchestrator}/v1/signals/generate`,
    request.body
  );
  if (status >= 400) {
    publishChannelEvent("risk.alert", payload);
  } else {
    publishChannelEvent("signal.generated", payload);
  }
  return reply.code(status).send(payload);
});

server.post("/v1/orders/create", async (request, reply) => {
  const { status, payload } = await proxyPost(
    `${urls.execution}/v1/orders/create`,
    request.body
  );
  publishChannelEvent("order.requested", payload);
  return reply.code(status).send(payload);
});

server.post("/v1/orders/cancel", async (request, reply) => {
  const { status, payload } = await proxyPost(
    `${urls.execution}/v1/orders/cancel`,
    request.body
  );
  publishChannelEvent("order.executed", payload);
  return reply.code(status).send(payload);
});

server.get("/v1/positions", async (_, reply) => {
  const { status, payload } = await proxyGet(`${urls.analytics}/v1/positions`);
  return reply.code(status).send(payload);
});

server.get("/v1/portfolio/pnl", async (_, reply) => {
  const { status, payload } = await proxyGet(`${urls.analytics}/v1/portfolio/pnl`);
  return reply.code(status).send(payload);
});

server.get("/v1/risk/policies", async (_, reply) => {
  const { status, payload } = await proxyGet(`${urls.risk}/v1/risk/policies`);
  return reply.code(status).send(payload);
});

server.get("/v1/risk/presets", async (_, reply) => {
  const { status, payload } = await proxyGet(`${urls.risk}/v1/risk/presets`);
  return reply.code(status).send(payload);
});

server.put("/v1/risk/presets/:name", async (request, reply) => {
  const { name } = request.params as { name: string };
  const { status, payload } = await proxyPut(
    `${urls.risk}/v1/risk/presets/${name}`,
    request.body
  );
  return reply.code(status).send(payload);
});

server.get("/v1/autonomy/mode", async (_, reply) => {
  const { status, payload } = await proxyGet(`${urls.orchestrator}/v1/autonomy/mode`);
  return reply.code(status).send(payload);
});

server.put("/v1/autonomy/mode", async (request, reply) => {
  const { status, payload } = await proxyPut(
    `${urls.orchestrator}/v1/autonomy/mode`,
    request.body
  );
  publishChannelEvent("autonomy.state_changed", payload);
  return reply.code(status).send(payload);
});

server.get("/v1/autonomy/gate", async (_, reply) => {
  const { status, payload } = await proxyGet(`${urls.orchestrator}/v1/autonomy/gate`);
  return reply.code(status).send(payload);
});

server.post("/v1/approvals/decision", async (request, reply) => {
  const { status, payload } = await proxyPost(
    `${urls.execution}/v1/approvals/decision`,
    request.body
  );
  publishChannelEvent("approval.required", payload);
  return reply.code(status).send(payload);
});

server.post("/v1/ws/broadcast", async (request) => {
  const body = z
    .object({
      channel: z.enum([
        "market.tick",
        "signal.generated",
        "order.requested",
        "order.executed",
        "risk.alert",
        "approval.required",
        "autonomy.state_changed"
      ]),
      data: z.record(z.any()).default({})
    })
    .parse(request.body);
  publishChannelEvent(body.channel, body.data);
  return { ok: true };
});

server.get("/v1/approvals/pending", async (_, reply) => {
  const { status, payload } = await proxyGet(`${urls.execution}/v1/approvals/pending`);
  return reply.code(status).send(payload);
});

server.get("/v1/analytics/overview", async (_, reply) => {
  const { status, payload } = await proxyGet(`${urls.analytics}/v1/analytics/overview`);
  return reply.code(status).send(payload);
});

server.get("/v1/analytics/pnl", async (_, reply) => {
  const { status, payload } = await proxyGet(`${urls.analytics}/v1/analytics/pnl`);
  return reply.code(status).send(payload);
});

server.get("/v1/analytics/risk", async (_, reply) => {
  const { status, payload } = await proxyGet(`${urls.analytics}/v1/analytics/risk`);
  return reply.code(status).send(payload);
});

const port = Number(process.env.PORT ?? "4001");
await server.listen({ host: "0.0.0.0", port });
