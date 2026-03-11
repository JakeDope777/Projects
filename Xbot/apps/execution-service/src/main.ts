import { randomUUID } from "node:crypto";
import Fastify from "fastify";
import cors from "@fastify/cors";
import { z } from "zod";
import {
  createEventEnvelope,
  InMemoryEventBus,
  JsonlLedger
} from "@xbot/shared-events";
import type {
  ApprovalDecision,
  HealthResponse,
  OrderRequest
} from "@xbot/shared-contracts";
import { PolymarketAdapter } from "./venues/polymarket-adapter.js";

const server = Fastify({ logger: true });
await server.register(cors, { origin: true });

const adapter = new PolymarketAdapter();
const events = new InMemoryEventBus();
const ledger = new JsonlLedger(
  process.env.LEDGER_PATH ?? "/tmp/xbot-decision-ledger.jsonl"
);

const approvals = new Map<string, { request: OrderRequest; created_at: string }>();
const orderStatus = new Map<string, string>();

function requiresApproval(order: OrderRequest, mode: string): boolean {
  if (mode === "approval_required") return true;
  return order.requires_approval;
}

let autonomyMode = process.env.DEFAULT_AUTONOMY_MODE ?? "approval_required";

server.get("/health", async () => {
  const payload: HealthResponse = {
    status: "healthy",
    version: "0.1.0",
    timestamp: new Date().toISOString(),
    checks: {
      adapter: "healthy",
      event_bus: "healthy"
    }
  };
  return payload;
});

server.get("/v1/approvals/pending", async () => {
  return {
    count: approvals.size,
    items: Array.from(approvals.values())
  };
});

server.post("/v1/approvals/decision", async (request, reply) => {
  const decision = z
    .object({
      approval_id: z.string(),
      request_id: z.string(),
      approved: z.boolean(),
      actor_id: z.string(),
      reason: z.string().optional(),
      decided_at: z.string().optional()
    })
    .parse(request.body) as ApprovalDecision;

  const pending = approvals.get(decision.request_id);
  if (!pending) {
    return reply.code(404).send({ error: "approval_request_not_found" });
  }

  if (!decision.approved) {
    orderStatus.set(decision.request_id, "rejected");
    approvals.delete(decision.request_id);
    await events.publish(
      createEventEnvelope("execution-service", "approval.rejected.v1", decision.request_id, "risk-policy-v1", {
        approval_id: decision.approval_id,
        actor_id: decision.actor_id,
        reason: decision.reason
      })
    );
    await ledger.append(
      createEventEnvelope("execution-service", "approval.rejected.v1", decision.request_id, "risk-policy-v1", {
        approval_id: decision.approval_id,
        actor_id: decision.actor_id,
        reason: decision.reason
      })
    );
    return {
      request_id: decision.request_id,
      status: "rejected"
    };
  }

  const executed = await adapter.createOrder(pending.request);
  approvals.delete(decision.request_id);
  orderStatus.set(decision.request_id, executed.status);
  await events.publish(
    createEventEnvelope("execution-service", "order.executed.v1", decision.request_id, "risk-policy-v1", {
      request_id: decision.request_id,
      venue_order_id: executed.venue_order_id,
      status: executed.status
    })
  );
  await ledger.append(
    createEventEnvelope("execution-service", "order.executed.v1", decision.request_id, "risk-policy-v1", {
      request_id: decision.request_id,
      venue_order_id: executed.venue_order_id,
      status: executed.status
    })
  );
  return {
    request_id: decision.request_id,
    approval_id: decision.approval_id,
    status: executed.status,
    venue_order_id: executed.venue_order_id
  };
});

server.post("/v1/orders/create", async (request, reply) => {
  const order = z
    .object({
      request_id: z.string().optional(),
      correlation_id: z.string().optional(),
      market_id: z.string(),
      side: z.enum(["buy", "sell"]),
      quantity: z.number().positive(),
      limit_price: z.number().positive(),
      strategy_id: z.string(),
      confidence: z.number().min(0).max(1).default(0.5),
      requires_approval: z.boolean().optional(),
      requested_at: z.string().optional(),
      metadata: z.record(z.any()).optional(),
      autonomy_mode: z.string().optional()
    })
    .parse(request.body);

  const requestId = order.request_id ?? randomUUID();
  const payload: OrderRequest = {
    request_id: requestId,
    correlation_id: order.correlation_id ?? requestId,
    market_id: order.market_id,
    side: order.side,
    quantity: order.quantity,
    limit_price: order.limit_price,
    strategy_id: order.strategy_id,
    confidence: order.confidence,
    requires_approval: order.requires_approval ?? true,
    requested_at: order.requested_at ?? new Date().toISOString(),
    metadata: order.metadata ?? {}
  };

  const mode = order.autonomy_mode ?? autonomyMode;
  if (requiresApproval(payload, mode)) {
    approvals.set(requestId, {
      request: payload,
      created_at: new Date().toISOString()
    });
    orderStatus.set(requestId, "pending_approval");

    await events.publish(
      createEventEnvelope("execution-service", "approval.required.v1", payload.correlation_id, "risk-policy-v1", {
        request_id: requestId,
        market_id: payload.market_id,
        side: payload.side,
        quantity: payload.quantity
      })
    );
    await ledger.append(
      createEventEnvelope("execution-service", "approval.required.v1", payload.correlation_id, "risk-policy-v1", {
        request_id: requestId,
        market_id: payload.market_id,
        side: payload.side,
        quantity: payload.quantity
      })
    );
    return reply.code(202).send({
      request_id: requestId,
      status: "pending_approval"
    });
  }

  const executed = await adapter.createOrder(payload);
  orderStatus.set(requestId, executed.status);
  await events.publish(
    createEventEnvelope("execution-service", "order.executed.v1", payload.correlation_id, "risk-policy-v1", {
      request_id: requestId,
      venue_order_id: executed.venue_order_id,
      status: executed.status
    })
  );
  await ledger.append(
    createEventEnvelope("execution-service", "order.executed.v1", payload.correlation_id, "risk-policy-v1", {
      request_id: requestId,
      venue_order_id: executed.venue_order_id,
      status: executed.status
    })
  );

  return reply.code(201).send({
    request_id: requestId,
    status: executed.status,
    venue_order_id: executed.venue_order_id
  });
});

server.post("/v1/orders/cancel", async (request, reply) => {
  const body = z.object({ venue_order_id: z.string() }).parse(request.body);
  const cancelled = await adapter.cancelOrder(body.venue_order_id);
  return reply.send(cancelled);
});

server.put("/v1/internal/autonomy-mode", async (request) => {
  const body = z.object({ mode: z.string() }).parse(request.body);
  autonomyMode = body.mode;
  return { mode: autonomyMode };
});

const port = Number(process.env.PORT ?? "4003");
await server.listen({ host: "0.0.0.0", port });
