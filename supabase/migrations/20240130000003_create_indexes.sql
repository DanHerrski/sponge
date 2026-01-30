-- Sponge P0 Schema: Indexes
-- Migration: 20240130000003_create_indexes
-- Idempotent: Uses IF NOT EXISTS

-- Chat turns: ordered retrieval by session
CREATE INDEX IF NOT EXISTS ix_chat_turns_session_turn
    ON chat_turns(session_id, turn_number);

-- Nodes: filter by session
CREATE INDEX IF NOT EXISTS ix_nodes_session
    ON nodes(session_id);

-- Nodes: HNSW index for vector similarity search (dedup/retrieval)
-- Uses cosine distance for semantic similarity
CREATE INDEX IF NOT EXISTS ix_nodes_embedding
    ON nodes
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Edges: outbound traversal
CREATE INDEX IF NOT EXISTS ix_edges_source
    ON edges(source_id);

-- Edges: inbound traversal
CREATE INDEX IF NOT EXISTS ix_edges_target
    ON edges(target_id);

-- Edges: filtered graph view
CREATE INDEX IF NOT EXISTS ix_edges_session_type
    ON edges(session_id, edge_type);

-- Nuggets: join to nodes (already unique from table definition)
CREATE INDEX IF NOT EXISTS ix_nuggets_node
    ON nuggets(node_id);

-- Nuggets: filter by status and score for prioritization
CREATE INDEX IF NOT EXISTS ix_nuggets_status_score
    ON nuggets(status, score DESC);

-- Provenance: join to nodes
CREATE INDEX IF NOT EXISTS ix_provenance_node
    ON provenance(node_id);

-- Documents: filter by session
CREATE INDEX IF NOT EXISTS ix_documents_session
    ON documents(session_id);
