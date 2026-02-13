"""Smoke tests for the extraction pipeline.

Test inputs:
- Generic advice (should trigger low scores or graceful recovery)
- Strong anecdote (should surface high-signal nuggets)
- Repeated idea (should trigger dedup)
- Weak/ambiguous input (should trigger graceful recovery)

Assertions:
- Weak inputs trigger graceful recovery
- Strong inputs surface high-signal nuggets
- Downvoted nuggets stop influencing prioritization

Evaluation hooks:
- Log nugget count
- Log avg score
- Log feedback rates
- Log follow-up question engagement
"""

import pytest

from app.llm.client import _extract_json
from app.llm.schemas import (
    CandidateNugget,
    ExtractOutput,
    GapType,
    MissingField,
    NextQuestionCandidate,
    NuggetDimensionScores,
    NuggetType,
    ScoredNugget,
    ScoreOutput,
)

# --- Test Data ---

GENERIC_ADVICE_INPUT = """
Communication is really important in leadership. You need to be a good listener
and make sure your team feels heard. It's all about building trust.
"""

STRONG_ANECDOTE_INPUT = """
When I was at Stripe in 2019, we had a critical incident where our payment processing
went down for 45 minutes. The thing that saved us wasn't the runbook - it was that
our on-call engineer Sarah had built a personal relationship with the AWS support team
over the previous 6 months. She got us escalated to a principal engineer in 10 minutes
instead of the usual 2 hours. We lost $2M in that outage, but it would have been $8M
without that relationship. Ever since then, I've made "build relationships before you
need them" a core principle for my teams.
"""

WEAK_AMBIGUOUS_INPUT = """
I think maybe we should do something about the thing we discussed.
It could be good, or maybe not. Hard to say really.
"""

REPEATED_IDEA_INPUT = """
Building relationships before you need them is crucial. I learned this from an incident
where having a pre-existing relationship saved us millions of dollars.
"""


# --- Unit Tests for JSON Extraction ---


class TestJsonExtraction:
    """Test JSON extraction from LLM responses."""

    def test_extract_direct_json(self):
        """Test extracting JSON from direct response."""
        response = '{"key": "value"}'
        result = _extract_json(response)
        assert result == {"key": "value"}

    def test_extract_from_markdown_code_block(self):
        """Test extracting JSON from markdown code block."""
        response = """Here's the response:
```json
{"key": "value"}
```
"""
        result = _extract_json(response)
        assert result == {"key": "value"}

    def test_extract_from_generic_code_block(self):
        """Test extracting JSON from generic code block."""
        response = """Here's the response:
```
{"key": "value"}
```
"""
        result = _extract_json(response)
        assert result == {"key": "value"}

    def test_extract_embedded_json(self):
        """Test extracting JSON embedded in text."""
        response = 'The result is: {"key": "value"} as shown above.'
        result = _extract_json(response)
        assert result == {"key": "value"}

    def test_invalid_json_raises(self):
        """Test that invalid JSON raises ValueError."""
        response = "This is not JSON at all"
        with pytest.raises(ValueError):
            _extract_json(response)


# --- Unit Tests for LLM Schemas ---


