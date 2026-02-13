"""LLM integration module for Sponge knowledge extraction pipeline."""

from app.llm.pipeline import ExtractionPipeline
from app.llm.schemas import (
    CandidateNugget,
    DedupDecision,
    DedupOutcome,
    ExtractOutput,
    NextQuestionCandidate,
    NextQuestionOutput,
    NuggetDimensionScores,
    ScoredNugget,
    ScoreOutput,
)

__all__ = [
    "CandidateNugget",
    "DedupDecision",
    "DedupOutcome",
    "ExtractOutput",
    "ExtractionPipeline",
    "NextQuestionCandidate",
    "NextQuestionOutput",
    "NuggetDimensionScores",
    "ScoreOutput",
    "ScoredNugget",
]
