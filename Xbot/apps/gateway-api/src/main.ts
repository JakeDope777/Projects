import Fastify from "fastify";
import cors from "@fastify/cors";
import websocket from "@fastify/websocket";
import bcrypt from "bcryptjs";
import jwt, { type JwtPayload } from "jsonwebtoken";
import { z } from "zod";
import type { HealthResponse } from "@xbot/shared-contracts";

type Role = "admin" | "agent" | "viewer";
type TokenKind = "access" | "refresh";

interface AuthTokenPayload extends JwtPayload {
  sub: string;
  email: string;
  role: Role;
  kind: TokenKind;
}

const server = Fastify({ logger: true });

const urls = {
  orchestrator: process.env.ORCHESTRATOR_URL ?? "http://localhost:4002",
  execution: process.env.EXECUTION_URL ?? "http://localhost:4003",
  risk: process.env.RISK_URL ?? "http://localhost:4004",
  analytics: process.env.ANALYTICS_URL ?? "http://localhost:4005",
  marketData: process.env.MARKET_DATA_URL ?? "http://localhost:8002"
};

const authRequired = process.env.AUTH_REQUIRED !== "false";
const jwtSecret = process.env.JWT_SECRET ?? "dev_jwt_secret_change_me";
const accessTokenTtlSeconds = Number(
  process.env.ACCESS_TOKEN_TTL_SECONDS ?? "3600"
);
const refreshTokenTtlSeconds = Number(
  process.env.REFRESH_TOKEN_TTL_SECONDS ?? "604800"
);
const operator = {
  id: process.env.OPERATOR_ID ?? "user_internal_operator",
  email: process.env.OPERATOR_EMAIL ?? "operator@xbot.local",
  role: (process.env.OPERATOR_ROLE as Role | undefined) ?? "admin",
  password: process.env.OPERATOR_PASSWORD ?? "ChangeMe!123",
  passwordHash: process.env.OPERATOR_PASSWORD_HASH
};

await server.register(cors, { origin: true });
await server.register(websocket);

const wsClients = new Set<any>();

const publicRoutes = new Set([
  "/health",
  "/v1/auth/login",
  "/v1/auth/refresh",
  "/v1/auth/logout"
]);

const adminOnly = [
  { method: "POST", path: "/v1/autonomy/kill-switch" },
  { method: "POST", path: "/v1/autonomy/resume" },
  { method: "POST", path: "/v1/ws/broadcast" },
  { method: "PUT", path: "/v1/autonomy/mode" },
  { method: "PUT", pathPrefix: "/v1/risk/presets/" }
] as const;

function toPath(url: string) {
  return url.split("?")[0];
}

function createToken(payload: Omit<AuthTokenPayload, "kind">, kind: TokenKind) {
  return jwt.sign(
    {
      ...payload,
      kind
    },
    jwtSecret,
    {
      expiresIn: kind === "access" ? accessTokenTtlSeconds : refreshTokenTtlSeconds
    }
  );
}

function verifyToken(rawToken: string, expectedKind: TokenKind): AuthTokenPayload | null {
  try {
    const decoded = jwt.verify(rawToken, jwtSecret) as AuthTokenPayload;
    if (decoded.kind !== expectedKind) return null;
    return decoded;
  } catch {
    return null;
  }
}

function extractBearerToken(authorizationHeader?: string) {
  if (!authorizationHeader) return null;
  const [scheme, token] = authorizationHeader.split(" ");
  if (scheme !== "Bearer" || !token) return null;
  return token;
}

function isAdminOnlyRoute(method: string, path: string) {
  return adminOnly.some((rule) => {
    if (rule.method !== method) return false;
    if ("path" in rule) {
      return rule.path === path;
    }
    return path.startsWith(rule.pathPrefix);
  });
}

function roleAllowsRoute(role: Role, method: string, path: string) {
  if (role === "admin") return true;
  if (isAdminOnlyRoute(method, path)) return false;
  if (method === "GET") return true;
  return role === "agent";
}

async function verifyOperatorPassword(password: string) {
  if (operator.passwordHash) {
    return bcrypt.compare(password, operator.passwordHash);
  }
  return password === operator.password;
}

