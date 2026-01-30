-- Sponge P0 Schema: Enum Types
-- Migration: 20240130000001_create_enums
-- Idempotent: Safe to re-run

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

-- Node types for knowledge graph
DO $$ BEGIN
    CREATE TYPE node_type AS ENUM (
        'idea',
        'story',
        'framework',
        'definition',
        'evidence',
        'theme'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Edge types for relationships between nodes
DO $$ BEGIN
    CREATE TYPE edge_type AS ENUM (
        'supports',
        'example_of',
        'expands_on',
        'related_to',
        'contradicts'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Nugget types (subset of node types for prioritization)
DO $$ BEGIN
    CREATE TYPE nugget_type AS ENUM (
        'idea',
        'story',
        'framework'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Nugget status for workflow tracking
DO $$ BEGIN
    CREATE TYPE nugget_status AS ENUM (
        'new',
        'explored',
        'parked'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- User feedback on nuggets
DO $$ BEGIN
    CREATE TYPE user_feedback AS ENUM (
        'up',
        'down'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Chat message roles
DO $$ BEGIN
    CREATE TYPE chat_role AS ENUM (
        'user',
        'assistant'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Provenance source types
DO $$ BEGIN
    CREATE TYPE source_type AS ENUM (
        'chat',
        'upload'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Extraction confidence levels
DO $$ BEGIN
    CREATE TYPE confidence_level AS ENUM (
        'low',
        'med',
        'high'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;
