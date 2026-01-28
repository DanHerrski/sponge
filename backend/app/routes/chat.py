"""POST /chat_turn — accept user input, persist chat turn, return stubbed response."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tables import ChatRole, ChatTurn, Session
from app.schemas import (
    AlternatePath,
    CapturedNugget,
    ChatTurnRequest,
    ChatTurnResponse,
    NextQuestion,
)

router = APIRouter(tags=["chat"])


@router.post("/chat_turn", response_model=ChatTurnResponse)
async def create_chat_turn(
    request: ChatTurnRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatTurnResponse:
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

    # --- Stub: placeholder response ---
    # In the real implementation, this is where the LLM extraction + scoring
    # + dedup + graph write + question selection pipeline runs.
    stub_nugget_id = uuid.uuid4()
    stub_node_id = uuid.uuid4()

    # Persist assistant turn (stub)
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
        captured_nuggets=[
            CapturedNugget(
                nugget_id=stub_nugget_id,
                node_id=stub_node_id,
                title="[stub] Extracted nugget from your input",
                nugget_type="Idea",
                score=65,
                is_new=True,
            )
        ],
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
