"""POST /chat_turn — process user input through the extraction pipeline."""

import logging
import uuid
from typing import Union

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.llm.pipeline import ExtractionPipeline, get_graph_subset
from app.models.tables import ChatRole, ChatTurn, Session, UserFeedback
from app.schemas import (
    AlternatePath,
    CapturedNugget,
    CapturedNuggetDimensionScores,
    ChatTurnRequest,
    ChatTurnResponse,
    ExtractionFailureResponse,
    FeedbackValue,
    GraphEdge,
    GraphNode,
    NextQuestion,
)

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)

# Recovery questions to ask when extraction fails
RECOVERY_QUESTIONS = [
    "Can you give me a concrete example of what you mean?",
    "What decision or mistake does this relate to?",
    "Who specifically would benefit from this idea?",
    "What's the one thing you'd want someone to remember from this?",
    "Can you tell me a short story that illustrates this?",
]


def _select_recovery_question(turn_number: int) -> str:
    """Select a recovery question based on turn number for variety."""
    return RECOVERY_QUESTIONS[turn_number % len(RECOVERY_QUESTIONS)]


def _feedback_to_schema(feedback: UserFeedback | None) -> FeedbackValue | None:
    """Convert UserFeedback enum to FeedbackValue schema."""
    if feedback is None:
        return None
    return FeedbackValue(feedback.value)


