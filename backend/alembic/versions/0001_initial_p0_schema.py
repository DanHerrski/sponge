"""Initial P0 schema: sessions, chat_turns, nodes, edges, nuggets, provenance, documents

Revision ID: 0001
Revises: None
Create Date: 2026-01-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Reusable defaults
_uuid_pk = sa.text("gen_random_uuid()")
_now = sa.func.now()


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Enum types
    chat_role = sa.Enum("user", "assistant", name="chat_role", create_type=True)
    node_type = sa.Enum(
        "idea",
        "story",
        "framework",
        "definition",
        "evidence",
        "theme",
        name="node_type",
        create_type=True,
    )
    edge_type = sa.Enum(
        "supports",
        "example_of",
        "expands_on",
        "related_to",
        "contradicts",
        name="edge_type",
        create_type=True,
    )
    nugget_type = sa.Enum(
        "idea",
        "story",
        "framework",
        name="nugget_type",
        create_type=True,
    )
    nugget_status = sa.Enum(
        "new",
        "explored",
        "parked",
        name="nugget_status",
        create_type=True,
    )
    source_type = sa.Enum(
        "chat",
        "upload",
        name="source_type",
        create_type=True,
    )
    confidence_level = sa.Enum(
        "low",
        "med",
        "high",
        name="confidence_level",
        create_type=True,
    )

    # --- sessions ---
    op.create_table(
        "sessions",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=_uuid_pk,
        ),
        sa.Column("project_name", sa.VARCHAR(255), nullable=True),
        sa.Column("topic", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=_now,
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=_now,
            nullable=False,
        ),
    )

    # --- chat_turns ---
    op.create_table(
        "chat_turns",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=_uuid_pk,
        ),
        sa.Column(
            "session_id",
            UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("turn_number", sa.Integer, nullable=False),
        sa.Column("role", chat_role, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=_now,
            nullable=False,
        ),
    )
    op.create_index(
        "ix_chat_turns_session_turn",
        "chat_turns",
        ["session_id", "turn_number"],
    )

    # --- nodes ---
    op.create_table(
        "nodes",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=_uuid_pk,
        ),
        sa.Column(
            "session_id",
            UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("node_type", node_type, nullable=False),
        sa.Column("title", sa.VARCHAR(500), nullable=False),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=_now,
            nullable=False,
        ),
    )
    op.create_index("ix_nodes_session", "nodes", ["session_id"])

    # Add vector column (pgvector)
    op.execute("ALTER TABLE nodes ADD COLUMN embedding vector(1536)")

    # HNSW index for vector similarity search
    op.execute(
        "CREATE INDEX ix_nodes_embedding_hnsw ON nodes "
        "USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )

    # --- edges ---
    op.create_table(
        "edges",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=_uuid_pk,
        ),
        sa.Column(
            "session_id",
            UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_id",
            UUID(as_uuid=True),
            sa.ForeignKey("nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_id",
            UUID(as_uuid=True),
            sa.ForeignKey("nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("edge_type", edge_type, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=_now,
            nullable=False,
        ),
    )
    op.create_index("ix_edges_source", "edges", ["source_id"])
    op.create_index("ix_edges_target", "edges", ["target_id"])
    op.create_index(
        "ix_edges_session_type",
        "edges",
        ["session_id", "edge_type"],
    )

    # --- nuggets ---
    op.create_table(
        "nuggets",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=_uuid_pk,
        ),
        sa.Column(
            "node_id",
            UUID(as_uuid=True),
            sa.ForeignKey("nodes.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("nugget_type", nugget_type, nullable=False),
        sa.Column("title", sa.VARCHAR(500), nullable=False),
        sa.Column("short_summary", sa.Text, nullable=False),
        sa.Column(
            "score",
            sa.Integer,
            nullable=False,
            server_default="0",
        ),
        sa.Column("dimension_scores", JSONB, nullable=True),
        sa.Column("missing_fields", JSONB, nullable=True),
        sa.Column("next_questions", JSONB, nullable=True),
        sa.Column(
            "status",
            nugget_status,
            nullable=False,
            server_default="new",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=_now,
            nullable=False,
        ),
    )
    op.create_index(
        "ix_nuggets_node",
        "nuggets",
        ["node_id"],
        unique=True,
    )

    # --- provenance ---
    op.create_table(
        "provenance",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=_uuid_pk,
        ),
        sa.Column(
            "node_id",
            UUID(as_uuid=True),
            sa.ForeignKey("nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_type", source_type, nullable=False),
        sa.Column("source_id", UUID(as_uuid=True), nullable=False),
        sa.Column("confidence", confidence_level, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=_now,
            nullable=False,
        ),
    )
    op.create_index("ix_provenance_node", "provenance", ["node_id"])

    # --- documents ---
    op.create_table(
        "documents",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=_uuid_pk,
        ),
        sa.Column(
            "session_id",
            UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.VARCHAR(500), nullable=False),
        sa.Column("content_type", sa.VARCHAR(100), nullable=False),
        sa.Column("storage_path", sa.Text, nullable=False),
        sa.Column("size_bytes", sa.Integer, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=_now,
            nullable=False,
        ),
    )
    op.create_index("ix_documents_session", "documents", ["session_id"])


def downgrade() -> None:
    op.drop_table("documents")
    op.drop_table("provenance")
    op.drop_table("nuggets")
    op.drop_table("edges")
    op.execute("DROP INDEX IF EXISTS ix_nodes_embedding_hnsw")
    op.drop_table("nodes")
    op.drop_table("chat_turns")
    op.drop_table("sessions")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS confidence_level")
    op.execute("DROP TYPE IF EXISTS source_type")
    op.execute("DROP TYPE IF EXISTS nugget_status")
    op.execute("DROP TYPE IF EXISTS nugget_type")
    op.execute("DROP TYPE IF EXISTS edge_type")
    op.execute("DROP TYPE IF EXISTS node_type")
    op.execute("DROP TYPE IF EXISTS chat_role")

    op.execute("DROP EXTENSION IF EXISTS vector")
