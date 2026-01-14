"""Analytics API endpoints for Aurora EDC AI Assistant."""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Conversation, Message, Lead, Analytics, get_db
from app.models.schemas import AnalyticsOverview, ConversationAnalytics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
async def get_overview(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get overview analytics for the dashboard.
    """
    since = datetime.utcnow() - timedelta(days=days)

    # Total conversations
    conv_result = await db.execute(
        select(func.count(Conversation.id))
        .where(Conversation.started_at >= since)
    )
    total_conversations = conv_result.scalar() or 0

    # Total messages
    msg_result = await db.execute(
        select(func.count(Message.id))
        .where(Message.timestamp >= since)
    )
    total_messages = msg_result.scalar() or 0

    # Leads captured
    leads_result = await db.execute(
        select(func.count(Lead.id))
        .where(Lead.created_at >= since)
    )
    leads_captured = leads_result.scalar() or 0

    # Conversion rate
    conversion_rate = (leads_captured / total_conversations * 100) if total_conversations > 0 else 0

    # Average messages per conversation
    avg_messages = total_messages / total_conversations if total_conversations > 0 else 0

    # Top topics (from conversation topics JSON field)
    topics_result = await db.execute(
        select(Conversation.topics)
        .where(
            and_(
                Conversation.started_at >= since,
                Conversation.topics.isnot(None)
            )
        )
    )
    all_topics = topics_result.scalars().all()

    # Count topic occurrences
    topic_counts = {}
    for topics in all_topics:
        if topics:
            for topic in topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

    top_topics = [
        {"topic": topic, "count": count}
        for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    # Questions by category (simplified)
    category_result = await db.execute(
        select(Lead.industry, func.count(Lead.id))
        .where(
            and_(
                Lead.created_at >= since,
                Lead.industry.isnot(None)
            )
        )
        .group_by(Lead.industry)
    )
    questions_by_category = dict(category_result.all())

    return AnalyticsOverview(
        total_conversations=total_conversations,
        total_messages=total_messages,
        leads_captured=leads_captured,
        conversion_rate=round(conversion_rate, 2),
        avg_messages_per_conversation=round(avg_messages, 2),
        top_topics=top_topics,
        questions_by_category=questions_by_category,
    )


@router.get("/conversations/daily")
async def get_daily_conversations(
    days: int = Query(30, ge=1, le=90, description="Number of days"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get daily conversation counts for charting.
    """
    since = datetime.utcnow() - timedelta(days=days)

    # Get daily counts
    result = await db.execute(
        select(
            func.date(Conversation.started_at).label("date"),
            func.count(Conversation.id).label("count")
        )
        .where(Conversation.started_at >= since)
        .group_by(func.date(Conversation.started_at))
        .order_by(func.date(Conversation.started_at))
    )

    daily_data = [
        {"date": str(row.date), "count": row.count}
        for row in result.all()
    ]

    return {"data": daily_data}


@router.get("/leads/funnel")
async def get_lead_funnel(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """
    Get lead funnel data showing conversion at each stage.
    """
    since = datetime.utcnow() - timedelta(days=days)

    # Total conversations
    conv_result = await db.execute(
        select(func.count(Conversation.id))
        .where(Conversation.started_at >= since)
    )
    total_conversations = conv_result.scalar() or 0

    # Conversations with lead captured
    captured_result = await db.execute(
        select(func.count(Conversation.id))
        .where(
            and_(
                Conversation.started_at >= since,
                Conversation.lead_captured == True
            )
        )
    )
    leads_captured = captured_result.scalar() or 0

    # Leads by status
    status_result = await db.execute(
        select(Lead.status, func.count(Lead.id))
        .where(Lead.created_at >= since)
        .group_by(Lead.status)
    )
    status_counts = dict(status_result.all())

    funnel = {
        "conversations": total_conversations,
        "leads_captured": leads_captured,
        "contacted": status_counts.get("contacted", 0),
        "qualified": status_counts.get("qualified", 0),
        "converted": status_counts.get("converted", 0),
    }

    return funnel


@router.get("/feedback/summary")
async def get_feedback_summary(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """
    Get summary of message feedback (thumbs up/down).
    """
    since = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(Message.feedback, func.count(Message.id))
        .where(
            and_(
                Message.timestamp >= since,
                Message.feedback.isnot(None)
            )
        )
        .group_by(Message.feedback)
    )

    feedback_counts = dict(result.all())

    thumbs_up = feedback_counts.get("thumbs_up", 0)
    thumbs_down = feedback_counts.get("thumbs_down", 0)
    total = thumbs_up + thumbs_down

    return {
        "thumbs_up": thumbs_up,
        "thumbs_down": thumbs_down,
        "total_feedback": total,
        "satisfaction_rate": round((thumbs_up / total * 100) if total > 0 else 0, 1),
    }


@router.get("/questions/common")
async def get_common_questions(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Get most common questions asked by users.

    This analyzes user messages to identify frequently asked topics.
    """
    since = datetime.utcnow() - timedelta(days=days)

    # Get user messages
    result = await db.execute(
        select(Message.content)
        .where(
            and_(
                Message.timestamp >= since,
                Message.role == "user"
            )
        )
        .limit(1000)  # Limit for performance
    )

    messages = result.scalars().all()

    # Simple keyword extraction for common topics
    # In production, you'd want more sophisticated NLP
    keywords = {}
    topic_keywords = [
        "permit", "permits", "license", "licensing",
        "property", "properties", "space", "warehouse", "office",
        "incentive", "incentives", "tax", "taxes", "credit",
        "zoning", "zone", "zones",
        "manufacturing", "distribution", "logistics", "retail",
        "employee", "workforce", "workers", "hiring",
        "cost", "costs", "rate", "rates", "price",
        "location", "area", "neighborhood", "downtown",
        "transportation", "highway", "rail", "airport",
    ]

    for message in messages:
        message_lower = message.lower()
        for keyword in topic_keywords:
            if keyword in message_lower:
                keywords[keyword] = keywords.get(keyword, 0) + 1

    sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:limit]

    return {
        "common_topics": [
            {"topic": k, "count": v}
            for k, v in sorted_keywords
        ]
    }


@router.get("/content-gaps")
async def get_content_gaps(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """
    Identify potential content gaps based on negative feedback
    and unanswered questions.
    """
    since = datetime.utcnow() - timedelta(days=days)

    # Get messages with negative feedback
    result = await db.execute(
        select(Message.content, Message.conversation_id)
        .where(
            and_(
                Message.timestamp >= since,
                Message.role == "assistant",
                Message.feedback == "thumbs_down"
            )
        )
        .limit(50)
    )

    negative_responses = result.all()

    # Get the questions that preceded negative responses
    gaps = []
    for response_content, conv_id in negative_responses:
        # Get the user message before this response
        user_msg_result = await db.execute(
            select(Message.content)
            .where(
                and_(
                    Message.conversation_id == conv_id,
                    Message.role == "user"
                )
            )
            .order_by(Message.timestamp.desc())
            .limit(1)
        )
        user_msg = user_msg_result.scalar()
        if user_msg:
            gaps.append({
                "user_question": user_msg[:200],
                "assistant_response": response_content[:200],
            })

    return {
        "content_gaps": gaps[:20],
        "total_negative_feedback": len(negative_responses),
    }


@router.post("/event")
async def log_event(
    event_type: str,
    event_data: dict,
    conversation_id: Optional[str] = None,
    session_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Log an analytics event.
    """
    from uuid import UUID

    analytics = Analytics(
        event_type=event_type,
        event_data=event_data,
        conversation_id=UUID(conversation_id) if conversation_id else None,
        session_id=session_id,
    )
    db.add(analytics)
    await db.commit()

    return {"status": "logged"}
