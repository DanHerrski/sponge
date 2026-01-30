"""POST /chat_turn — accept user input, persist chat turn, return stubbed response."""

import uuid
from typing import Union

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tables import ChatRole, ChatTurn, Session
from app.schemas import (
    AlternatePath,
    CapturedNugget,
    CapturedNuggetDimensionScores,
    ChatTurnRequest,
    ChatTurnResponse,
    ExtractionFailureResponse,
    NextQuestion,
)

router = APIRouter(tags=["chat"])

# Minimum score threshold for nuggets to be considered valid
MIN_NUGGET_SCORE_THRESHOLD = 30

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


def _check_extraction_failure(
    extracted_nuggets: list[CapturedNugget],
    min_score_threshold: int = MIN_NUGGET_SCORE_THRESHOLD,
) -> tuple[bool, str]:
    """
    Check if extraction should be considered a failure.

    Returns:
        (is_failure, failure_reason)
    """
    # Condition 1: Zero nuggets extracted
    if len(extracted_nuggets) == 0:
        return True, "I couldn't identify any distinct ideas from what you shared."

    # Condition 2: All nuggets below minimum score threshold
    valid_nuggets = [n for n in extracted_nuggets if n.score >= min_score_threshold]
    if len(valid_nuggets) == 0:
        return True, "The ideas I captured seem too vague or general to be useful."

    return False, ""


@router.post(
    "/chat_turn",
    response_model=Union[ChatTurnResponse, ExtractionFailureResponse],
)
async def create_chat_turn(
    request: ChatTurnRequest,
    db: AsyncSession = Depends(get_db),
) -> Union[ChatTurnResponse, ExtractionFailureResponse]:
    """
    Process a user's brain-dump message and extract knowledge nuggets.

    This endpoint:
    1. Stores the user's message as a chat turn
    2. Extracts nuggets via LLM (stubbed for now)
    3. Scores and deduplicates nuggets
    4. Writes to the knowledge graph
    5. Selects the next-best question

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
        select(func.coalesce(func.max(ChatTurn.turn_number), 0))
        .where(ChatTurn.session_id == session_id)
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

    # --- Stub: placeholder extraction ---
    # In the real implementation, this is where the LLM extraction + scoring
    # + dedup + graph write + question selection pipeline runs.

    # Simulate extraction - for demo, create nuggets with dimension scores
    stub_nugget_id = uuid.uuid4()
    stub_node_id = uuid.uuid4()

    # Stub dimension scores for transparency
    stub_dimension_scores = CapturedNuggetDimensionScores(
        specificity=70,
        novelty=55,
        authority=60,
        actionability=75,
        story_energy=45,
        audience_resonance=65,
    )

    extracted_nuggets = [
        CapturedNugget(
            nugget_id=stub_nugget_id,
            node_id=stub_node_id,
            title="[stub] Extracted nugget from your input",
            nugget_type="Idea",
            score=65,
            is_new=True,
            user_feedback=None,  # No feedback yet
            dimension_scores=stub_dimension_scores,
        )
    ]

    # Check for extraction failure
    is_failure, failure_reason = _check_extraction_failure(extracted_nuggets)

    if is_failure:
        # Persist assistant turn with failure acknowledgment
        recovery_question = _select_recovery_question(next_turn)
        assistant_content = (
            f"I'm not sure I fully captured that. {failure_reason} "
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
            failure_reason=failure_reason,
            recovery_question=recovery_question,
            captured_nuggets=[],
            graph_update_summary="",
        )

    # Success path: persist assistant turn and return nuggets
    assistant_turn = ChatTurn(
        session_id=session_id,
        turn_number=next_turn + 1,
        role=ChatRole.assistant,
        content="[stub] Nuggets extracted and graph updated.",
    )
    db.add(assistant_turn)
    await db.commit()

    return ChatTurnResponse(
        turn_id=user_turn.id,
        session_id=session_id,
        captured_nuggets=extracted_nuggets,
        graph_update_summary="[stub] Added 1 new idea node to your knowledge graph.",
        next_question=NextQuestion(
            question="[stub] Can you give a concrete example of this idea?",
            target_nugget_id=stub_nugget_id,
            gap_type="example",
            why_this_next="[stub] A specific example would make this idea more compelling.",
        ),
        alternate_paths=[
            AlternatePath(
                question="[stub] Who would benefit most from this?",
                target_nugget_id=stub_nugget_id,
                gap_type="audience",
            ),
            AlternatePath(
                question="[stub] What are the concrete steps to apply this?",
                target_nugget_id=stub_nugget_id,
                gap_type="steps",
            ),
        ],
    )