@router.post(
    "/chat_turn",
    response_model=Union[ChatTurnResponse, ExtractionFailureResponse],
)
async def create_chat_turn(
    request: ChatTurnRequest,
    db: AsyncSession = Depends(get_db),
) -> Union[ChatTurnResponse, ExtractionFailureResponse]:
    """
    Process a user's brain-dump message through the extraction pipeline.

    This endpoint:
    1. Stores the user's message as a chat turn
    2. Extracts nuggets via LLM
    3. Scores nuggets with dimension breakdowns
    4. Deduplicates against existing nodes
    5. Persists to knowledge graph
    6. Generates next-best questions
    7. Returns structured response with graph subset

    If extraction fails (zero nuggets or all below threshold), returns
    an ExtractionFailureResponse with a recovery question.
    """
    # Resolve or create session
    if request.session_id:
        session_id = request.session_id
    else:
        new_session = Session(project_name="Untitled", topic=None)
        db.add(new_session)
        await db.flush()
        session_id = new_session.id

    # Determine next turn number
    result = await db.execute(
        select(func.coalesce(func.max(ChatTurn.turn_number), 0)).where(
            ChatTurn.session_id == session_id
        )
    )
    next_turn = result.scalar_one() + 1

    # Persist user chat turn
    user_turn = ChatTurn(
        session_id=session_id,
        turn_number=next_turn,
        role=ChatRole.user,
        content=request.message,
    )
    db.add(user_turn)
    await db.flush()

    # Run extraction pipeline
    pipeline = ExtractionPipeline(db, session_id)
    pipeline_result = await pipeline.run(
        user_message=request.message,
        chat_turn_id=user_turn.id,
    )

    # Handle extraction failure
    if pipeline_result.extraction_failed:
        recovery_question = _select_recovery_question(next_turn)
        assistant_content = (
            f"I'm not sure I fully captured that. {pipeline_result.failure_reason} "
            f"{recovery_question}"
        )
        assistant_turn = ChatTurn(
            session_id=session_id,
            turn_number=next_turn + 1,
            role=ChatRole.assistant,
            content=assistant_content,
        )
        db.add(assistant_turn)
        await db.commit()

        return ExtractionFailureResponse(
            turn_id=user_turn.id,
            session_id=session_id,
            extraction_failed=True,
            failure_reason=pipeline_result.failure_reason,
            recovery_question=recovery_question,
            captured_nuggets=[],
            graph_update_summary="",
        )

    # Build captured nuggets from pipeline result
    captured_nuggets: list[CapturedNugget] = []
    for nugget in pipeline_result.created_nuggets:
        # Get dimension scores
        dim_scores = None
        if nugget.dimension_scores:
            dim_scores = CapturedNuggetDimensionScores(
                specificity=nugget.dimension_scores.get("specificity", 50),
                novelty=nugget.dimension_scores.get("novelty", 50),
                authority=nugget.dimension_scores.get("authority", 50),
                actionability=nugget.dimension_scores.get("actionability", 50),
                story_energy=nugget.dimension_scores.get("story_energy", 50),
                audience_resonance=nugget.dimension_scores.get("audience_resonance", 50),
            )

        captured_nuggets.append(
            CapturedNugget(
                nugget_id=nugget.id,
                node_id=nugget.node_id,
                title=nugget.title,
                nugget_type=nugget.nugget_type.value.capitalize(),
                score=nugget.score,
                is_new=True,
                user_feedback=_feedback_to_schema(nugget.user_feedback),
                dimension_scores=dim_scores,
            )
        )

    # Filter to top 4 nuggets by score, excluding any that were downvoted
    captured_nuggets = [
        n for n in captured_nuggets if n.user_feedback != FeedbackValue.down
    ]
    captured_nuggets = sorted(captured_nuggets, key=lambda n: n.score, reverse=True)[:4]

    # Build graph update summary
    node_count = len(pipeline_result.created_nodes)
    edge_count = len(pipeline_result.created_edges)
    graph_update_summary = f"Added {node_count} new node{'s' if node_count != 1 else ''}"
    if edge_count > 0:
        graph_update_summary += f" and {edge_count} connection{'s' if edge_count != 1 else ''}"
    graph_update_summary += " to your knowledge graph."

    # Build next question from pipeline result
    next_question = None
    alternate_paths: list[AlternatePath] = []

    if pipeline_result.questions:
        # Sort by total score
        sorted_questions = sorted(
            pipeline_result.questions, key=lambda q: q.total_score, reverse=True
        )

        # Primary question
        primary = sorted_questions[0]

        # Map nugget index to actual nugget ID
        target_nugget_id = None
        if primary.target_nugget_index < len(pipeline_result.created_nuggets):
            target_nugget_id = pipeline_result.created_nuggets[
                primary.target_nugget_index
            ].id

        if target_nugget_id:
            next_question = NextQuestion(
                question=primary.question,
                target_nugget_id=target_nugget_id,
                gap_type=primary.gap_type.value,
                why_this_next=pipeline_result.why_primary,
            )

            # Alternate paths (next 2 questions)
            for alt in sorted_questions[1:3]:
                alt_target_id = None
                if alt.target_nugget_index < len(pipeline_result.created_nuggets):
                    alt_target_id = pipeline_result.created_nuggets[
                        alt.target_nugget_index
                    ].id
                if alt_target_id:
                    alternate_paths.append(
                        AlternatePath(
                            question=alt.question,
                            target_nugget_id=alt_target_id,
                            gap_type=alt.gap_type.value,
                        )
                    )

    # Fallback next question if none generated
    if not next_question and captured_nuggets:
        next_question = NextQuestion(
            question=f"Can you give me a specific example of '{captured_nuggets[0].title}'?",
            target_nugget_id=captured_nuggets[0].nugget_id,
            gap_type="example",
            why_this_next="A concrete example would make this insight more compelling.",
        )

    # Get graph subset for UI
    nodes, edges = await get_graph_subset(db, session_id)

    # Build graph response
    graph_nodes = [
        GraphNode(
            node_id=n.id,
            node_type=n.node_type.value,
            title=n.title,
            summary=n.summary,
            score=n.nugget.score if n.nugget else None,
        )
        for n in nodes
    ]
    graph_edges = [
        GraphEdge(
            edge_id=e.id,
            source_id=e.source_id,
            target_id=e.target_id,
            edge_type=e.edge_type.value,
        )
        for e in edges
    ]

    # Persist assistant turn
    nugget_titles = [n.title for n in captured_nuggets[:3]]
    assistant_content = f"Captured: {', '.join(nugget_titles)}. {graph_update_summary}"
    if next_question:
        assistant_content += f" {next_question.question}"

    assistant_turn = ChatTurn(
        session_id=session_id,
        turn_number=next_turn + 1,
        role=ChatRole.assistant,
        content=assistant_content,
    )
    db.add(assistant_turn)
    await db.commit()

    return ChatTurnResponse(
        turn_id=user_turn.id,
        session_id=session_id,
        captured_nuggets=captured_nuggets,
        graph_update_summary=graph_update_summary,
        next_question=next_question,
        alternate_paths=alternate_paths,
        graph_nodes=graph_nodes,
        graph_edges=graph_edges,
    )
