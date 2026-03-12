import { Pool } from "pg";
import type { Position } from "@xbot/shared-contracts";

export interface AnalyticsStore {
  readonly backend: "memory" | "postgres";
  init(): Promise<void>;
  isHealthy(): Promise<boolean>;
  listPositions(): Promise<Position[]>;
  upsertPosition(position: Position): Promise<void>;
}

class MemoryAnalyticsStore implements AnalyticsStore {
  readonly backend = "memory" as const;
  private readonly positions = new Map<string, Position>();

  async init(): Promise<void> {
    // no-op
  }

  async isHealthy(): Promise<boolean> {
    return true;
  }

  async listPositions(): Promise<Position[]> {
    return Array.from(this.positions.values());
  }

  async upsertPosition(position: Position): Promise<void> {
    this.positions.set(position.position_id, position);
  }
}

class PostgresAnalyticsStore implements AnalyticsStore {
  readonly backend = "postgres" as const;
  private readonly pool: Pool;

  constructor(connectionString: string) {
    this.pool = new Pool({ connectionString });
  }

  async init(): Promise<void> {
    await this.pool.query(`
      CREATE TABLE IF NOT EXISTS positions_current (
        position_id VARCHAR(128) PRIMARY KEY,
        market_id VARCHAR(255) NOT NULL,
        side VARCHAR(8) NOT NULL,
        quantity DOUBLE PRECISION NOT NULL,
        average_entry_price DOUBLE PRECISION NOT NULL,
        mark_price DOUBLE PRECISION NOT NULL,
        unrealized_pnl DOUBLE PRECISION NOT NULL,
        realized_pnl DOUBLE PRECISION NOT NULL,
        opened_at TIMESTAMP NOT NULL,
        updated_at TIMESTAMP NOT NULL
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

  async listPositions(): Promise<Position[]> {
    const result = await this.pool.query<{
      position_id: string;
      market_id: string;
      side: "buy" | "sell";
      quantity: number;
      average_entry_price: number;
      mark_price: number;
      unrealized_pnl: number;
      realized_pnl: number;
      opened_at: Date;
      updated_at: Date;
    }>(
      `
      SELECT position_id, market_id, side, quantity, average_entry_price,
             mark_price, unrealized_pnl, realized_pnl, opened_at, updated_at
      FROM positions_current
      ORDER BY updated_at DESC
      `
    );

    return result.rows.map((row: {
      position_id: string;
      market_id: string;
      side: "buy" | "sell";
      quantity: number;
      average_entry_price: number;
      mark_price: number;
      unrealized_pnl: number;
      realized_pnl: number;
      opened_at: Date;
      updated_at: Date;
    }) => ({
      position_id: row.position_id,
      market_id: row.market_id,
      side: row.side,
      quantity: Number(row.quantity),
      average_entry_price: Number(row.average_entry_price),
      mark_price: Number(row.mark_price),
      unrealized_pnl: Number(row.unrealized_pnl),
      realized_pnl: Number(row.realized_pnl),
      opened_at: new Date(row.opened_at).toISOString(),
      updated_at: new Date(row.updated_at).toISOString()
    }));
  }

  async upsertPosition(position: Position): Promise<void> {
    await this.pool.query(
      `
      INSERT INTO positions_current (
        position_id, market_id, side, quantity, average_entry_price,
        mark_price, unrealized_pnl, realized_pnl, opened_at, updated_at
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
      ON CONFLICT (position_id) DO UPDATE SET
        market_id = EXCLUDED.market_id,
        side = EXCLUDED.side,
        quantity = EXCLUDED.quantity,
        average_entry_price = EXCLUDED.average_entry_price,
        mark_price = EXCLUDED.mark_price,
        unrealized_pnl = EXCLUDED.unrealized_pnl,
        realized_pnl = EXCLUDED.realized_pnl,
        opened_at = EXCLUDED.opened_at,
        updated_at = EXCLUDED.updated_at
      `,
      [
        position.position_id,
        position.market_id,
        position.side,
        position.quantity,
        position.average_entry_price,
        position.mark_price,
        position.unrealized_pnl,
        position.realized_pnl,
        position.opened_at,
        position.updated_at
      ]
    );
  }
}

export async function createAnalyticsStore(): Promise<AnalyticsStore> {
  const url = process.env.POSTGRES_URL;
  if (!url) {
    const memory = new MemoryAnalyticsStore();
    await memory.init();
    return memory;
  }

  try {
    const postgres = new PostgresAnalyticsStore(url);
    await postgres.init();
    return postgres;
  } catch (error) {
    console.error(
      "[portfolio-analytics-store] postgres unavailable, falling back to memory",
      error
    );
    const memory = new MemoryAnalyticsStore();
    await memory.init();
    return memory;
  }
}