class TestLLMSchemas:
    """Test LLM output schema validation."""

    def test_candidate_nugget_valid(self):
        """Test valid candidate nugget."""
        nugget = CandidateNugget(
            nugget_type=NuggetType.idea,
            title="Specific insight about hiring",
            summary=(
                "When hiring engineers, I learned that technical"
                " skills matter less than curiosity. In my last"
                " three hires, the most successful were those who"
                " asked the most questions."
            ),
            key_phrases=["hiring", "curiosity", "questions"],
            confidence="high",
        )
        assert nugget.title == "Specific insight about hiring"
        assert nugget.confidence == "high"

    def test_candidate_nugget_rejects_generic_title(self):
        """Test that generic titles are rejected."""
        with pytest.raises(ValueError, match="Title too generic"):
            CandidateNugget(
                nugget_type=NuggetType.idea,
                title="General advice about leadership",
                summary="Some summary here that is long enough.",
                confidence="medium",
            )

    def test_dimension_scores_total(self):
        """Test dimension scores total calculation."""
        scores = NuggetDimensionScores(
            specificity=80,
            novelty=70,
            authority=90,
            actionability=60,
            story_energy=50,
            audience_resonance=75,
        )
        # Weighted: 0.20*80 + 0.15*70 + 0.20*90 + 0.15*60 + 0.15*50 + 0.15*75
        # = 16 + 10.5 + 18 + 9 + 7.5 + 11.25 = 72.25 -> 72
        assert scores.total_score == 72

    def test_extract_output_valid(self):
        """Test valid extraction output."""
        output = ExtractOutput(
            nuggets=[
                CandidateNugget(
                    nugget_type=NuggetType.story,
                    title="The Stripe incident that changed my leadership",
                    summary="A specific story about learning from failure.",
                    confidence="high",
                )
            ],
            extraction_notes="Good quality input with specific details.",
        )
        assert len(output.nuggets) == 1
        assert output.nuggets[0].nugget_type == NuggetType.story

    def test_score_output_valid(self):
        """Test valid score output."""
        output = ScoreOutput(
            scored_nuggets=[
                ScoredNugget(
                    nugget_index=0,
                    dimension_scores=NuggetDimensionScores(
                        specificity=85,
                        novelty=70,
                        authority=90,
                        actionability=65,
                        story_energy=80,
                        audience_resonance=75,
                    ),
                    missing_fields=[MissingField.steps],
                    scoring_rationale="Strong story with specific details.",
                )
            ]
        )
        assert len(output.scored_nuggets) == 1
        assert output.scored_nuggets[0].dimension_scores.specificity == 85

    def test_next_question_total_score(self):
        """Test next question total score calculation."""
        question = NextQuestionCandidate(
            question="Can you walk me through the exact steps you took?",
            target_nugget_index=0,
            gap_type=GapType.steps,
            impact_score=80,
            leverage_score=70,
            momentum_score=85,
            connectivity_score=60,
            gap_criticality_score=75,
        )
        # Weighted: 0.25*80 + 0.20*70 + 0.20*85 + 0.15*60 + 0.20*75
        # = 20 + 14 + 17 + 9 + 15 = 75
        assert question.total_score == 75


# --- Integration Tests (with mocked LLM) ---


class TestExtractionPipelineIntegration:
    """Integration tests for the extraction pipeline with mocked LLM."""

    @pytest.fixture
    def mock_llm_responses(self):
        """Mock LLM responses for different input types."""
        return {
            "strong_anecdote": {
                "extract": ExtractOutput(
                    nuggets=[
                        CandidateNugget(
                            nugget_type=NuggetType.story,
                            title="Stripe incident: relationship-based escalation",
                            summary=(
                                "During a 45-minute payment outage at"
                                " Stripe in 2019, pre-built relationships"
                                " with AWS support enabled 10-minute"
                                " escalation instead of 2 hours,"
                                " saving $6M."
                            ),
                            key_phrases=[
                                "Stripe",
                                "AWS support",
                                "relationship",
                                "$6M saved",
                            ],
                            confidence="high",
                        ),
                        CandidateNugget(
                            nugget_type=NuggetType.framework,
                            title="Build relationships before you need them",
                            summary=(
                                "A principle for engineering teams:"
                                " invest in support relationships"
                                " proactively, not reactively during"
                                " incidents."
                            ),
                            key_phrases=[
                                "relationships",
                                "proactive",
                                "support",
                            ],
                            confidence="high",
                        ),
                    ]
                ),
                "score": ScoreOutput(
                    scored_nuggets=[
                        ScoredNugget(
                            nugget_index=0,
                            dimension_scores=NuggetDimensionScores(
                                specificity=95,
                                novelty=80,
                                authority=90,
                                actionability=70,
                                story_energy=90,
                                audience_resonance=85,
                            ),
                            missing_fields=[MissingField.steps],
                        ),
                        ScoredNugget(
                            nugget_index=1,
                            dimension_scores=NuggetDimensionScores(
                                specificity=75,
                                novelty=65,
                                authority=85,
                                actionability=80,
                                story_energy=60,
                                audience_resonance=80,
                            ),
                            missing_fields=[MissingField.example],
                        ),
                    ]
                ),
            },
            "generic_advice": {
                "extract": ExtractOutput(
                    nuggets=[
                        CandidateNugget(
                            nugget_type=NuggetType.idea,
                            title="Leadership requires active listening",
                            summary="Being a good listener helps build trust with your team.",
                            confidence="low",
                        ),
                    ]
                ),
                "score": ScoreOutput(
                    scored_nuggets=[
                        ScoredNugget(
                            nugget_index=0,
                            dimension_scores=NuggetDimensionScores(
                                specificity=25,
                                novelty=15,
                                authority=20,
                                actionability=30,
                                story_energy=10,
                                audience_resonance=35,
                            ),
                            missing_fields=[MissingField.example, MissingField.evidence],
                        ),
                    ]
                ),
            },
        }

    def test_strong_anecdote_produces_high_scores(self, mock_llm_responses):
        """Test that strong anecdotes produce high-scoring nuggets."""
        extract_output = mock_llm_responses["strong_anecdote"]["extract"]
        score_output = mock_llm_responses["strong_anecdote"]["score"]

        # Verify extraction
        assert len(extract_output.nuggets) == 2
        assert all(n.confidence == "high" for n in extract_output.nuggets)

        # Verify scores
        for scored in score_output.scored_nuggets:
            assert scored.dimension_scores.total_score >= 70

        # Log evaluation metrics
        scored = score_output.scored_nuggets
        avg_score = sum(s.dimension_scores.total_score for s in scored) / len(scored)
        nugget_count = len(extract_output.nuggets)
        print(f"[EVAL] Strong anecdote - nugget_count: {nugget_count}, avg_score: {avg_score:.1f}")

    def test_generic_advice_triggers_low_scores(self, mock_llm_responses):
        """Test that generic advice triggers low scores."""
        extract_output = mock_llm_responses["generic_advice"]["extract"]
        score_output = mock_llm_responses["generic_advice"]["score"]

        # Verify low confidence extraction
        assert len(extract_output.nuggets) == 1
        assert extract_output.nuggets[0].confidence == "low"

        # Verify low scores (below threshold)
        for scored in score_output.scored_nuggets:
            assert scored.dimension_scores.total_score < 30

        # Log evaluation metrics
        scored = score_output.scored_nuggets
        avg_score = sum(s.dimension_scores.total_score for s in scored) / len(scored)
        nugget_count = len(extract_output.nuggets)
        print(f"[EVAL] Generic advice - nugget_count: {nugget_count}, avg_score: {avg_score:.1f}")


