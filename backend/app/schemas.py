"""Pydantic request/response schemas matching steel-thread.md API contracts."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

# --- Enums reused from models (as string literals for API serialization) ---


# --- Chat Turn ---


class ChatTurnRequest(BaseModel):
    session_id: uuid.UUID | None = Field(
        default=None,
        description="Session ID. If omitted, a new session is created.",
    )
    message: str = Field(..., min_length=1, description="User's brain-dump text")


class CapturedNugget(BaseModel):
    nugget_id: uuid.UUID
    node_id: uuid.UUID
    title: str
    nugget_type: str  # "Idea" | "Story" | "Framework"
    score: int = Field(ge=0, le=100)
    is_new: bool


class NextQuestion(BaseModel):
    question: str
    target_nugget_id: uuid.UUID
    gap_type: str  # "example" | "evidence" | "steps" | etc.
    why_this_next: str


class AlternatePath(BaseModel):
    question: str
    target_nugget_id: uuid.UUID
    gap_type: str


class ChatTurnResponse(BaseModel):
    turn_id: uuid.UUID
    session_id: uuid.UUID
    captured_nuggets: list[CapturedNugget]
    graph_update_summary: str
    next_question: NextQuestion | None = None
    alternate_paths: list[AlternatePath] = Field(default_factory=list)


# --- Graph View ---


class GraphNode(BaseModel):
    node_id: uuid.UUID
    node_type: str
    title: str
    summary: str
    score: int | None = None


class GraphEdge(BaseModel):
    edge_id: uuid.UUID
    source_id: uuid.UUID
    target_id: uuid.UUID
    edge_type: str


class GraphViewResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


# --- Node Detail ---


class ProvenanceRecord(BaseModel):
    source_type: str
    source_id: uuid.UUID
    timestamp: datetime
    confidence: str


class DimensionScores(BaseModel):
    specificity: int = Field(ge=0, le=100)
    novelty: int = Field(ge=0, le=100)
    authority: int = Field(ge=0, le=100)
    actionability: int = Field(ge=0, le=100)
    story_energy: int = Field(ge=0, le=100)
    audience_resonance: int = Field(ge=0, le=100)


class NuggetDetail(BaseModel):
    nugget_id: uuid.UUID
    score: int = Field(ge=0, le=100)
    dimension_scores: DimensionScores | None = None
    missing_fields: list[str] = Field(default_factory=list)
    next_questions: list[str] = Field(default_factory=list)


class NodeDetailResponse(BaseModel):
    node_id: uuid.UUID
    node_type: str
    title: str
    summary: str
    provenance: list[ProvenanceRecord]
    nugget: NuggetDetail | None = None


# --- Upload ---


class UploadResponse(BaseModel):
    document_id: uuid.UUID
    filename: str
    size_bytes: int
    message: str
