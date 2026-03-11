CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  role VARCHAR(32) NOT NULL CHECK (role IN ('admin', 'agent', 'viewer')),
  organization_id UUID,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  last_login_at TIMESTAMP NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS bots (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(100) UNIQUE NOT NULL,
  description TEXT NULL,
  organization_id UUID,
  configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
  model_config JSONB NOT NULL DEFAULT '{}'::jsonb,
  personality TEXT NULL,
  fallback_message TEXT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id VARCHAR(255) NOT NULL,
  bot_id UUID REFERENCES bots(id),
  user_id VARCHAR(255) NOT NULL,
  channel VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL CHECK (status IN ('active', 'waiting', 'resolved', 'escalated')),
  sentiment VARCHAR(64),
  metadata JSONB,
  started_at TIMESTAMP NOT NULL DEFAULT NOW(),
  ended_at TIMESTAMP NULL,
  last_activity_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  role VARCHAR(32) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  intent VARCHAR(255),
  confidence DECIMAL(5, 4),
  sentiment VARCHAR(64),
  entities JSONB,
  sources JSONB,
  metadata JSONB,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS knowledge_base (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  bot_id UUID REFERENCES bots(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  file_url VARCHAR(500),
  file_type VARCHAR(50),
  embedding_id VARCHAR(255),
  metadata JSONB,
  is_indexed BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS risk_policy_versions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  policy_name VARCHAR(64) NOT NULL,
  policy_version VARCHAR(64) NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trade_orders (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  request_id VARCHAR(128) UNIQUE NOT NULL,
  market_id VARCHAR(255) NOT NULL,
  venue VARCHAR(64) NOT NULL,
  side VARCHAR(8) NOT NULL CHECK (side IN ('buy', 'sell')),
  quantity NUMERIC(20, 8) NOT NULL,
  limit_price NUMERIC(20, 8) NOT NULL,
  status VARCHAR(64) NOT NULL,
  requires_approval BOOLEAN NOT NULL,
  metadata JSONB,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS approvals (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  request_id VARCHAR(128) NOT NULL,
  actor_id VARCHAR(128) NOT NULL,
  approved BOOLEAN NOT NULL,
  reason TEXT,
  decided_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS position_snapshots (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  market_id VARCHAR(255) NOT NULL,
  side VARCHAR(8) NOT NULL CHECK (side IN ('buy', 'sell')),
  quantity NUMERIC(20, 8) NOT NULL,
  average_entry_price NUMERIC(20, 8) NOT NULL,
  mark_price NUMERIC(20, 8) NOT NULL,
  unrealized_pnl NUMERIC(20, 8) NOT NULL,
  realized_pnl NUMERIC(20, 8) NOT NULL,
  recorded_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS autonomy_gate_results (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  window_days INT NOT NULL,
  sharpe_like_ratio NUMERIC(10, 4) NOT NULL,
  cumulative_return_pct NUMERIC(10, 4) NOT NULL,
  max_drawdown_pct NUMERIC(10, 4) NOT NULL,
  critical_violations INT NOT NULL,
  passed BOOLEAN NOT NULL,
  failures JSONB,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_bot_status_activity
  ON conversations(bot_id, status, last_activity_at);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_created
  ON messages(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_messages_intent_created
  ON messages(intent, created_at);
CREATE INDEX IF NOT EXISTS idx_users_org_active
  ON users(organization_id, is_active);
CREATE INDEX IF NOT EXISTS idx_kb_bot_indexed
  ON knowledge_base(bot_id, is_indexed);

