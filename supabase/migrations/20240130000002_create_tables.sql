-- Sponge P0 Schema: Tables
-- Migration: 20240130000002_create_tables
-- Idempotent: Uses IF NOT EXISTS

-- Sessions: Group chat turns and knowledge graph into projects
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_name VARCHAR(255),
    topic TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Chat turns: Conversation history
CREATE TABLE IF NOT EXISTS chat_turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,
    role chat_role NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Nodes: Knowledge graph vertices
CREATE TABLE IF NOT EXISTS nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    node_type node_type NOT NULL,
    title VARCHAR(500) NOT NULL,
    summary TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Edges: Knowledge graph relationships
CREATE TABLE IF NOT EXISTS edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    source_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    edge_type edge_type NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Nuggets: Prioritization wrapper for high-value nodes
CREATE TABLE IF NOT EXISTS nuggets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id UUID NOT NULL UNIQUE REFERENCES nodes(id) ON DELETE CASCADE,
    nugget_type nugget_type NOT NULL,
    title VARCHAR(500) NOT NULL,
    short_summary TEXT NOT NULL,
    score INTEGER NOT NULL DEFAULT 0 CHECK (score >= 0 AND score <= 100),
    dimension_scores JSONB,
    missing_fields JSONB,
    next_questions JSONB,
    status nugget_status NOT NULL DEFAULT 'new',
    user_feedback user_feedback,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Provenance: Track node origins
CREATE TABLE IF NOT EXISTS provenance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    source_type source_type NOT NULL,
    source_id UUID NOT NULL,
    confidence confidence_level NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Documents: Uploaded file metadata
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    filename VARCHAR(500) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    storage_path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Trigger to auto-update updated_at on sessions
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_sessions_updated_at ON sessions;
CREATE TRIGGER update_sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
