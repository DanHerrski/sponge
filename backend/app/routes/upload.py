"""POST /upload — accept file, parse, chunk, extract nuggets via pipeline."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.llm.pipeline import ExtractionPipeline
from app.models.tables import ChatRole, ChatTurn, Document, Session
from app.schemas import UploadNuggetSummary, UploadResponse
from app.services.chunker import chunk_text
from app.services.filestore import FileStore
from app.services.parser import extract_text

router = APIRouter(tags=["upload"])
logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".txt", ".docx"}


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    session_id: uuid.UUID,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
) -> UploadResponse:
    """
    Upload a document, parse it, chunk it, and extract nuggets.

    Pipeline:
    1. Validate file type and size
    2. Store file via FileStore
    3. Parse text from file (.txt / .docx)
    4. Split into semantic chunks
    5. Run extraction pipeline on each chunk
    6. Return summary with top nuggets and deep-dive options
    """
    # Validate file size
    if file.size and file.size > settings.max_upload_size_bytes:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    # Validate file type
    filename = file.filename or "upload"
    import os

    ext = os.path.splitext(filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}",
        )

    # Read and store file
    content = await file.read()
    store = FileStore()
    doc_id, storage_path = store.save(content, filename)

    # Persist document metadata
    document = Document(
        id=doc_id,
        session_id=session_id,
        filename=filename,
        content_type=file.content_type or "application/octet-stream",
        storage_path=storage_path,
        size_bytes=len(content),
    )
    db.add(document)
    await db.flush()

    # Parse text from document
    try:
        text = extract_text(content, filename)
    except (ValueError, ImportError) as e:
        await db.commit()
        return UploadResponse(
            document_id=doc_id,
            filename=filename,
            size_bytes=len(content),
            message=f"File stored but could not parse text: {e}",
            nugget_count=0,
            top_nuggets=[],
            deep_dive_options=[],
        )

    if not text.strip():
        await db.commit()
        return UploadResponse(
            document_id=doc_id,
            filename=filename,
            size_bytes=len(content),
            message="File stored but contained no extractable text.",
            nugget_count=0,
            top_nuggets=[],
            deep_dive_options=[],
        )

    # Chunk the text
    chunks = chunk_text(text)
    logger.info(f"Upload {doc_id}: parsed {len(text)} chars into {len(chunks)} chunks")

    # Run extraction pipeline on each chunk
    all_nuggets = []
    pipeline = ExtractionPipeline(db, session_id)

    # Create a synthetic chat turn for provenance tracking
    from sqlalchemy import func, select
    from app.models.tables import ChatTurn as CT

    result = await db.execute(
        select(func.coalesce(func.max(CT.turn_number), 0)).where(
            CT.session_id == session_id
        )
    )
    next_turn = result.scalar_one() + 1

    for chunk in chunks:
        # Store chunk as a system chat turn for provenance
        chunk_turn = ChatTurn(
            session_id=session_id,
            turn_number=next_turn,
            role=ChatRole.user,
            content=f"[Upload: {filename}] {chunk.text[:500]}",
        )
        db.add(chunk_turn)
        await db.flush()
        next_turn += 1

        # Run pipeline on this chunk
        pipeline_result = await pipeline.run(
            user_message=chunk.text,
            chat_turn_id=chunk_turn.id,
        )

        if not pipeline_result.extraction_failed:
            all_nuggets.extend(pipeline_result.created_nuggets)

    # Count types
    idea_count = sum(1 for n in all_nuggets if n.nugget_type.value == "idea")
    story_count = sum(1 for n in all_nuggets if n.nugget_type.value == "story")
    framework_count = sum(1 for n in all_nuggets if n.nugget_type.value == "framework")

    # Build type summary
    type_parts = []
    if idea_count:
        type_parts.append(f"{idea_count} idea{'s' if idea_count != 1 else ''}")
    if story_count:
        type_parts.append(f"{story_count} stor{'ies' if story_count != 1 else 'y'}")
    if framework_count:
        type_parts.append(f"{framework_count} framework{'s' if framework_count != 1 else ''}")

    type_summary = " and ".join(type_parts) if type_parts else "no distinct nuggets"
    message = f"I found {type_summary} in your document."

    # Top 3 nuggets by score
    sorted_nuggets = sorted(all_nuggets, key=lambda n: n.score, reverse=True)
    top_nuggets = [
        UploadNuggetSummary(
            nugget_id=n.id,
            title=n.title,
            nugget_type=n.nugget_type.value,
            score=n.score,
        )
        for n in sorted_nuggets[:3]
    ]

    # Deep-dive options from top nuggets' missing fields
    deep_dive_options: list[str] = []
    for n in sorted_nuggets[:3]:
        if n.missing_fields:
            gap = n.missing_fields[0] if n.missing_fields else "example"
            deep_dive_options.append(
                f"Explore '{n.title}' — needs {gap}"
            )
    # Pad to 3 options
    while len(deep_dive_options) < 3 and sorted_nuggets:
        deep_dive_options.append(
            f"Tell me more about '{sorted_nuggets[0].title}'"
        )

    # Store assistant response
    assistant_turn = ChatTurn(
        session_id=session_id,
        turn_number=next_turn,
        role=ChatRole.assistant,
        content=message,
    )
    db.add(assistant_turn)
    await db.commit()

    return UploadResponse(
        document_id=doc_id,
        filename=filename,
        size_bytes=len(content),
        message=message,
        nugget_count=len(all_nuggets),
        top_nuggets=top_nuggets,
        deep_dive_options=deep_dive_options[:3],
    )
