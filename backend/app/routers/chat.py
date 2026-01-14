"""Chat API endpoints for Aurora EDC AI Assistant."""
import logging
import uuid
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Conversation, Message, get_db
from app.models.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationResponse,
    MessageResponse,
    MessageFeedbackRequest,
)
from app.services.llm import get_llm_service, LLMService
from app.services.rag import get_rag_service, RAGService
from app.services.lead_capture import get_lead_capture_service, LeadCaptureService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    rag_service: RAGService = Depends(get_rag_service),
    lead_service: LeadCaptureService = Depends(get_lead_capture_service),
):
    """
    Send a message and get an AI response.

    This endpoint handles the main chat interaction:
    1. Creates or continues a conversation
    2. Retrieves relevant context from the knowledge base
    3. Generates a response using Claude
    4. Analyzes for lead capture opportunities
    5. Stores the conversation history
    """
    # Get or create conversation
    conversation = await _get_or_create_conversation(
        db=db,
        conversation_id=request.conversation_id,
        session_id=request.session_id,
        http_request=http_request,
    )

    # Store user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
    )
    db.add(user_message)
    await db.commit()

    # Get conversation history
    history = await _get_conversation_history(db, conversation.id)

    # Retrieve relevant context
    context = rag_service.get_context_for_query(request.message)
    sources = _extract_sources_from_context(context)

    # Generate response
    messages = [{"role": m["role"], "content": m["content"]} for m in history]
    response_text = await llm_service.generate_response(
        messages=messages,
        context=context,
        stream=False,
    )

    # Store assistant message
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=response_text,
        retrieved_docs=sources,
    )
    db.add(assistant_message)

    # Update conversation stats
    conversation.message_count = len(history) + 1

    # Analyze for lead intent
    lead_analysis = await llm_service.detect_lead_intent(messages + [
        {"role": "assistant", "content": response_text}
    ])

    lead_form_requested = False
    suggested_actions = []

    if lead_analysis.get("should_capture") and lead_analysis.get("confidence", 0) > 0.6:
        # Check if we should prompt for more info
        should_prompt, missing_fields = lead_service.should_prompt_for_info(
            lead_analysis.get("extracted_info", {}),
            lead_analysis.get("confidence", 0),
        )
        if should_prompt:
            lead_form_requested = True
            suggested_actions = lead_analysis.get("suggested_questions", [])

        # If we have enough info, create the lead
        extracted = lead_analysis.get("extracted_info", {})
        if extracted.get("email") or (extracted.get("company_name") and extracted.get("contact_name")):
            await lead_service.create_lead(
                db=db,
                lead_data=extracted,
                conversation_id=conversation.id,
            )

    await db.commit()

    return ChatMessageResponse(
        message=response_text,
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        sources=sources,
        lead_form_requested=lead_form_requested,
        suggested_actions=suggested_actions,
    )


@router.post("/message/stream")
async def send_message_stream(
    request: ChatMessageRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    Send a message and stream the AI response.

    Returns a Server-Sent Events stream of the response.
    """
    # Get or create conversation
    conversation = await _get_or_create_conversation(
        db=db,
        conversation_id=request.conversation_id,
        session_id=request.session_id,
        http_request=http_request,
    )

    # Store user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
    )
    db.add(user_message)
    await db.commit()

    # Get conversation history
    history = await _get_conversation_history(db, conversation.id)

    # Retrieve relevant context
    context = rag_service.get_context_for_query(request.message)

    # Prepare messages for LLM
    messages = [{"role": m["role"], "content": m["content"]} for m in history]

    async def generate_stream():
        """Generator for SSE stream."""
        full_response = []
        try:
            # Send conversation ID first
            yield f"data: {{'type': 'start', 'conversation_id': '{conversation.id}'}}\n\n"

            # Stream response
            async for chunk in await llm_service.generate_response(
                messages=messages,
                context=context,
                stream=True,
            ):
                full_response.append(chunk)
                # Escape for JSON
                escaped_chunk = chunk.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
                yield f"data: {{\"type\": \"chunk\", \"content\": \"{escaped_chunk}\"}}\n\n"

            # Store complete response
            complete_text = "".join(full_response)
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=complete_text,
            )
            db.add(assistant_message)
            conversation.message_count = len(history) + 1
            await db.commit()

            yield f"data: {{\"type\": \"end\", \"message_id\": \"{assistant_message.id}\"}}\n\n"

        except Exception as e:
            logger.error(f"Error in stream: {e}")
            yield f"data: {{\"type\": \"error\", \"message\": \"An error occurred\"}}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversation/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a conversation with all its messages."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get messages
    messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
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


@router.post("/feedback")
async def submit_feedback(
    request: MessageFeedbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit feedback (thumbs up/down) on a message."""
    result = await db.execute(
        select(Message).where(Message.id == request.message_id)
    )
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    message.feedback = request.feedback
    await db.commit()

    return {"status": "ok", "feedback": request.feedback}


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation and all its messages."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.delete(conversation)
    await db.commit()

    return {"status": "deleted"}


# Helper functions

async def _get_or_create_conversation(
    db: AsyncSession,
    conversation_id: Optional[uuid.UUID],
    session_id: Optional[str],
    http_request: Request,
) -> Conversation:
    """Get existing conversation or create a new one."""
    if conversation_id:
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            return conversation

    # Create new conversation
    conversation = Conversation(
        session_id=session_id or str(uuid.uuid4()),
        source="api",
        user_agent=http_request.headers.get("user-agent"),
        ip_address=http_request.client.host if http_request.client else None,
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def _get_conversation_history(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    limit: int = 20,
) -> list:
    """Get recent conversation history."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.timestamp.desc())
        .limit(limit)
    )
    messages = result.scalars().all()

    # Return in chronological order
    return [
        {"role": m.role, "content": m.content}
        for m in reversed(messages)
    ]


def _extract_sources_from_context(context: str) -> list:
    """Extract source citations from context string."""
    sources = []
    if not context:
        return sources

    # Parse [Source N: Title - URL] format
    import re
    pattern = r'\[Source \d+: ([^\]]+)\]'
    matches = re.findall(pattern, context)

    for match in matches:
        parts = match.split(" - ", 1)
        sources.append({
            "title": parts[0].strip(),
            "source": parts[1].strip() if len(parts) > 1 else "Aurora EDC Knowledge Base",
        })

    return sources
