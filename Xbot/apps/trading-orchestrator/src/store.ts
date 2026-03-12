import { Pool } from "pg";
import type { AutonomyGateMetrics, AutonomyMode } from "@xbot/shared-contracts";

export interface OrchestratorState {
  mode: AutonomyMode;
  metrics: AutonomyGateMetrics;
}

export interface OrchestratorStore {
  readonly backend: "memory" | "postgres";
  init(defaultState: OrchestratorState): Promise<OrchestratorState>;
  isHealthy(): Promise<boolean>;
  setMode(mode: AutonomyMode): Promise<void>;
  setMetrics(metrics: AutonomyGateMetrics): Promise<void>;
}

class MemoryOrchestratorStore implements OrchestratorStore {
  readonly backend = "memory" as const;
  private state: OrchestratorState = {
    mode: "approval_required",
    metrics: {
      window_days: 30,
      sharpe_like_ratio: 0,
      cumulative_return_pct: 0,
      max_drawdown_pct: 0,
      critical_violations: 0,
      evaluated_at: new Date().toISOString()
    }
  };

  async init(defaultState: OrchestratorState): Promise<OrchestratorState> {
    this.state = defaultState;
    return this.state;
  }

  async isHealthy(): Promise<boolean> {
    return true;
  }

  async setMode(mode: AutonomyMode): Promise<void> {
    this.state.mode = mode;
  }

  async setMetrics(metrics: AutonomyGateMetrics): Promise<void> {
    this.state.metrics = metrics;
  }
}

class PostgresOrchestratorStore implements OrchestratorStore {
  readonly backend = "postgres" as const;
  private readonly pool: Pool;

  constructor(connectionString: string) {
    this.pool = new Pool({ connectionString });
  }

  async init(defaultState: OrchestratorState): Promise<OrchestratorState> {
    await this.pool.query(`
      CREATE TABLE IF NOT EXISTS autonomy_runtime_state (
        key VARCHAR(64) PRIMARY KEY,
        value JSONB NOT NULL,
        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
      )
    `);

    await this.pool.query(
      `
      INSERT INTO autonomy_runtime_state (key, value)
      VALUES ('autonomy_mode', $1::jsonb)
      ON CONFLICT (key) DO NOTHING
      `,
      [JSON.stringify({ mode: defaultState.mode })]
    );
    await this.pool.query(
      `
      INSERT INTO autonomy_runtime_state (key, value)
      VALUES ('autonomy_gate_metrics', $1::jsonb)
      ON CONFLICT (key) DO NOTHING
      `,
      [JSON.stringify(defaultState.metrics)]
    );

    const rows = await this.pool.query<{ key: string; value: Record<string, unknown> }>(
      `
      SELECT key, value FROM autonomy_runtime_state
      WHERE key IN ('autonomy_mode', 'autonomy_gate_metrics')
      `
    );

    const modeRow = rows.rows.find(
      (row: { key: string; value: Record<string, unknown> }) =>
        row.key === "autonomy_mode"
    );
    const metricsRow = rows.rows.find(
      (row: { key: string; value: Record<string, unknown> }) =>
        row.key === "autonomy_gate_metrics"
    );

    return {
      mode: (modeRow?.value.mode as AutonomyMode) ?? defaultState.mode,
      metrics: (metricsRow?.value as unknown as AutonomyGateMetrics) ?? defaultState.metrics
    };
  }

  async isHealthy(): Promise<boolean> {
    try {
      await this.pool.query("SELECT 1");
      return true;
    } catch {
      return false;
    }
  }

  async setMode(mode: AutonomyMode): Promise<void> {
    await this.pool.query(
      `
      INSERT INTO autonomy_runtime_state (key, value, updated_at)
      VALUES ('autonomy_mode', $1::jsonb, NOW())
      ON CONFLICT (key) DO UPDATE SET
        value = EXCLUDED.value,
        updated_at = NOW()
      `,
      [JSON.stringify({ mode })]
    );
  }

  async setMetrics(metrics: AutonomyGateMetrics): Promise<void> {
    await this.pool.query(
      `
      INSERT INTO autonomy_runtime_state (key, value, updated_at)
      VALUES ('autonomy_gate_metrics', $1::jsonb, NOW())
      ON CONFLICT (key) DO UPDATE SET
        value = EXCLUDED.value,
        updated_at = NOW()
      `,
      [JSON.stringify(metrics)]
    );
  }
}

export async function createOrchestratorStore(
  defaultState: OrchestratorState
): Promise<{ store: OrchestratorStore; state: OrchestratorState }> {
  const url = process.env.POSTGRES_URL;
  if (!url) {
    const memory = new MemoryOrchestratorStore();
    const state = await memory.init(defaultState);
    return { store: memory, state };
  }

  try {
    const postgres = new PostgresOrchestratorStore(url);
    const state = await postgres.init(defaultState);
    return { store: postgres, state };
  } catch (error) {
    console.error(
      "[trading-orchestrator-store] postgres unavailable, falling back to memory",
      error
    );
    const memory = new MemoryOrchestratorStore();
    const state = await memory.init(defaultState);
    return { store: memory, state };
  }
}
