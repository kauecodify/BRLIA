-- Esquema inicial: ledger particionado, outbox e WORM.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS ledger_entries (
  correlation_id text NOT NULL,
  entry_id text NOT NULL,
  account text NOT NULL,
  account_name text,
  side char(1) NOT NULL CHECK (side IN ('D', 'C')),
  amount_minor bigint NOT NULL CHECK (amount_minor >= 0),
  currency char(3) NOT NULL,
  scale int NOT NULL DEFAULT 2,
  nature text NOT NULL CHECK (nature IN ('capital', 'compensacao', 'operacao')),
  pool_id text,
  window_seq bigint,
  idempotency_key text,
  entry_hash text NOT NULL,
  previous_hash text,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (entry_id, created_at)
) PARTITION BY RANGE (created_at);

CREATE TABLE IF NOT EXISTS ledger_entries_default PARTITION OF ledger_entries
  DEFAULT;

CREATE TABLE IF NOT EXISTS outbox_events (
  event_id uuid PRIMARY KEY,
  event_type text NOT NULL,
  pool_id text,
  payload jsonb NOT NULL,
  published boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_worm (
  record_hash text PRIMARY KEY,
  previous_hash text,
  kind text NOT NULL,
  pool_id text,
  payload jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Genesis imutavel: sem UPDATE e sem DELETE para a role operacional.
CREATE ROLE brlia_app NOLOGIN;
GRANT SELECT, INSERT ON ledger_entries, ledger_entries_default, outbox_events TO brlia_app;
GRANT SELECT, INSERT ON audit_worm TO brlia_app;

CREATE INDEX IF NOT EXISTS idx_ledger_pool ON ledger_entries (pool_id) WHERE pool_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_outbox_unpublished ON outbox_events (created_at) WHERE published = false;
