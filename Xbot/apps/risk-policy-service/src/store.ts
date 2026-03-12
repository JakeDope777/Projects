import { Pool } from "pg";
import type { RiskPreset } from "@xbot/shared-contracts";

export interface RiskState {
  presets: Map<string, RiskPreset>;
  activePresetKey: string;
}

export interface RiskStore {
  readonly backend: "memory" | "postgres";
  init(seedState: RiskState): Promise<RiskState>;
  isHealthy(): Promise<boolean>;
  savePreset(name: string, preset: RiskPreset): Promise<void>;
  setActivePreset(name: string): Promise<void>;
}

class MemoryRiskStore implements RiskStore {
  readonly backend = "memory" as const;
  private state: RiskState = {
    presets: new Map(),
    activePresetKey: "conservative"
  };

  async init(seedState: RiskState): Promise<RiskState> {
    this.state = {
      presets: new Map(seedState.presets),
      activePresetKey: seedState.activePresetKey
    };
    return this.state;
  }

  async isHealthy(): Promise<boolean> {
    return true;
  }

  async savePreset(name: string, preset: RiskPreset): Promise<void> {
    this.state.presets.set(name, preset);
  }

  async setActivePreset(name: string): Promise<void> {
    this.state.activePresetKey = name;
  }
}

class PostgresRiskStore implements RiskStore {
  readonly backend = "postgres" as const;
  private readonly pool: Pool;

  constructor(connectionString: string) {
    this.pool = new Pool({ connectionString });
  }

  async init(seedState: RiskState): Promise<RiskState> {
    await this.pool.query(`
      CREATE TABLE IF NOT EXISTS risk_presets (
        name VARCHAR(64) PRIMARY KEY,
        payload JSONB NOT NULL,
        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
      )
    `);
    await this.pool.query(`
      CREATE TABLE IF NOT EXISTS risk_runtime_state (
        key VARCHAR(64) PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
      )
    `);

    const countResult = await this.pool.query<{ count: string }>(
      "SELECT COUNT(*)::text AS count FROM risk_presets"
    );
    if (Number(countResult.rows[0]?.count ?? "0") === 0) {
      for (const [name, preset] of seedState.presets.entries()) {
        await this.pool.query(
          "INSERT INTO risk_presets (name, payload) VALUES ($1, $2::jsonb)",
          [name, JSON.stringify(preset)]
        );
      }
      await this.pool.query(
        `
        INSERT INTO risk_runtime_state (key, value)
        VALUES ('active_preset', $1)
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
        `,
        [seedState.activePresetKey]
      );
      return seedState;
    }

    const presetRows = await this.pool.query<{
      name: string;
      payload: RiskPreset;
    }>("SELECT name, payload FROM risk_presets");

    const stateRows = await this.pool.query<{
      key: string;
      value: string;
    }>("SELECT key, value FROM risk_runtime_state WHERE key = 'active_preset'");

    const loadedPresets = new Map<string, RiskPreset>();
    for (const row of presetRows.rows) {
      loadedPresets.set(row.name, row.payload);
    }

    const activePreset =
      stateRows.rows[0]?.value ??
      (loadedPresets.has(seedState.activePresetKey)
        ? seedState.activePresetKey
        : loadedPresets.keys().next().value) ??
      "conservative";

    return {
      presets: loadedPresets,
      activePresetKey: activePreset
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

  async savePreset(name: string, preset: RiskPreset): Promise<void> {
    await this.pool.query(
      `
      INSERT INTO risk_presets (name, payload, updated_at)
      VALUES ($1, $2::jsonb, NOW())
      ON CONFLICT (name) DO UPDATE SET
        payload = EXCLUDED.payload,
        updated_at = NOW()
      `,
      [name, JSON.stringify(preset)]
    );
  }

  async setActivePreset(name: string): Promise<void> {
    await this.pool.query(
      `
      INSERT INTO risk_runtime_state (key, value, updated_at)
      VALUES ('active_preset', $1, NOW())
      ON CONFLICT (key) DO UPDATE SET
        value = EXCLUDED.value,
        updated_at = NOW()
      `,
      [name]
    );
  }
}

export async function createRiskStore(
  seedState: RiskState
): Promise<{ store: RiskStore; state: RiskState }> {
  const url = process.env.POSTGRES_URL;
  if (!url) {
    const memory = new MemoryRiskStore();
    const state = await memory.init(seedState);
    return { store: memory, state };
  }

  try {
    const postgres = new PostgresRiskStore(url);
    const state = await postgres.init(seedState);
    return { store: postgres, state };
  } catch (error) {
    console.error("[risk-store] postgres unavailable, falling back to memory", error);
    const memory = new MemoryRiskStore();
    const state = await memory.init(seedState);
    return { store: memory, state };
  }
}
