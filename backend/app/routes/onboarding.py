"""POST /onboard — create a session with project context for LLM prompts."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tables import Session
from app.schemas import OnboardingRequest, OnboardingResponse

router = APIRouter(tags=["onboarding"])


@router.post("/onboard", response_model=OnboardingResponse)
async def onboard(
    request: OnboardingRequest,
    db: AsyncSession = Depends(get_db),
) -> OnboardingResponse:
    """
    Create a new session with project context (name, topic, audience).

    The onboarding data is passed into LLM context assembly so that
    extraction and question prompts are tailored to the user's project.
    """
    session = Session(
        project_name=request.project_name,
        topic=request.topic,
        audience=request.audience,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return OnboardingResponse(
        session_id=session.id,
        project_name=session.project_name or "",
        topic=session.topic,
        audience=session.audience,
        message=f"Session created for '{session.project_name}'. Start chatting!",
    )
