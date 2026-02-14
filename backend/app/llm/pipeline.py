"""Extraction pipeline: extract -> score -> dedup -> persist -> questions."""

import json
import logging
import time
import uuid
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.llm.client import ValidationRetryExhaustedError, call_llm_with_schema
from app.llm.schemas import (
    CandidateNugget,
    DedupDecision,
    DedupOutcome,
    ExtractOutput,
    NextQuestionCandidate,
    NextQuestionOutput,
    ScoredNugget,
    ScoreOutput,
)
from app.models.tables import (
    ConfidenceLevel,
    Edge,
    EdgeType,
    Node,
    NodeType,
    Nugget,
    NuggetType,
    Provenance,
    Session,
    SourceType,
    UserFeedback,
)

logger = logging.getLogger(__name__)

# Configuration
MIN_SCORE_THRESHOLD = 30
ANTI_GENERIC_NOVELTY_THRESHOLD = 20
SIMILARITY_THRESHOLD = 0.85
CONTRADICTION_SIMILARITY_FLOOR = 0.3
MAX_GRAPH_NODES = 20


@dataclass
class TurnMetrics:
    """Structured per-turn telemetry (task 10.1)."""

    session_id: str = ""
    turn_id: str = ""
    extracted_count: int = 0
    scored_count: int = 0
    created_count: int = 0
    merged_count: int = 0
    linked_count: int = 0
    demoted_generic_count: int = 0
    avg_score: float = 0.0
    min_score: int = 0
    max_score: int = 0
    score_stdev: float = 0.0
    dedup_trigger_count: int = 0
    dedup_rate: float = 0.0
    contradiction_count: int = 0
    selected_question: str = ""
    selected_gap_type: str = ""
    user_message_length: int = 0
    extraction_failed: bool = False
    total_latency_ms: float = 0.0
    extract_latency_ms: float = 0.0
    score_latency_ms: float = 0.0
    dedup_latency_ms: float = 0.0
    persist_latency_ms: float = 0.0
    question_latency_ms: float = 0.0


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
    metrics: TurnMetrics = field(default_factory=TurnMetrics)


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
        2b. Anti-generic filter: demote nuggets with Novelty < 20
        3. Deduplicate against existing nodes
        4. Persist new nodes, edges, nuggets, and provenance
        4b. Soft contradiction detection
        5. Generate next-best questions
        6. Emit structured telemetry log

        Returns:
            PipelineResult with all outputs
        """
        t_start = time.monotonic()
        result = PipelineResult()
        metrics = result.metrics
        metrics.session_id = str(self.session_id)
        metrics.turn_id = str(chat_turn_id)
        metrics.user_message_length = len(user_message)

        # Get session context
        session_context = await self._get_session_context()
        downvoted_context = await self._get_downvoted_context()
        existing_nodes = await self._get_existing_nodes()

        # Step 1: Extract nuggets
        t0 = time.monotonic()
        try:
            extract_output = await self._extract_nuggets(user_message, session_context)
            result.extracted_nuggets = extract_output.nuggets
        except ValidationRetryExhaustedError as e:
            logger.error(f"Extraction failed: {e}")
            result.extraction_failed = True
            result.failure_reason = "I couldn't identify any distinct ideas from what you shared."
            metrics.extraction_failed = True
            self._emit_metrics(metrics, t_start)
            return result
        metrics.extract_latency_ms = (time.monotonic() - t0) * 1000

        # Check for extraction failure (no nuggets)
        if not result.extracted_nuggets:
            result.extraction_failed = True
            result.failure_reason = "I couldn't identify any distinct ideas from what you shared."
            metrics.extraction_failed = True
            self._emit_metrics(metrics, t_start)
            return result

        # Filter low-confidence nuggets if we have alternatives
        high_confidence = [n for n in result.extracted_nuggets if n.confidence != "low"]
        if high_confidence:
            result.extracted_nuggets = high_confidence

        metrics.extracted_count = len(result.extracted_nuggets)

        # Step 2: Score nuggets
        t0 = time.monotonic()
        try:
            score_output = await self._score_nuggets(
                result.extracted_nuggets,
                session_context,
                downvoted_context,
            )
            result.scored_nuggets = score_output.scored_nuggets
        except ValidationRetryExhaustedError as e:
            logger.error(f"Scoring failed: {e}")
            # Use default scores on failure
            result.scored_nuggets = self._default_scores(result.extracted_nuggets)
        metrics.score_latency_ms = (time.monotonic() - t0) * 1000

        # Step 2b: Anti-generic filter (task 10.2)
        # Demote nuggets with Novelty < ANTI_GENERIC_NOVELTY_THRESHOLD
        demoted_count = 0
        for scored in result.scored_nuggets:
            if scored.dimension_scores.novelty < ANTI_GENERIC_NOVELTY_THRESHOLD:
                demoted_count += 1
        metrics.demoted_generic_count = demoted_count

        # Check if all nuggets are below threshold
        valid_nuggets = [
            s
            for s in result.scored_nuggets
            if s.dimension_scores.total_score >= MIN_SCORE_THRESHOLD
        ]
        if not valid_nuggets:
            result.extraction_failed = True
            result.failure_reason = "The ideas I captured seem too vague or general to be useful."
            metrics.extraction_failed = True
            self._emit_metrics(metrics, t_start)
            return result

        # Compute score statistics for metrics
        all_scores = [s.dimension_scores.total_score for s in result.scored_nuggets]
        metrics.scored_count = len(all_scores)
        metrics.avg_score = sum(all_scores) / len(all_scores) if all_scores else 0.0
        metrics.min_score = min(all_scores) if all_scores else 0
        metrics.max_score = max(all_scores) if all_scores else 0
        if len(all_scores) > 1:
            mean = metrics.avg_score
            metrics.score_stdev = (
                sum((s - mean) ** 2 for s in all_scores) / len(all_scores)
            ) ** 0.5

        # Step 3: Deduplicate
        t0 = time.monotonic()
        try:
            dedup_output = await self._deduplicate(
                result.extracted_nuggets,
                result.scored_nuggets,
                existing_nodes,
            )
            result.dedup_decisions = dedup_output
        except ValidationRetryExhaustedError as e:
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
        metrics.dedup_latency_ms = (time.monotonic() - t0) * 1000

        # Dedup rate metrics (task 10.3)
        for d in result.dedup_decisions:
            if d.outcome == DedupOutcome.merge:
                metrics.merged_count += 1
                metrics.dedup_trigger_count += 1
            elif d.outcome in (DedupOutcome.link_expands, DedupOutcome.link_related):
                metrics.linked_count += 1
                metrics.dedup_trigger_count += 1
        total_decisions = len(result.dedup_decisions)
        metrics.dedup_rate = (
            metrics.dedup_trigger_count / total_decisions if total_decisions else 0.0
        )

        # Step 4: Persist to graph
        t0 = time.monotonic()
        await self._persist_graph(
            result.extracted_nuggets,
            result.scored_nuggets,
            result.dedup_decisions,
            chat_turn_id,
            result,
        )
        metrics.persist_latency_ms = (time.monotonic() - t0) * 1000
        metrics.created_count = len(result.created_nodes)

        # Step 4b: Soft contradiction detection (task 10.4)
        t0 = time.monotonic()
        contradiction_count = await self._detect_contradictions(
            result.created_nodes, existing_nodes
        )
        metrics.contradiction_count = contradiction_count

        # Step 5: Generate questions
        t0 = time.monotonic()
        try:
            questions_output = await self._generate_questions(
                result.extracted_nuggets,
                result.scored_nuggets,
                result.created_nuggets,
                downvoted_context,
            )
            result.questions = questions_output.candidates
            result.why_primary = questions_output.why_primary
        except ValidationRetryExhaustedError as e:
            logger.error(f"Question generation failed: {e}")
            # Use default question
            result.questions = self._default_questions(result.extracted_nuggets)
            result.why_primary = "Let's explore this further with a concrete example."
        metrics.question_latency_ms = (time.monotonic() - t0) * 1000

        # Record selected question
        if result.questions:
            best_q = max(result.questions, key=lambda q: q.total_score)
            metrics.selected_question = best_q.question
            metrics.selected_gap_type = best_q.gap_type.value

        # Step 6: Emit structured telemetry (task 10.1)
        self._emit_metrics(metrics, t_start)

        # Session-level dedup rate log (task 10.3)
        session_dedup_rate = await self._get_session_dedup_rate()
        logger.info(
            "session_dedup_rate",
            extra={
                "session_id": str(self.session_id),
                "session_dedup_rate": round(session_dedup_rate, 3),
            },
        )

        return result

    async def _get_session_dedup_rate(self) -> float:
        """Compute session-level dedup rate: fraction of edges that are
        ``expands_on`` or ``contradicts`` vs total nodes (task 10.3)."""
        node_count_result = await self.db.execute(
            select(func.count(Node.id)).where(Node.session_id == self.session_id)
        )
        node_count = node_count_result.scalar_one()
        if node_count == 0:
            return 0.0

        dedup_edge_result = await self.db.execute(
            select(func.count(Edge.id))
            .where(Edge.session_id == self.session_id)
            .where(Edge.edge_type.in_([EdgeType.expands_on, EdgeType.contradicts]))
        )
        dedup_edge_count = dedup_edge_result.scalar_one()
        return dedup_edge_count / node_count

    def _emit_metrics(self, metrics: TurnMetrics, t_start: float) -> None:
        """Emit structured per-turn metrics as a JSON log line."""
        metrics.total_latency_ms = (time.monotonic() - t_start) * 1000
        logger.info(
            "pipeline_turn_metrics",
            extra={
                "turn_metrics": {
                    "session_id": metrics.session_id,
                    "turn_id": metrics.turn_id,
                    "extracted_count": metrics.extracted_count,
                    "scored_count": metrics.scored_count,
                    "created_count": metrics.created_count,
                    "merged_count": metrics.merged_count,
                    "linked_count": metrics.linked_count,
                    "demoted_generic_count": metrics.demoted_generic_count,
                    "avg_score": round(metrics.avg_score, 1),
                    "min_score": metrics.min_score,
                    "max_score": metrics.max_score,
                    "score_stdev": round(metrics.score_stdev, 1),
                    "dedup_trigger_count": metrics.dedup_trigger_count,
                    "dedup_rate": round(metrics.dedup_rate, 3),
                    "contradiction_count": metrics.contradiction_count,
                    "selected_question": metrics.selected_question[:100],
                    "selected_gap_type": metrics.selected_gap_type,
                    "user_message_length": metrics.user_message_length,
                    "extraction_failed": metrics.extraction_failed,
                    "total_latency_ms": round(metrics.total_latency_ms, 1),
                    "extract_latency_ms": round(metrics.extract_latency_ms, 1),
                    "score_latency_ms": round(metrics.score_latency_ms, 1),
                    "dedup_latency_ms": round(metrics.dedup_latency_ms, 1),
                    "persist_latency_ms": round(metrics.persist_latency_ms, 1),
                    "question_latency_ms": round(metrics.question_latency_ms, 1),
                }
            },
        )

    async def _detect_contradictions(
        self,
        new_nodes: list[Node],
        existing_nodes: list[ExistingNodeContext],
    ) -> int:
        """Soft contradiction detection (task 10.4).

        Uses simple heuristic: if a new node's title contains a negation
        word and shares significant word overlap with an existing node,
        flag it as a potential contradiction by creating a ``contradicts``
        edge.  Returns the number of contradiction edges created.
        """
        if not new_nodes or not existing_nodes:
            return 0

        negation_signals = {
            "not",
            "never",
            "don't",
            "dont",
            "shouldn't",
            "shouldnt",
            "avoid",
            "stop",
            "wrong",
            "myth",
            "overrated",
            "instead",
            "contrary",
            "opposite",
            "actually",
            "however",
            "but",
        }

        contradiction_count = 0
        for node in new_nodes:
            node_words = set(node.title.lower().split())
            has_negation = bool(node_words & negation_signals)

            if not has_negation:
                continue

            content_words = node_words - negation_signals
            for existing in existing_nodes:
                existing_words = set(existing.title.lower().split())
                if not content_words or not existing_words:
                    continue

                overlap = len(content_words & existing_words)
                union = len(content_words | existing_words)
                similarity = overlap / union if union > 0 else 0.0

                if similarity >= CONTRADICTION_SIMILARITY_FLOOR:
                    edge = Edge(
                        session_id=self.session_id,
                        source_id=node.id,
                        target_id=uuid.UUID(existing.node_id),
                        edge_type=EdgeType.contradicts,
                    )
                    self.db.add(edge)
                    contradiction_count += 1
                    logger.info(
                        "contradiction_detected",
                        extra={
                            "new_node": node.title,
                            "existing_node": existing.title,
                            "similarity": round(similarity, 3),
                        },
                    )

        if contradiction_count:
            await self.db.flush()
        return contradiction_count

    async def _get_session_context(self) -> str:
        """Get context from session onboarding data + existing high-value nuggets."""
        context_parts: list[str] = []

        # Include onboarding context (project name, topic, audience)
        session_result = await self.db.execute(select(Session).where(Session.id == self.session_id))
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
        nuggets_json = json.dumps([n.model_dump() for n in nuggets], indent=2)
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
                    existing_node_id=(
                        best_match.node_id
                        if best_match and outcome != DedupOutcome.create
                        else None
                    ),
                    merge_rationale=(
                        f"Similar to: {best_match.title}"
                        if best_match and outcome != DedupOutcome.create
                        else None
                    ),
                    similarity_score=best_similarity,
                )
            )

        return decisions

    @staticmethod
    def _compute_persisted_score(score_data: ScoredNugget | None) -> int:
        """Compute the final persisted score, applying anti-generic demotion.

        If the nugget's Novelty dimension is below the anti-generic threshold,
        the persisted score is halved so the nugget won't surface in top results
        (task 10.2).
        """
        if score_data is None:
            return 50
        raw = score_data.dimension_scores.total_score
        if score_data.dimension_scores.novelty < ANTI_GENERIC_NOVELTY_THRESHOLD:
            return max(0, raw // 2)
        return raw

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
                    score=self._compute_persisted_score(score_data),
                    dimension_scores=(
                        score_data.dimension_scores.model_dump() if score_data else None
                    ),
                    missing_fields=(
                        [f.value for f in score_data.missing_fields] if score_data else []
                    ),
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
                    score=self._compute_persisted_score(score_data),
                    dimension_scores=(
                        score_data.dimension_scores.model_dump() if score_data else None
                    ),
                    missing_fields=(
                        [f.value for f in score_data.missing_fields] if score_data else []
                    ),
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
                    "score": (score_data.dimension_scores.total_score if score_data else 50),
                    "missing_fields": (
                        [f.value for f in score_data.missing_fields] if score_data else []
                    ),
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

    def _default_scores(self, nuggets: list[CandidateNugget]) -> list[ScoredNugget]:
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

    def _default_questions(self, nuggets: list[CandidateNugget]) -> list[NextQuestionCandidate]:
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
