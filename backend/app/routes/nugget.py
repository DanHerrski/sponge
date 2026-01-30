"""POST /nugget/:id/feedback — allow users to approve/reject extracted nuggets."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tables import Nugget, UserFeedback
from app.schemas import (
    NuggetFeedbackRequest,
    NuggetFeedbackResponse,
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
