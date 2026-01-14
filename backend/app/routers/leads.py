"""Lead management API endpoints."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Lead, Conversation, Message, get_db
from app.models.schemas import (
    LeadCaptureRequest,
    LeadResponse,
    LeadUpdateRequest,
    LeadListResponse,
    ConversationResponse,
    MessageResponse,
)
from app.services.lead_capture import get_lead_capture_service, LeadCaptureService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("/", response_model=LeadResponse)
async def create_lead(
    request: LeadCaptureRequest,
    db: AsyncSession = Depends(get_db),
    lead_service: LeadCaptureService = Depends(get_lead_capture_service),
):
    """
    Create a new lead manually or from chat capture.
    """
    lead_data = request.model_dump(exclude_none=True)
    lead = await lead_service.create_lead(
        db=db,
        lead_data=lead_data,
        conversation_id=request.conversation_id,
    )
    return LeadResponse.model_validate(lead)


@router.get("/", response_model=LeadListResponse)
async def list_leads(
    status: Optional[str] = Query(None, description="Filter by status"),
    assigned_to: Optional[UUID] = Query(None, description="Filter by assignee"),
    min_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum lead score"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    lead_service: LeadCaptureService = Depends(get_lead_capture_service),
):
    """
    Get paginated list of leads with optional filters.
    """
    offset = (page - 1) * page_size
    leads, total = await lead_service.get_leads(
        db=db,
        status=status,
        assigned_to=assigned_to,
        min_score=min_score,
        limit=page_size,
        offset=offset,
    )

    return LeadListResponse(
        leads=[LeadResponse.model_validate(lead) for lead in leads],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    lead_service: LeadCaptureService = Depends(get_lead_capture_service),
):
    """
    Get a specific lead by ID.
    """
    lead = await lead_service.get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadResponse.model_validate(lead)


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    request: LeadUpdateRequest,
    db: AsyncSession = Depends(get_db),
    lead_service: LeadCaptureService = Depends(get_lead_capture_service),
):
    """
    Update a lead's status, assignment, notes, or score.
    """
    updates = request.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    lead = await lead_service.update_lead(db, lead_id, updates)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return LeadResponse.model_validate(lead)


@router.get("/{lead_id}/conversation", response_model=ConversationResponse)
async def get_lead_conversation(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the conversation history associated with a lead.
    """
    # Get lead
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if not lead.conversation_id:
        raise HTTPException(status_code=404, detail="No conversation associated with this lead")

    # Get conversation
    conv_result = await db.execute(
        select(Conversation).where(Conversation.id == lead.conversation_id)
    )
    conversation = conv_result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get messages
    messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.timestamp)
    )
    messages = messages_result.scalars().all()

    return ConversationResponse(
        id=conversation.id,
        session_id=conversation.session_id,
        started_at=conversation.started_at,
        message_count=conversation.message_count,
        lead_captured=conversation.lead_captured,
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                timestamp=m.timestamp,
                feedback=m.feedback,
                sources=m.retrieved_docs or [],
            )
            for m in messages
        ],
    )


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a lead.
    """
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    await db.delete(lead)
    await db.commit()

    return {"status": "deleted"}


@router.get("/stats/summary")
async def get_lead_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Get summary statistics about leads.
    """
    from sqlalchemy import func

    # Total leads by status
    status_result = await db.execute(
        select(Lead.status, func.count(Lead.id))
        .group_by(Lead.status)
    )
    status_counts = dict(status_result.all())

    # Average score
    avg_result = await db.execute(
        select(func.avg(Lead.score))
    )
    avg_score = avg_result.scalar() or 0

    # Total leads
    total_result = await db.execute(select(func.count(Lead.id)))
    total = total_result.scalar()

    # Leads by industry
    industry_result = await db.execute(
        select(Lead.industry, func.count(Lead.id))
        .where(Lead.industry.isnot(None))
        .group_by(Lead.industry)
        .order_by(func.count(Lead.id).desc())
        .limit(10)
    )
    industries = dict(industry_result.all())

    # High-value leads (score >= 70)
    high_value_result = await db.execute(
        select(func.count(Lead.id)).where(Lead.score >= 70)
    )
    high_value_count = high_value_result.scalar()

    return {
        "total": total,
        "by_status": status_counts,
        "average_score": round(avg_score, 1),
        "high_value_leads": high_value_count,
        "top_industries": industries,
    }
