"""Strict JSON schemas for LLM outputs with validation."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# --- Extraction Schemas ---


class NuggetType(str, Enum):
    idea = "idea"
    story = "story"
    framework = "framework"


class CandidateNugget(BaseModel):
    """A candidate nugget extracted from user input."""

    nugget_type: NuggetType = Field(
        ..., description="Type of nugget: idea, story, or framework"
    )
    title: str = Field(
        ...,
        min_length=5,
        max_length=100,
        description="Concise title capturing the core insight",
    )
    summary: str = Field(
        ...,
        min_length=20,
        max_length=500,
        description="2-3 sentence summary of the nugget",
    )
    key_phrases: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Key phrases from the original text",
    )
    confidence: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="Extraction confidence level",
    )

    @field_validator("title")
    @classmethod
    def title_not_generic(cls, v: str) -> str:
        """Reject generic titles."""
        generic_phrases = [
            "general advice",
            "key insight",
            "important point",
            "main idea",
            "lesson learned",
        ]
        lower_v = v.lower()
        for phrase in generic_phrases:
            if phrase in lower_v:
                raise ValueError(f"Title too generic: contains '{phrase}'")
        return v


class ExtractOutput(BaseModel):
    """Output schema for nugget extraction."""

    nuggets: list[CandidateNugget] = Field(
        default_factory=list,
        max_length=6,
        description="2-6 candidate nuggets extracted from input",
    )
    extraction_notes: str | None = Field(
        default=None,
        description="Optional notes about extraction quality or concerns",
    )


# --- Scoring Schemas ---


class NuggetDimensionScores(BaseModel):
    """Per-dimension scores for a nugget."""

    specificity: int = Field(
        ge=0, le=100, description="How specific vs generic is this insight?"
    )
    novelty: int = Field(
        ge=0, le=100, description="How fresh/unexpected is this perspective?"
    )
    authority: int = Field(
        ge=0, le=100, description="Does this come from real experience?"
    )
    actionability: int = Field(
        ge=0, le=100, description="Can someone act on this immediately?"
    )
    story_energy: int = Field(
        ge=0, le=100, description="Does this have narrative power?"
    )
    audience_resonance: int = Field(
        ge=0, le=100, description="Will the target audience care?"
    )

    @property
    def total_score(self) -> int:
        """Compute weighted total score."""
        # Weights emphasize specificity and authority (real experience matters)
        weights = {
            "specificity": 0.20,
            "novelty": 0.15,
            "authority": 0.20,
            "actionability": 0.15,
            "story_energy": 0.15,
            "audience_resonance": 0.15,
        }
        return int(
            self.specificity * weights["specificity"]
            + self.novelty * weights["novelty"]
            + self.authority * weights["authority"]
            + self.actionability * weights["actionability"]
            + self.story_energy * weights["story_energy"]
            + self.audience_resonance * weights["audience_resonance"]
        )


class MissingField(str, Enum):
    """Types of missing information that would strengthen a nugget."""

    example = "example"
    evidence = "evidence"
    steps = "steps"
    counterpoint = "counterpoint"
    definition = "definition"
    audience = "audience"
    outcome = "outcome"


class ScoredNugget(BaseModel):
    """A nugget with scoring information."""

    nugget_index: int = Field(
        ..., ge=0, description="Index of the nugget in the extraction output"
    )
    dimension_scores: NuggetDimensionScores
    missing_fields: list[MissingField] = Field(
        default_factory=list,
        max_length=3,
        description="Top 1-3 missing fields that would strengthen this nugget",
    )
    scoring_rationale: str | None = Field(
        default=None,
        max_length=200,
        description="Brief explanation of scoring decisions",
    )


class ScoreOutput(BaseModel):
    """Output schema for nugget scoring."""

    scored_nuggets: list[ScoredNugget] = Field(
        ..., description="Scored nuggets matching extraction output"
    )


# --- Deduplication Schemas ---


class DedupOutcome(str, Enum):
    """Possible deduplication outcomes."""

    create = "create"  # Create new node
    merge = "merge"  # Merge into existing node
    link_expands = "link_expands"  # Link as expands_on
    link_related = "link_related"  # Link as related_to


class DedupDecision(BaseModel):
    """Deduplication decision for a candidate nugget."""

    nugget_index: int = Field(..., ge=0, description="Index of the candidate nugget")
    outcome: DedupOutcome = Field(..., description="Deduplication outcome")
    existing_node_id: str | None = Field(
        default=None,
        description="UUID of existing node (for merge/link outcomes)",
    )
    merge_rationale: str | None = Field(
        default=None,
        max_length=200,
        description="Why this should be merged/linked (for non-create outcomes)",
    )
    similarity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Semantic similarity to closest existing node",
    )


class DedupOutput(BaseModel):
    """Output schema for deduplication decisions."""

    decisions: list[DedupDecision] = Field(
        ..., description="Dedup decision for each candidate nugget"
    )


# --- Next Question Schemas ---


class GapType(str, Enum):
    """Types of gaps that a question can address."""

    example = "example"
    evidence = "evidence"
    steps = "steps"
    counterpoint = "counterpoint"
    definition = "definition"
    audience = "audience"
    outcome = "outcome"


class NextQuestionCandidate(BaseModel):
    """A candidate next-best question."""

    question: str = Field(
        ...,
        min_length=10,
        max_length=200,
        description="The question to ask the user",
    )
    target_nugget_index: int = Field(
        ..., ge=0, description="Index of the nugget this question targets"
    )
    gap_type: GapType = Field(..., description="Type of gap this question addresses")
    impact_score: int = Field(
        ge=0, le=100, description="Potential impact of getting an answer"
    )
    leverage_score: int = Field(
        ge=0, le=100, description="How much will this unlock other insights?"
    )
    momentum_score: int = Field(
        ge=0, le=100, description="Does this feel like natural next step?"
    )
    connectivity_score: int = Field(
        ge=0, le=100, description="Will this connect to other nodes?"
    )
    gap_criticality_score: int = Field(
        ge=0, le=100, description="How critical is filling this gap?"
    )

    @property
    def total_score(self) -> int:
        """Compute weighted total score for question ranking."""
        return int(
            self.impact_score * 0.25
            + self.leverage_score * 0.20
            + self.momentum_score * 0.20
            + self.connectivity_score * 0.15
            + self.gap_criticality_score * 0.20
        )


class NextQuestionOutput(BaseModel):
    """Output schema for next question generation."""

    candidates: list[NextQuestionCandidate] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Candidate questions ranked by score",
    )
    why_primary: str = Field(
        ...,
        max_length=150,
        description="One sentence explaining why the top question is best",
    )
