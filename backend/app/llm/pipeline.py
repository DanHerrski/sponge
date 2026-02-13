"""Extraction pipeline: extract -> score -> dedup -> persist -> questions."""

import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.llm.client import ValidationRetryExhausted, call_llm_with_schema
from app.llm.schemas import (
    CandidateNugget,
    DedupDecision,
    DedupOutcome,
    ExtractOutput,
    NextQuestionCandidate,
    NextQuestionOutput,
    ScoreOutput,
    ScoredNugget,
)
from app.models.tables import (
    ChatTurn,
    Edge,
    EdgeType,
    Node,
    NodeType,
    Nugget,
    NuggetType,
    Provenance,
    Session,
    SourceType,
    ConfidenceLevel,
    UserFeedback,
)

logger = logging.getLogger(__name__)

# Configuration
MIN_SCORE_THRESHOLD = 30
SIMILARITY_THRESHOLD = 0.85
MAX_GRAPH_NODES = 20


@dataclass
class PipelineResult:
    """Result of the extraction pipeline."""

    extracted_nuggets: list[CandidateNugget] = field(default_factory=list)
    scored_nuggets: list[ScoredNugget] = field(default_factory=list)
    dedup_decisions: list[DedupDecision] = field(default_factory=list)
    created_nodes: list[Node] = field(default_factory=list)
    created_edges: list[Edge] = field(default_factory=list)
    created_nuggets: list[Nugget] = field(default_factory=list)
    questions: list[NextQuestionCandidate] = field(default_factory=list)
    why_primary: str = ""
    extraction_failed: bool = False
    failure_reason: str = ""


@dataclass
class ExistingNodeContext:
    """Context about an existing node for dedup decisions."""

    node_id: str
    title: str
    summary: str
    user_edited: bool = False
    embedding: list[float] | None = None