function publishChannelEvent(channel: string, data: unknown) {
  const message = JSON.stringify({
    channel,
    timestamp: new Date().toISOString(),
    data
  });
  for (const client of wsClients) {
    client.send(message);
  }
}

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

server.addHook("preHandler", async (request, reply) => {
  const path = toPath(request.url);
  const method = request.method.toUpperCase();

  if (!authRequired || publicRoutes.has(path)) {
    return;
  }

  const token = extractBearerToken(request.headers.authorization);
  if (!token) {
    return reply.code(401).send({
      error: "missing_token"
    });
  }

  const payload = verifyToken(token, "access");
  if (!payload) {
    return reply.code(401).send({
      error: "invalid_or_expired_token"
    });
  }

  if (!roleAllowsRoute(payload.role, method, path)) {
    return reply.code(403).send({
      error: "insufficient_role",
      role: payload.role
    });
  }
});

server.get("/v1/ws", { websocket: true }, (socket, request) => {
  if (authRequired) {
    const queryToken = (request.query as { token?: string }).token;
    const token = queryToken ?? extractBearerToken(request.headers.authorization);
    if (!token || !verifyToken(token, "access")) {
      socket.send(
        JSON.stringify({
          channel: "connection_error",
          timestamp: new Date().toISOString(),
          data: { error: "unauthorized" }
        })
      );
      socket.close(4001, "unauthorized");
      return;
    }
  }

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

  const validEmail = body.email.toLowerCase() === operator.email.toLowerCase();
  const validPassword = await verifyOperatorPassword(body.password);
  if (!validEmail || !validPassword) {
    return reply.code(401).send({ error: "invalid_credentials" });
  }

  const tokenPayload = {
    sub: operator.id,
    email: operator.email,
    role: operator.role
  };
  const accessToken = createToken(tokenPayload, "access");
  const refreshToken = createToken(tokenPayload, "refresh");

  return reply.send({
    user: {
      id: operator.id,
      email: operator.email,
      role: operator.role
    },
    access_token: accessToken,
    refresh_token: refreshToken,
    expires_in_seconds: accessTokenTtlSeconds
  });
});

server.post("/v1/auth/refresh", async (request, reply) => {
  const body = z
    .object({
      refresh_token: z.string().min(10)
    })
    .parse(request.body);

  const decoded = verifyToken(body.refresh_token, "refresh");
  if (!decoded) {
    return reply.code(401).send({ error: "invalid_refresh_token" });
  }

  const accessToken = createToken(
    {
      sub: decoded.sub,
      email: decoded.email,
      role: decoded.role
    },
    "access"
  );

  return {
    access_token: accessToken,
    expires_in_seconds: accessTokenTtlSeconds
  };
});

server.post("/v1/auth/logout", async () => {
  return { ok: true };
});

server.get("/v1/auth/me", async (request, reply) => {
  if (!authRequired) {
    return {
      user: {
        id: operator.id,
        email: operator.email,
        role: operator.role
      },
      auth_required: false
    };
  }
  const token = extractBearerToken(request.headers.authorization);
  if (!token) {
    return reply.code(401).send({ error: "missing_token" });
  }
  const payload = verifyToken(token, "access");
  if (!payload) {
    return reply.code(401).send({ error: "invalid_or_expired_token" });
  }
  return {
    user: {
      id: payload.sub,
      email: payload.email,
      role: payload.role
    },
    auth_required: true
  };
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

server.get("/v1/orders/:requestId", async (request, reply) => {
  const { requestId } = request.params as { requestId: string };
  const { status, payload } = await proxyGet(
    `${urls.execution}/v1/orders/${requestId}`
  );
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

server.post("/v1/autonomy/kill-switch", async (request, reply) => {
  const { status, payload } = await proxyPost(
    `${urls.orchestrator}/v1/autonomy/kill-switch`,
    request.body
  );
  publishChannelEvent("risk.alert", payload);
  publishChannelEvent("autonomy.state_changed", payload);
  return reply.code(status).send(payload);
});

server.post("/v1/autonomy/resume", async (request, reply) => {
  const { status, payload } = await proxyPost(
    `${urls.orchestrator}/v1/autonomy/resume`,
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
  if (payload?.status === "rejected") {
    publishChannelEvent("risk.alert", payload);
  } else {
    publishChannelEvent("order.executed", payload);
  }
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

