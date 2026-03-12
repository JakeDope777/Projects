import { Pool } from "pg";
import type { ApprovalDecision, OrderRequest } from "@xbot/shared-contracts";

export interface PendingApprovalRecord {
  request: OrderRequest;
  created_at: string;
}

export interface ExecutionStore {
  readonly backend: "memory" | "postgres";
  init(): Promise<void>;
  isHealthy(): Promise<boolean>;
  upsertOrder(
    order: OrderRequest,
    status: string,
    venueOrderId?: string
  ): Promise<void>;
  setOrderStatus(requestId: string, status: string, venueOrderId?: string): Promise<void>;
  getOrderStatus(requestId: string): Promise<string | null>;
  getPendingApproval(requestId: string): Promise<PendingApprovalRecord | null>;
  listPendingApprovals(): Promise<PendingApprovalRecord[]>;
  saveApproval(decision: ApprovalDecision): Promise<void>;
}

class MemoryExecutionStore implements ExecutionStore {
  readonly backend = "memory" as const;
  private readonly approvals = new Map<string, PendingApprovalRecord>();
  private readonly orderStatus = new Map<string, string>();

  async init(): Promise<void> {
    // no-op
  }

  async isHealthy(): Promise<boolean> {
    return true;
  }

  async upsertOrder(order: OrderRequest, status: string): Promise<void> {
    this.orderStatus.set(order.request_id, status);
    if (status === "pending_approval") {
      this.approvals.set(order.request_id, {
        request: order,
        created_at: new Date().toISOString()
      });
    }
  }

  async setOrderStatus(requestId: string, status: string): Promise<void> {
    this.orderStatus.set(requestId, status);
    if (status !== "pending_approval") {
      this.approvals.delete(requestId);
    }
  }

  async getOrderStatus(requestId: string): Promise<string | null> {
    return this.orderStatus.get(requestId) ?? null;
  }

  async getPendingApproval(requestId: string): Promise<PendingApprovalRecord | null> {
    return this.approvals.get(requestId) ?? null;
  }

  async listPendingApprovals(): Promise<PendingApprovalRecord[]> {
    return Array.from(this.approvals.values());
  }

  async saveApproval(_decision: ApprovalDecision): Promise<void> {
    // no-op
  }
}

class PostgresExecutionStore implements ExecutionStore {
  readonly backend = "postgres" as const;
  private readonly pool: Pool;

  constructor(connectionString: string) {
    this.pool = new Pool({ connectionString });
  }

  async init(): Promise<void> {
    await this.pool.query(`
      CREATE TABLE IF NOT EXISTS trade_orders (
        request_id VARCHAR(128) PRIMARY KEY,
        correlation_id VARCHAR(128),
        market_id VARCHAR(255) NOT NULL,
        strategy_id VARCHAR(255),
        side VARCHAR(8) NOT NULL,
        quantity DOUBLE PRECISION NOT NULL,
        limit_price DOUBLE PRECISION NOT NULL,
        confidence DOUBLE PRECISION NOT NULL,
        status VARCHAR(64) NOT NULL,
        venue VARCHAR(64) NOT NULL DEFAULT 'polymarket',
        venue_order_id VARCHAR(255),
        requires_approval BOOLEAN NOT NULL,
        requested_at TIMESTAMP NOT NULL,
        metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
      )
    `);
    await this.pool.query(
      "ALTER TABLE trade_orders ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(128)"
    );
    await this.pool.query(
      "ALTER TABLE trade_orders ADD COLUMN IF NOT EXISTS strategy_id VARCHAR(255)"
    );
    await this.pool.query(
      "ALTER TABLE trade_orders ADD COLUMN IF NOT EXISTS confidence DOUBLE PRECISION"
    );
    await this.pool.query(
      "ALTER TABLE trade_orders ADD COLUMN IF NOT EXISTS venue VARCHAR(64) DEFAULT 'polymarket'"
    );
    await this.pool.query(
      "ALTER TABLE trade_orders ADD COLUMN IF NOT EXISTS venue_order_id VARCHAR(255)"
    );
    await this.pool.query(
      "ALTER TABLE trade_orders ADD COLUMN IF NOT EXISTS requested_at TIMESTAMP"
    );
    await this.pool.query(`
      CREATE TABLE IF NOT EXISTS approvals (
        approval_id VARCHAR(128) UNIQUE NOT NULL,
        request_id VARCHAR(128) NOT NULL,
        actor_id VARCHAR(128) NOT NULL,
        approved BOOLEAN NOT NULL,
        reason TEXT,
        decided_at TIMESTAMP NOT NULL DEFAULT NOW()
      )
    `);
  }

  async isHealthy(): Promise<boolean> {
    try {
      await this.pool.query("SELECT 1");
      return true;
    } catch {
      return false;
    }
  }