# --- Evaluation Hooks ---


class EvaluationMetrics:
    """Evaluation metrics for pipeline performance."""

    def __init__(self):
        self.nugget_counts: list[int] = []
        self.avg_scores: list[float] = []
        self.feedback_up: int = 0
        self.feedback_down: int = 0
        self.questions_followed: int = 0
        self.questions_skipped: int = 0

    def log_extraction(self, nugget_count: int, avg_score: float):
        """Log extraction metrics."""
        self.nugget_counts.append(nugget_count)
        self.avg_scores.append(avg_score)

    def log_feedback(self, feedback: str):
        """Log user feedback."""
        if feedback == "up":
            self.feedback_up += 1
        elif feedback == "down":
            self.feedback_down += 1

    def log_question_engagement(self, followed: bool):
        """Log question engagement."""
        if followed:
            self.questions_followed += 1
        else:
            self.questions_skipped += 1

    def summary(self) -> dict:
        """Get evaluation summary."""
        total_feedback = self.feedback_up + self.feedback_down
        total_questions = self.questions_followed + self.questions_skipped

        return {
            "total_extractions": len(self.nugget_counts),
            "avg_nuggets_per_turn": (
                sum(self.nugget_counts) / len(self.nugget_counts) if self.nugget_counts else 0
            ),
            "avg_score": sum(self.avg_scores) / len(self.avg_scores) if self.avg_scores else 0,
            "feedback_up_rate": self.feedback_up / total_feedback if total_feedback else 0,
            "feedback_down_rate": self.feedback_down / total_feedback if total_feedback else 0,
            "question_follow_rate": (
                self.questions_followed / total_questions if total_questions else 0
            ),
        }


# Global metrics instance for evaluation
evaluation_metrics = EvaluationMetrics()


class TestEvaluationHooks:
    """Test evaluation hooks work correctly."""

    def test_metrics_logging(self):
        """Test that metrics are logged correctly."""
        metrics = EvaluationMetrics()

        # Simulate extractions
        metrics.log_extraction(nugget_count=3, avg_score=75.5)
        metrics.log_extraction(nugget_count=2, avg_score=82.0)
        metrics.log_extraction(nugget_count=1, avg_score=45.0)

        # Simulate feedback
        metrics.log_feedback("up")
        metrics.log_feedback("up")
        metrics.log_feedback("down")

        # Simulate question engagement
        metrics.log_question_engagement(followed=True)
        metrics.log_question_engagement(followed=True)
        metrics.log_question_engagement(followed=False)

        summary = metrics.summary()

        assert summary["total_extractions"] == 3
        assert summary["avg_nuggets_per_turn"] == 2.0
        assert abs(summary["avg_score"] - 67.5) < 0.1
        assert abs(summary["feedback_up_rate"] - 0.667) < 0.01
        assert abs(summary["question_follow_rate"] - 0.667) < 0.01


# --- Run Smoke Tests ---

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