class ExtractionPipeline:
    """Orchestrates the full extraction pipeline."""

    def __init__(self, db: AsyncSession, session_id: uuid.UUID):
        self.db = db
        self.session_id = session_id

    async def run(
        self,
        user_message: str,
        chat_turn_id: uuid.UUID,
    ) -> PipelineResult:
        """
        Run the full extraction pipeline.

        Steps:
        1. Extract candidate nuggets from user message
        2. Score nuggets with dimension breakdowns
        3. Deduplicate against existing nodes
        4. Persist new nodes, edges, nuggets, and provenance
        5. Generate next-best questions

        Returns:
            PipelineResult with all outputs
        """
        result = PipelineResult()

        # Get session context
        session_context = await self._get_session_context()
        downvoted_context = await self._get_downvoted_context()
        existing_nodes = await self._get_existing_nodes()

        # Step 1: Extract nuggets
        try:
            extract_output = await self._extract_nuggets(
                user_message, session_context
            )
            result.extracted_nuggets = extract_output.nuggets
        except ValidationRetryExhausted as e:
            logger.error(f"Extraction failed: {e}")
            result.extraction_failed = True
            result.failure_reason = "I couldn't identify any distinct ideas from what you shared."
            return result

        # Check for extraction failure (no nuggets)
        if not result.extracted_nuggets:
            result.extraction_failed = True
            result.failure_reason = "I couldn't identify any distinct ideas from what you shared."
            return result

        # Filter low-confidence nuggets if we have alternatives
        high_confidence = [
            n for n in result.extracted_nuggets if n.confidence != "low"
        ]
        if high_confidence:
            result.extracted_nuggets = high_confidence

        # Step 2: Score nuggets
        try:
            score_output = await self._score_nuggets(
                result.extracted_nuggets,
                session_context,
                downvoted_context,
            )
            result.scored_nuggets = score_output.scored_nuggets
        except ValidationRetryExhausted as e:
            logger.error(f"Scoring failed: {e}")
            # Use default scores on failure
            result.scored_nuggets = self._default_scores(result.extracted_nuggets)

        # Check if all nuggets are below threshold
        valid_nuggets = [
            s for s in result.scored_nuggets
            if s.dimension_scores.total_score >= MIN_SCORE_THRESHOLD
        ]
        if not valid_nuggets:
            result.extraction_failed = True
            result.failure_reason = "The ideas I captured seem too vague or general to be useful."
            return result

        # Step 3: Deduplicate
        try:
            dedup_output = await self._deduplicate(
                result.extracted_nuggets,
                result.scored_nuggets,
                existing_nodes,
            )
            result.dedup_decisions = dedup_output
        except ValidationRetryExhausted as e:
            logger.error(f"Dedup failed: {e}")
            # Default to create all
            result.dedup_decisions = [
                DedupDecision(
                    nugget_index=i,
                    outcome=DedupOutcome.create,
                    similarity_score=0.0,
                )
                for i in range(len(result.extracted_nuggets))
            ]

        # Step 4: Persist to graph
        await self._persist_graph(
            result.extracted_nuggets,
            result.scored_nuggets,
            result.dedup_decisions,
            chat_turn_id,
            result,
        )

        # Step 5: Generate questions
        try:
            questions_output = await self._generate_questions(
                result.extracted_nuggets,
                result.scored_nuggets,
                result.created_nuggets,
                downvoted_context,
            )
            result.questions = questions_output.candidates
            result.why_primary = questions_output.why_primary
        except ValidationRetryExhausted as e:
            logger.error(f"Question generation failed: {e}")
            # Use default question
            result.questions = self._default_questions(result.extracted_nuggets)
            result.why_primary = "Let's explore this further with a concrete example."

        return result

    async def _get_session_context(self) -> str:
        """Get context from session onboarding data + existing high-value nuggets."""
        context_parts: list[str] = []

        # Include onboarding context (project name, topic, audience)
        session_result = await self.db.execute(
            select(Session).where(Session.id == self.session_id)
        )
        session = session_result.scalar_one_or_none()
        if session:
            if session.project_name and session.project_name != "Untitled":
                context_parts.append(f"Project: {session.project_name}")
            if session.topic:
                context_parts.append(f"Topic: {session.topic}")
            if session.audience:
                context_parts.append(f"Target audience: {session.audience}")

        # Include existing high-value nuggets
        stmt = (
            select(Nugget)
            .join(Node)
            .where(Node.session_id == self.session_id)
            .where(Nugget.score >= 60)
            .where(Nugget.user_feedback != UserFeedback.down)
            .order_by(Nugget.score.desc())
            .limit(5)
        )
        result = await self.db.execute(stmt)
        nuggets = result.scalars().all()

        if nuggets:
            context_parts.append("Previous high-value nuggets:")
            for n in nuggets:
                context_parts.append(f"- {n.title}: {n.short_summary}")

        return "\n".join(context_parts) if context_parts else "No previous context."

    async def _get_downvoted_context(self) -> str:
        """Get context about downvoted nuggets to avoid similar extractions."""
        stmt = (
            select(Nugget)
            .join(Node)
            .where(Node.session_id == self.session_id)
            .where(Nugget.user_feedback == UserFeedback.down)
            .limit(10)
        )
        result = await self.db.execute(stmt)
        nuggets = result.scalars().all()

        if not nuggets:
            return "No downvoted nuggets."

        context_parts = []
        for n in nuggets:
            context_parts.append(f"- {n.title}")
        return "\n".join(context_parts)

    async def _get_existing_nodes(self) -> list[ExistingNodeContext]:
        """Get existing nodes for deduplication."""
        stmt = (
            select(Node)
            .where(Node.session_id == self.session_id)
            .options(selectinload(Node.provenance_records))
            .limit(50)
        )
        result = await self.db.execute(stmt)
        nodes = result.scalars().all()

        return [
            ExistingNodeContext(
                node_id=str(n.id),
                title=n.title,
                summary=n.summary,
                user_edited=any(
                    p.source_type == SourceType.chat for p in n.provenance_records
                ),  # Simplified - would track user edits separately
            )
            for n in nodes
        ]

    async def _extract_nuggets(
        self,
        user_message: str,
        session_context: str,
    ) -> ExtractOutput:
        """Extract candidate nuggets from user message."""
        return await call_llm_with_schema(
            prompt_name="extract_nuggets_v1",
            schema_class=ExtractOutput,
            prompt_vars={
                "user_message": user_message,
                "session_context": session_context,
            },
        )

    async def _score_nuggets(
        self,
        nuggets: list[CandidateNugget],
        session_context: str,
        downvoted_context: str,
    ) -> ScoreOutput:
        """Score extracted nuggets."""
        nuggets_json = json.dumps(
            [n.model_dump() for n in nuggets], indent=2
        )
        return await call_llm_with_schema(
            prompt_name="score_nuggets_v1",
            schema_class=ScoreOutput,
            prompt_vars={
                "nuggets_json": nuggets_json,
                "session_context": session_context,
                "downvoted_context": downvoted_context,
            },
        )

    async def _deduplicate(
        self,
        nuggets: list[CandidateNugget],
        scores: list[ScoredNugget],
        existing_nodes: list[ExistingNodeContext],
    ) -> list[DedupDecision]:
        """
        Deduplicate nuggets against existing nodes.

        For now, uses simple title/summary comparison.
        TODO: Add embedding-based similarity when embeddings are available.
        """
        if not existing_nodes:
            # No existing nodes - create all
            return [
                DedupDecision(
                    nugget_index=i,
                    outcome=DedupOutcome.create,
                    similarity_score=0.0,
                )
                for i in range(len(nuggets))
            ]

        # Compute simple similarity (title overlap)
        decisions = []
        for i, nugget in enumerate(nuggets):
            best_match = None
            best_similarity = 0.0

            nugget_words = set(nugget.title.lower().split())

            for node in existing_nodes:
                node_words = set(node.title.lower().split())
                if not nugget_words or not node_words:
                    continue

                # Jaccard similarity
                intersection = len(nugget_words & node_words)
                union = len(nugget_words | node_words)
                similarity = intersection / union if union > 0 else 0.0

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = node

            # Decide based on similarity
            if best_similarity >= SIMILARITY_THRESHOLD:
                outcome = DedupOutcome.merge
            elif best_similarity >= 0.5:
                outcome = DedupOutcome.link_expands
            elif best_similarity >= 0.3:
                outcome = DedupOutcome.link_related
            else:
                outcome = DedupOutcome.create

            decisions.append(
                DedupDecision(
                    nugget_index=i,
                    outcome=outcome,
                    existing_node_id=best_match.node_id if best_match and outcome != DedupOutcome.create else None,
                    merge_rationale=f"Similar to: {best_match.title}" if best_match and outcome != DedupOutcome.create else None,
                    similarity_score=best_similarity,
                )
            )

        return decisions

    async def _persist_graph(
        self,
        nuggets: list[CandidateNugget],
        scores: list[ScoredNugget],
        dedup_decisions: list[DedupDecision],
        chat_turn_id: uuid.UUID,
        result: PipelineResult,
    ) -> None:
        """Persist nodes, edges, nuggets, and provenance to database."""
        node_id_map: dict[int, uuid.UUID] = {}  # nugget_index -> node_id

        for i, (nugget, decision) in enumerate(zip(nuggets, dedup_decisions)):
            # Find corresponding score
            score_data = next(
                (s for s in scores if s.nugget_index == i),
                None,
            )

            if decision.outcome == DedupOutcome.create:
                # Create new node
                node = Node(
                    session_id=self.session_id,
                    node_type=NodeType(nugget.nugget_type.value),
                    title=nugget.title,
                    summary=nugget.summary,
                )
                self.db.add(node)
                await self.db.flush()
                node_id_map[i] = node.id
                result.created_nodes.append(node)

                # Create nugget record
                nugget_record = Nugget(
                    node_id=node.id,
                    nugget_type=NuggetType(nugget.nugget_type.value),
                    title=nugget.title,
                    short_summary=nugget.summary[:200],
                    score=score_data.dimension_scores.total_score if score_data else 50,
                    dimension_scores=score_data.dimension_scores.model_dump() if score_data else None,
                    missing_fields=[f.value for f in score_data.missing_fields] if score_data else [],
                    next_questions=[],
                )
                self.db.add(nugget_record)
                result.created_nuggets.append(nugget_record)

                # Create provenance
                provenance = Provenance(
                    node_id=node.id,
                    source_type=SourceType.chat,
                    source_id=chat_turn_id,
                    confidence=ConfidenceLevel(nugget.confidence),
                )
                self.db.add(provenance)

            elif decision.outcome == DedupOutcome.merge:
                # Merge into existing node - just link provenance
                if decision.existing_node_id:
                    existing_id = uuid.UUID(decision.existing_node_id)
                    node_id_map[i] = existing_id

                    # Add provenance linking new source
                    provenance = Provenance(
                        node_id=existing_id,
                        source_type=SourceType.chat,
                        source_id=chat_turn_id,
                        confidence=ConfidenceLevel(nugget.confidence),
                    )
                    self.db.add(provenance)

            elif decision.outcome in (DedupOutcome.link_expands, DedupOutcome.link_related):
                # Create new node and link to existing
                node = Node(
                    session_id=self.session_id,
                    node_type=NodeType(nugget.nugget_type.value),
                    title=nugget.title,
                    summary=nugget.summary,
                )
                self.db.add(node)
                await self.db.flush()
                node_id_map[i] = node.id
                result.created_nodes.append(node)

                # Create nugget record
                nugget_record = Nugget(
                    node_id=node.id,
                    nugget_type=NuggetType(nugget.nugget_type.value),
                    title=nugget.title,
                    short_summary=nugget.summary[:200],
                    score=score_data.dimension_scores.total_score if score_data else 50,
                    dimension_scores=score_data.dimension_scores.model_dump() if score_data else None,
                    missing_fields=[f.value for f in score_data.missing_fields] if score_data else [],
                    next_questions=[],
                )
                self.db.add(nugget_record)
                result.created_nuggets.append(nugget_record)

                # Create provenance
                provenance = Provenance(
                    node_id=node.id,
                    source_type=SourceType.chat,
                    source_id=chat_turn_id,
                    confidence=ConfidenceLevel(nugget.confidence),
                )
                self.db.add(provenance)

                # Create edge to existing node
                if decision.existing_node_id:
                    edge_type = (
                        EdgeType.expands_on
                        if decision.outcome == DedupOutcome.link_expands
                        else EdgeType.related_to
                    )
                    edge = Edge(
                        session_id=self.session_id,
                        source_id=node.id,
                        target_id=uuid.UUID(decision.existing_node_id),
                        edge_type=edge_type,
                    )
                    self.db.add(edge)
                    result.created_edges.append(edge)

        # Create edges between co-extracted nodes (related_to)
        created_node_ids = list(node_id_map.values())
        for i, id1 in enumerate(created_node_ids):
            for id2 in created_node_ids[i + 1 :]:
                if id1 != id2:
                    edge = Edge(
                        session_id=self.session_id,
                        source_id=id1,
                        target_id=id2,
                        edge_type=EdgeType.related_to,
                    )
                    self.db.add(edge)
                    result.created_edges.append(edge)

        await self.db.flush()

    async def _generate_questions(
        self,
        nuggets: list[CandidateNugget],
        scores: list[ScoredNugget],
        created_nuggets: list[Nugget],
        downvoted_context: str,
    ) -> NextQuestionOutput:
        """Generate next-best questions for the nuggets."""
        # Build nuggets JSON with scores
        nuggets_data = []
        for i, nugget in enumerate(nuggets):
            score_data = next(
                (s for s in scores if s.nugget_index == i),
                None,
            )
            nuggets_data.append(
                {
                    "index": i,
                    "title": nugget.title,
                    "summary": nugget.summary,
                    "type": nugget.nugget_type.value,
                    "score": score_data.dimension_scores.total_score if score_data else 50,
                    "missing_fields": [f.value for f in score_data.missing_fields] if score_data else [],
                }
            )

        return await call_llm_with_schema(
            prompt_name="next_questions_v1",
            schema_class=NextQuestionOutput,
            prompt_vars={
                "nuggets_json": json.dumps(nuggets_data, indent=2),
                "graph_context": "Session graph context",  # TODO: Add real context
                "excluded_ids": downvoted_context,
            },
        )

    def _default_scores(
        self, nuggets: list[CandidateNugget]
    ) -> list[ScoredNugget]:
        """Generate default scores when LLM scoring fails."""
        from app.llm.schemas import MissingField, NuggetDimensionScores

        return [
            ScoredNugget(
                nugget_index=i,
                dimension_scores=NuggetDimensionScores(
                    specificity=50,
                    novelty=50,
                    authority=50,
                    actionability=50,
                    story_energy=50,
                    audience_resonance=50,
                ),
                missing_fields=[MissingField.example],
            )
            for i in range(len(nuggets))
        ]

    def _default_questions(
        self, nuggets: list[CandidateNugget]
    ) -> list[NextQuestionCandidate]:
        """Generate default questions when LLM question generation fails."""
        from app.llm.schemas import GapType

        if not nuggets:
            return []

        return [
            NextQuestionCandidate(
                question=f"Can you give me a specific example of '{nuggets[0].title}'?",
                target_nugget_index=0,
                gap_type=GapType.example,
                impact_score=70,
                leverage_score=65,
                momentum_score=75,
                connectivity_score=55,
                gap_criticality_score=70,
            )
        ]


