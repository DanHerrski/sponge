"""GET /graph_view, GET /node/:id, PATCH /node/:id — serve and edit knowledge graph data."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.tables import Edge, Node
from app.schemas import (
    DimensionScores,
    GraphEdge,
    GraphNode,
    GraphViewResponse,
    NodeDetailResponse,
    NodeEditRequest,
    NodeEditResponse,
    NuggetDetail,
    ProvenanceRecord,
)

router = APIRouter(tags=["graph"])


@router.get("/graph_view", response_model=GraphViewResponse)
async def get_graph_view(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> GraphViewResponse:
    # Fetch nodes for the session
    node_result = await db.execute(
        select(Node)
        .where(Node.session_id == session_id)
        .options(selectinload(Node.nugget))
    )
    nodes = node_result.scalars().all()

    # Fetch edges for the session
    edge_result = await db.execute(
        select(Edge).where(Edge.session_id == session_id)
    )
    edges = edge_result.scalars().all()

    return GraphViewResponse(
        nodes=[
            GraphNode(
                node_id=n.id,
                node_type=n.node_type.value,
                title=n.title,
                summary=n.summary,
                score=n.nugget.score if n.nugget else None,
            )
            for n in nodes
        ],
        edges=[
            GraphEdge(
                edge_id=e.id,
                source_id=e.source_id,
                target_id=e.target_id,
                edge_type=e.edge_type.value,
            )
            for e in edges
        ],
    )


@router.get("/node/{node_id}", response_model=NodeDetailResponse)
async def get_node_detail(
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> NodeDetailResponse:
    result = await db.execute(
        select(Node)
        .where(Node.id == node_id)
        .options(
            selectinload(Node.nugget),
            selectinload(Node.provenance_records),
        )
    )
    node = result.scalar_one_or_none()

    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")

    nugget_detail = None
    if node.nugget:
        dim_scores = None
        if node.nugget.dimension_scores:
            dim_scores = DimensionScores(**node.nugget.dimension_scores)
        nugget_detail = NuggetDetail(
            nugget_id=node.nugget.id,
            score=node.nugget.score,
            dimension_scores=dim_scores,
            missing_fields=node.nugget.missing_fields or [],
            next_questions=node.nugget.next_questions or [],
        )

    return NodeDetailResponse(
        node_id=node.id,
        node_type=node.node_type.value,
        title=node.title,
        summary=node.summary,
        provenance=[
            ProvenanceRecord(
                source_type=p.source_type.value,
                source_id=p.source_id,
                timestamp=p.created_at,
                confidence=p.confidence.value,
            )
            for p in node.provenance_records
        ],
        nugget=nugget_detail,
    )


@router.patch("/node/{node_id}", response_model=NodeEditResponse)
async def edit_node(
    node_id: uuid.UUID,
    request: NodeEditRequest,
    db: AsyncSession = Depends(get_db),
) -> NodeEditResponse:
    """
    Edit a node's title and/or summary.

    Allows users to correct extraction errors or refine captured ideas.
    - Overwrites existing values (no versioning for P0)
    - Preserves provenance and original extraction metadata
    - Also updates the associated nugget's title/summary if present
    """
    # Validate that at least one field is provided
    if request.title is None and request.summary is None:
        raise HTTPException(
            status_code=400,
            detail="At least one of 'title' or 'summary' must be provided",
        )

    # Fetch the node with its nugget
    result = await db.execute(
        select(Node)
        .where(Node.id == node_id)
        .options(selectinload(Node.nugget))
    )
    node = result.scalar_one_or_none()

    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")

    # Track what was updated for the message
    updated_fields = []

    # Update node fields
    if request.title is not None:
        node.title = request.title
        updated_fields.append("title")
        # Also update the nugget's title if it exists
        if node.nugget:
            node.nugget.title = request.title

    if request.summary is not None:
        node.summary = request.summary
        updated_fields.append("summary")
        # Also update the nugget's short_summary if it exists
        if node.nugget:
            node.nugget.short_summary = request.summary

    await db.commit()
    await db.refresh(node)

    return NodeEditResponse(
        node_id=node.id,
        title=node.title,
        summary=node.summary,
        message=f"Node updated: {', '.join(updated_fields)} changed.",
    )
