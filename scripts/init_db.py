"""Initialize PostgreSQL schema for ECP.

The vector column dimension is read from settings.embedding_dim so that
swapping embedding providers (Voyage 1024 ↔ OpenAI 1536) is a single
env-var change. Re-run this script after changing the dim.
"""
import asyncio
import asyncpg
from src.config import settings

POSTGRES_DSN = settings.postgres_dsn
EMBEDDING_DIM = settings.embedding_dim

SCHEMA = f"""
-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Assets table (glossary terms, data contracts, tribal knowledge, etc.)
CREATE TABLE IF NOT EXISTS assets (
    id VARCHAR(50) PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    content JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    CONSTRAINT valid_type CHECK (type IN (
        'glossary_term', 'data_contract', 'validation_rule',
        'tribal_knowledge', 'policy', 'query_template',
        'migration_record', 'calendar_config', 'metric_definition'
    ))
);

CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(type);
CREATE INDEX IF NOT EXISTS idx_assets_content_gin ON assets USING GIN(content);

-- Resolution sessions (decision trace graph)
CREATE TABLE IF NOT EXISTS resolution_sessions (
    query_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    user_context JSONB NOT NULL DEFAULT '{{}}',
    original_query TEXT NOT NULL,
    parsed_intent JSONB NOT NULL DEFAULT '{{}}',
    resolution_dag JSONB NOT NULL DEFAULT '[]',
    stores_queried JSONB NOT NULL DEFAULT '[]',
    definitions_selected JSONB NOT NULL DEFAULT '{{}}',
    precedents_used JSONB DEFAULT '[]',
    execution_plan JSONB NOT NULL DEFAULT '[]',
    status VARCHAR(40) NOT NULL DEFAULT 'parsing',
    confidence JSONB NOT NULL DEFAULT '{{}}',
    result JSONB,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    feedback_status VARCHAR(20) DEFAULT 'pending',
    feedback_at TIMESTAMP,
    feedback_by VARCHAR(100),
    correction_details JSONB,
    CONSTRAINT valid_status CHECK (status IN (
        'parsing', 'resolving', 'planning', 'authorizing',
        'executing', 'validating', 'complete', 'failed',
        'disambiguation_required'
    ))
);

CREATE INDEX IF NOT EXISTS idx_resolution_user ON resolution_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_resolution_status ON resolution_sessions(status);
CREATE INDEX IF NOT EXISTS idx_resolution_feedback ON resolution_sessions(feedback_status);
CREATE INDEX IF NOT EXISTS idx_resolution_started ON resolution_sessions(started_at);

-- Resolution embeddings (for precedent search) — dim from settings.embedding_dim
CREATE TABLE IF NOT EXISTS resolution_embeddings (
    query_id VARCHAR(50) PRIMARY KEY REFERENCES resolution_sessions(query_id),
    query_embedding vector({EMBEDDING_DIM}),
    intent_embedding vector({EMBEDDING_DIM}),
    resolution_embedding vector({EMBEDDING_DIM}),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Drift events
CREATE TABLE IF NOT EXISTS drift_events (
    id VARCHAR(50) PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    affected_object TEXT NOT NULL,
    affected_contracts JSONB,
    details JSONB NOT NULL,
    detected_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(100),
    resolution_action TEXT,
    severity VARCHAR(20) NOT NULL DEFAULT 'info',
    CONSTRAINT valid_severity CHECK (severity IN ('critical', 'warning', 'info'))
);

CREATE INDEX IF NOT EXISTS idx_drift_severity ON drift_events(severity);

-- Contract version history
CREATE TABLE IF NOT EXISTS contract_versions (
    id SERIAL PRIMARY KEY,
    asset_id VARCHAR(50) REFERENCES assets(id),
    version INTEGER NOT NULL,
    content JSONB NOT NULL,
    change_reason TEXT,
    migration_event_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    is_current BOOLEAN DEFAULT true
);

-- OSI sync log
CREATE TABLE IF NOT EXISTS osi_sync_log (
    id SERIAL PRIMARY KEY,
    direction VARCHAR(10) NOT NULL,
    source_tool VARCHAR(100) NOT NULL,
    definitions_synced INTEGER NOT NULL,
    conflicts_detected INTEGER DEFAULT 0,
    conflicts_resolved INTEGER DEFAULT 0,
    sync_at TIMESTAMP DEFAULT NOW(),
    details JSONB
);
"""


MIGRATE_VECTOR_DIM = f"""
-- Drop and recreate vector tables if embedding dimension changed.
-- This is safe because embeddings are re-seeded on every seed_data run.
DO $$
DECLARE
    current_dim INTEGER;
BEGIN
    -- Check asset_vectors dimension
    SELECT atttypmod INTO current_dim
    FROM pg_attribute
    WHERE attrelid = 'asset_vectors'::regclass
      AND attname = 'embedding'
      AND NOT attisdropped;

    IF current_dim IS NOT NULL AND current_dim != {EMBEDDING_DIM} THEN
        RAISE NOTICE 'Embedding dim changed (% → %), recreating vector tables', current_dim, {EMBEDDING_DIM};
        DROP TABLE IF EXISTS asset_vectors CASCADE;
        DROP TABLE IF EXISTS resolution_embeddings CASCADE;
    END IF;
EXCEPTION
    WHEN undefined_table THEN NULL;  -- Tables don't exist yet
END $$;
"""


async def main():
    conn = await asyncpg.connect(POSTGRES_DSN)
    try:
        # Migrate vector dimension if it changed
        await conn.execute(MIGRATE_VECTOR_DIM)
        # Create all tables (IF NOT EXISTS is safe for non-vector tables)
        await conn.execute(SCHEMA)
        print(f"Schema created successfully (embedding_dim={EMBEDDING_DIM}).")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
