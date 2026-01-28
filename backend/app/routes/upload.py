"""POST /upload — accept file, store metadata (no extraction yet)."""

import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.tables import Document
from app.schemas import UploadResponse

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    session_id: uuid.UUID,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
) -> UploadResponse:
    if file.size and file.size > settings.max_upload_size_bytes:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    # Ensure upload directory exists
    os.makedirs(settings.upload_dir, exist_ok=True)

    # Store file to local filesystem
    doc_id = uuid.uuid4()
    ext = os.path.splitext(file.filename or "upload")[1]
    storage_path = os.path.join(settings.upload_dir, f"{doc_id}{ext}")

    content = await file.read()
    with open(storage_path, "wb") as f:
        f.write(content)

    # Persist document metadata
    document = Document(
        id=doc_id,
        session_id=session_id,
        filename=file.filename or "upload",
        content_type=file.content_type or "application/octet-stream",
        storage_path=storage_path,
        size_bytes=len(content),
    )
    db.add(document)
    await db.commit()

    return UploadResponse(
        document_id=doc_id,
        filename=document.filename,
        size_bytes=document.size_bytes,
        message="[stub] File stored. Nugget extraction not yet implemented.",
    )