  async upsertOrder(
    order: OrderRequest,
    status: string,
    venueOrderId?: string
  ): Promise<void> {
    await this.pool.query(
      `
      INSERT INTO trade_orders (
        request_id, correlation_id, market_id, strategy_id, side, quantity,
        limit_price, confidence, status, venue, venue_order_id, requires_approval,
        requested_at, metadata, created_at, updated_at
      )
      VALUES (
        $1, $2, $3, $4, $5, $6,
        $7, $8, $9, $10, $11, $12,
        $13, $14::jsonb, NOW(), NOW()
      )
      ON CONFLICT (request_id) DO UPDATE SET
        correlation_id = EXCLUDED.correlation_id,
        market_id = EXCLUDED.market_id,
        strategy_id = EXCLUDED.strategy_id,
        side = EXCLUDED.side,
        quantity = EXCLUDED.quantity,
        limit_price = EXCLUDED.limit_price,
        confidence = EXCLUDED.confidence,
        status = EXCLUDED.status,
        venue = EXCLUDED.venue,
        venue_order_id = EXCLUDED.venue_order_id,
        requires_approval = EXCLUDED.requires_approval,
        requested_at = EXCLUDED.requested_at,
        metadata = EXCLUDED.metadata,
        updated_at = NOW()
      `,
      [
        order.request_id,
        order.correlation_id,
        order.market_id,
        order.strategy_id,
        order.side,
        order.quantity,
        order.limit_price,
        order.confidence,
        status,
        "polymarket",
        venueOrderId ?? null,
        order.requires_approval,
        order.requested_at,
        JSON.stringify(order.metadata ?? {})
      ]
    );
  }

  async setOrderStatus(
    requestId: string,
    status: string,
    venueOrderId?: string
  ): Promise<void> {
    await this.pool.query(
      `
      UPDATE trade_orders
      SET status = $2,
          venue_order_id = COALESCE($3, venue_order_id),
          updated_at = NOW()
      WHERE request_id = $1
      `,
      [requestId, status, venueOrderId ?? null]
    );
  }

  async getOrderStatus(requestId: string): Promise<string | null> {
    const result = await this.pool.query<{ status: string }>(
      "SELECT status FROM trade_orders WHERE request_id = $1",
      [requestId]
    );
    return result.rows[0]?.status ?? null;
  }

  async getPendingApproval(requestId: string): Promise<PendingApprovalRecord | null> {
    const result = await this.pool.query<{
      request_id: string;
      correlation_id: string;
      market_id: string;
      side: "buy" | "sell";
      quantity: number;
      limit_price: number;
      strategy_id: string;
      confidence: number;
      requires_approval: boolean;
      requested_at: Date;
      metadata: Record<string, unknown>;
      created_at: Date;
    }>(
      `
      SELECT request_id, correlation_id, market_id, side, quantity, limit_price,
             strategy_id, confidence, requires_approval, requested_at, metadata, created_at
      FROM trade_orders
      WHERE request_id = $1 AND status = 'pending_approval'
      `,
      [requestId]
    );
    const row = result.rows[0];
    if (!row) return null;
    return {
      request: {
        request_id: row.request_id,
        correlation_id: row.correlation_id,
        market_id: row.market_id,
        side: row.side,
        quantity: Number(row.quantity),
        limit_price: Number(row.limit_price),
        strategy_id: row.strategy_id,
        confidence: Number(row.confidence),
        requires_approval: row.requires_approval,
        requested_at: new Date(row.requested_at).toISOString(),
        metadata: row.metadata ?? {}
      },
      created_at: new Date(row.created_at).toISOString()
    };
  }

  async listPendingApprovals(): Promise<PendingApprovalRecord[]> {
    const result = await this.pool.query<{
      request_id: string;
      correlation_id: string;
      market_id: string;
      side: "buy" | "sell";
      quantity: number;
      limit_price: number;
      strategy_id: string;
      confidence: number;
      requires_approval: boolean;
      requested_at: Date;
      metadata: Record<string, unknown>;
      created_at: Date;
    }>(
      `
      SELECT request_id, correlation_id, market_id, side, quantity, limit_price,
             strategy_id, confidence, requires_approval, requested_at, metadata, created_at
      FROM trade_orders
      WHERE status = 'pending_approval'
      ORDER BY created_at DESC
      `
    );
    return result.rows.map((row: {
      request_id: string;
      correlation_id: string;
      market_id: string;
      side: "buy" | "sell";
      quantity: number;
      limit_price: number;
      strategy_id: string;
      confidence: number;
      requires_approval: boolean;
      requested_at: Date;
      metadata: Record<string, unknown>;
      created_at: Date;
    }) => ({
      request: {
        request_id: row.request_id,
        correlation_id: row.correlation_id,
        market_id: row.market_id,
        side: row.side,
        quantity: Number(row.quantity),
        limit_price: Number(row.limit_price),
        strategy_id: row.strategy_id,
        confidence: Number(row.confidence),
        requires_approval: row.requires_approval,
        requested_at: new Date(row.requested_at).toISOString(),
        metadata: row.metadata ?? {}
      },
      created_at: new Date(row.created_at).toISOString()
    }));
  }

  async saveApproval(decision: ApprovalDecision): Promise<void> {
    await this.pool.query(
      `
      INSERT INTO approvals (approval_id, request_id, actor_id, approved, reason, decided_at)
      VALUES ($1, $2, $3, $4, $5, $6)
      ON CONFLICT (approval_id) DO NOTHING
      `,
      [
        decision.approval_id,
        decision.request_id,
        decision.actor_id,
        decision.approved,
        decision.reason ?? null,
        decision.decided_at ?? new Date().toISOString()
      ]
    );
  }
}

export async function createExecutionStore(): Promise<ExecutionStore> {
  const url = process.env.POSTGRES_URL;
  if (!url) {
    const memory = new MemoryExecutionStore();
    await memory.init();
    return memory;
  }

  try {
    const postgres = new PostgresExecutionStore(url);
    await postgres.init();
    return postgres;
  } catch (error) {
    console.error("[execution-store] postgres unavailable, falling back to memory", error);
    const memory = new MemoryExecutionStore();
    await memory.init();
    return memory;
  }
}