async def get_graph_subset(
    db: AsyncSession,
    session_id: uuid.UUID,
    max_nodes: int = MAX_GRAPH_NODES,
) -> tuple[list[Node], list[Edge]]:
    """
    Get a subset of the graph most relevant for UI display.

    Returns up to max_nodes nodes, prioritizing:
    1. Recently created nodes
    2. High-scoring nodes
    3. Nodes not downvoted

    And all edges between the returned nodes.
    """
    # Get nodes prioritized by score and recency
    node_stmt = (
        select(Node)
        .where(Node.session_id == session_id)
        .outerjoin(Nugget)
        .where((Nugget.user_feedback != UserFeedback.down) | (Nugget.user_feedback.is_(None)))
        .order_by(Nugget.score.desc().nulls_last(), Node.created_at.desc())
        .limit(max_nodes)
        .options(selectinload(Node.nugget))
    )
    node_result = await db.execute(node_stmt)
    nodes = list(node_result.scalars().all())

    if not nodes:
        return [], []

    # Get edges between these nodes
    node_ids = [n.id for n in nodes]
    edge_stmt = (
        select(Edge)
        .where(Edge.session_id == session_id)
        .where(Edge.source_id.in_(node_ids))
        .where(Edge.target_id.in_(node_ids))
    )
    edge_result = await db.execute(edge_stmt)
    edges = list(edge_result.scalars().all())

    return nodes, edges
