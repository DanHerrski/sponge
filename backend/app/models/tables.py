import enum
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    VARCHAR,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# --- Enum types ---


class NodeType(str, enum.Enum):
    idea = "idea"
    story = "story"
    framework = "framework"
    definition = "definition"
    evidence = "evidence"
    theme = "theme"


class EdgeType(str, enum.Enum):
    supports = "supports"
    example_of = "example_of"
    expands_on = "expands_on"
    related_to = "related_to"
    contradicts = "contradicts"


class NuggetType(str, enum.Enum):
    idea = "idea"
    story = "story"
    framework = "framework"


class NuggetStatus(str, enum.Enum):
    new = "new"
    explored = "explored"
    parked = "parked"


class UserFeedback(str, enum.Enum):
    up = "up"
    down = "down"


class ChatRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class SourceType(str, enum.Enum):
    chat = "chat"
    upload = "upload"


class ConfidenceLevel(str, enum.Enum):
    low = "low"
    med = "med"
    high = "high"


# --- Tables ---


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_name: Mapped[str | None] = mapped_column(VARCHAR(255))
    topic: Mapped[str | None] = mapped_column(Text)
    audience: Mapped[str | None] = mapped_column(VARCHAR(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    chat_turns: Mapped[list["ChatTurn"]] = relationship(back_populates="session")
    nodes: Mapped[list["Node"]] = relationship(back_populates="session")
    edges: Mapped[list["Edge"]] = relationship(back_populates="session")
    documents: Mapped[list["Document"]] = relationship(back_populates="session")


class ChatTurn(Base):
    __tablename__ = "chat_turns"
    __table_args__ = (Index("ix_chat_turns_session_turn", "session_id", "turn_number"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[ChatRole] = mapped_column(
        Enum(ChatRole, name="chat_role", create_constraint=True), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["Session"] = relationship(back_populates="chat_turns")


class Node(Base):
    __tablename__ = "nodes"
    __table_args__ = (Index("ix_nodes_session", "session_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    node_type: Mapped[NodeType] = mapped_column(
        Enum(NodeType, name="node_type", create_constraint=True), nullable=False
    )
    title: Mapped[str] = mapped_column(VARCHAR(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(1536), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["Session"] = relationship(back_populates="nodes")
    nugget: Mapped["Nugget | None"] = relationship(back_populates="node", uselist=False)
    provenance_records: Mapped[list["Provenance"]] = relationship(back_populates="node")
    outbound_edges: Mapped[list["Edge"]] = relationship(
        back_populates="source_node", foreign_keys="Edge.source_id"
    )
    inbound_edges: Mapped[list["Edge"]] = relationship(
        back_populates="target_node", foreign_keys="Edge.target_id"
    )


class Edge(Base):
    __tablename__ = "edges"
    __table_args__ = (
        Index("ix_edges_source", "source_id"),
        Index("ix_edges_target", "target_id"),
        Index("ix_edges_session_type", "session_id", "edge_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False
    )
    edge_type: Mapped[EdgeType] = mapped_column(
        Enum(EdgeType, name="edge_type", create_constraint=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["Session"] = relationship(back_populates="edges")
    source_node: Mapped["Node"] = relationship(
        back_populates="outbound_edges", foreign_keys=[source_id]
    )
    target_node: Mapped["Node"] = relationship(
        back_populates="inbound_edges", foreign_keys=[target_id]
    )


class Nugget(Base):
    __tablename__ = "nuggets"
    __table_args__ = (Index("ix_nuggets_node", "node_id", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    nugget_type: Mapped[NuggetType] = mapped_column(
        Enum(NuggetType, name="nugget_type", create_constraint=True), nullable=False
    )
    title: Mapped[str] = mapped_column(VARCHAR(500), nullable=False)
    short_summary: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dimension_scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    missing_fields: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    next_questions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[NuggetStatus] = mapped_column(
        Enum(NuggetStatus, name="nugget_status", create_constraint=True),
        nullable=False,
        default=NuggetStatus.new,
        server_default="new",
    )
    user_feedback: Mapped[UserFeedback | None] = mapped_column(
        Enum(UserFeedback, name="user_feedback", create_constraint=True),
        nullable=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    node: Mapped["Node"] = relationship(back_populates="nugget")


class Provenance(Base):
    __tablename__ = "provenance"
    __table_args__ = (Index("ix_provenance_node", "node_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False
    )
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="source_type", create_constraint=True), nullable=False
    )
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    confidence: Mapped[ConfidenceLevel] = mapped_column(
        Enum(ConfidenceLevel, name="confidence_level", create_constraint=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    node: Mapped["Node"] = relationship(back_populates="provenance_records")


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (Index("ix_documents_session", "session_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(VARCHAR(500), nullable=False)
    content_type: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["Session"] = relationship(back_populates="documents")
