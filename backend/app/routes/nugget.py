"""Nugget endpoints: list, feedback, and status management."""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tables import Node, Nugget, NuggetStatus, UserFeedback
from app.schemas import (
    FeedbackValue,
    NuggetFeedbackRequest,
    NuggetFeedbackResponse,
    NuggetListItem,
    NuggetListResponse,
    NuggetStatusRequest,
    NuggetStatusResponse,
)

router = APIRouter(tags=["nugget"])

# Score boost applied to upvoted nuggets (heuristic, not LLM-based)
UPVOTE_SCORE_BOOST = 5


@router.post("/nugget/{nugget_id}/feedback", response_model=NuggetFeedbackResponse)
async def submit_nugget_feedback(
    nugget_id: uuid.UUID,
    request: NuggetFeedbackRequest,
    db: AsyncSession = Depends(get_db),
) -> NuggetFeedbackResponse:
    """
    Submit user feedback (thumbs up/down) on an extracted nugget.

    Behavior:
    - Downvoted nuggets are excluded from next-best-question candidate set
    - Downvoted nuggets are excluded from top surfaced nuggets in future turns
    - Upvoted nuggets receive a small score boost
    - Feedback is persisted for later evaluation (no learning loop yet)
    """
    # Fetch the nugget
    result = await db.execute(select(Nugget).where(Nugget.id == nugget_id))
    nugget = result.scalar_one_or_none()

    if nugget is None:
        raise HTTPException(status_code=404, detail="Nugget not found")

    # Convert string feedback to enum
    feedback_enum = UserFeedback(request.feedback.value)

    # Store previous feedback to handle score adjustment correctly
    previous_feedback = nugget.user_feedback

    # Update feedback
    nugget.user_feedback = feedback_enum

    # Apply score boost for upvotes, remove boost if changing from up to down
    if feedback_enum == UserFeedback.up:
        # Only add boost if not already upvoted
        if previous_feedback != UserFeedback.up:
            nugget.score = min(100, nugget.score + UPVOTE_SCORE_BOOST)
    elif feedback_enum == UserFeedback.down:
        # Remove boost if previously upvoted
        if previous_feedback == UserFeedback.up:
            nugget.score = max(0, nugget.score - UPVOTE_SCORE_BOOST)

    await db.commit()

    # Determine message based on feedback
    if feedback_enum == UserFeedback.up:
        message = "Nugget approved. It will be prioritized in future suggestions."
    else:
        message = "Nugget rejected. It will be excluded from future suggestions."

    return NuggetFeedbackResponse(
        nugget_id=nugget.id,
        user_feedback=request.feedback,
        message=message,
    )


@router.get("/nugget/{nugget_id}/feedback")
async def get_nugget_feedback(
    nugget_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the current feedback status for a nugget."""
    result = await db.execute(select(Nugget).where(Nugget.id == nugget_id))
    nugget = result.scalar_one_or_none()

    if nugget is None:
        raise HTTPException(status_code=404, detail="Nugget not found")

    return {
        "nugget_id": nugget.id,
        "user_feedback": nugget.user_feedback.value if nugget.user_feedback else None,
        "score": nugget.score,
    }


@router.get("/nuggets", response_model=NuggetListResponse)
async def list_nuggets(
    session_id: uuid.UUID,
    nugget_type: str | None = Query(default=None, description="Filter by type: idea, story, framework"),
    status: str | None = Query(default=None, description="Filter by status: new, explored, parked"),
    sort_by: Literal["score", "created_at"] = Query(default="score", description="Sort field"),
    db: AsyncSession = Depends(get_db),
) -> NuggetListResponse:
    """
    List all nuggets for a session with optional filters and sorting.

    Supports:
    - Type filter (idea, story, framework)
    - Status filter (new, explored, parked)
    - Sort by score (default, descending) or created_at (descending)
    """
    stmt = (
        select(Nugget)
        .join(Node)
        .where(Node.session_id == session_id)
    )

    if nugget_type:
        stmt = stmt.where(Nugget.nugget_type == nugget_type)

    if status:
        stmt = stmt.where(Nugget.status == status)

    if sort_by == "score":
        stmt = stmt.order_by(Nugget.score.desc())
    else:
        stmt = stmt.order_by(Nugget.created_at.desc())

    result = await db.execute(stmt)
    nuggets = result.scalars().all()

    items = [
        NuggetListItem(
            nugget_id=n.id,
            node_id=n.node_id,
            title=n.title,
            short_summary=n.short_summary,
            nugget_type=n.nugget_type.value,
            score=n.score,
            status=n.status.value,
            user_feedback=FeedbackValue(n.user_feedback.value) if n.user_feedback else None,
            missing_fields=n.missing_fields or [],
            created_at=n.created_at,
        )
        for n in nuggets
    ]

    return NuggetListResponse(nuggets=items, total=len(items))


@router.post("/nugget/{nugget_id}/status", response_model=NuggetStatusResponse)
async def update_nugget_status(
    nugget_id: uuid.UUID,
    request: NuggetStatusRequest,
    db: AsyncSession = Depends(get_db),
) -> NuggetStatusResponse:
    """
    Update a nugget's status (New -> Explored / Parked).

    Valid transitions:
    - new -> explored (user is exploring this nugget)
    - new -> parked (user wants to defer this nugget)
    - explored -> parked (done exploring, park it)
    - parked -> new (re-surface a parked nugget)
    """
    # Validate status value
    try:
        new_status = NuggetStatus(request.status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {request.status}. Must be one of: new, explored, parked",
        )

    result = await db.execute(select(Nugget).where(Nugget.id == nugget_id))
    nugget = result.scalar_one_or_none()

    if nugget is None:
        raise HTTPException(status_code=404, detail="Nugget not found")

    old_status = nugget.status.value
    nugget.status = new_status
    await db.commit()

    return NuggetStatusResponse(
        nugget_id=nugget.id,
        status=new_status.value,
        message=f"Nugget status changed from '{old_status}' to '{new_status.value}'.",
    )
