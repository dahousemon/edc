"""Pydantic schemas for API request/response validation."""
from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ============= Chat Schemas =============

class ChatMessageRequest(BaseModel):
    """Incoming chat message from user."""
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[UUID] = None
    session_id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    """Response to a chat message."""
    message: str
    conversation_id: UUID
    message_id: UUID
    sources: List[dict] = []
    lead_form_requested: bool = False
    suggested_actions: List[str] = []


class ConversationResponse(BaseModel):
    """Full conversation with messages."""
    id: UUID
    session_id: Optional[str]
    started_at: datetime
    message_count: int
    messages: List["MessageResponse"]
    lead_captured: bool

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Individual message in a conversation."""
    id: UUID
    role: str
    content: str
    timestamp: datetime
    feedback: Optional[str]
    sources: List[dict] = []

    class Config:
        from_attributes = True


class MessageFeedbackRequest(BaseModel):
    """Feedback on a message."""
    message_id: UUID
    feedback: str = Field(..., pattern="^(thumbs_up|thumbs_down)$")


# ============= Lead Schemas =============

class LeadCaptureRequest(BaseModel):
    """Lead information captured from chat."""
    conversation_id: Optional[UUID] = None
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    industry: Optional[str] = None
    space_requirements: Optional[str] = None
    timeline: Optional[str] = None
    budget: Optional[str] = None
    location_preference: Optional[str] = None
    notes: Optional[str] = None


class LeadResponse(BaseModel):
    """Lead information response."""
    id: UUID
    company_name: Optional[str]
    contact_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    industry: Optional[str]
    space_requirements: Optional[str]
    timeline: Optional[str]
    score: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeadUpdateRequest(BaseModel):
    """Update lead status or information."""
    status: Optional[str] = None
    assigned_to: Optional[UUID] = None
    notes: Optional[str] = None
    score: Optional[int] = Field(None, ge=0, le=100)


class LeadListResponse(BaseModel):
    """Paginated list of leads."""
    leads: List[LeadResponse]
    total: int
    page: int
    page_size: int


# ============= Property Schemas =============

class PropertySearchRequest(BaseModel):
    """Property search parameters."""
    query: Optional[str] = None
    property_type: Optional[str] = None
    min_sqft: Optional[int] = None
    max_sqft: Optional[int] = None
    max_price_per_sqft: Optional[float] = None
    features: Optional[List[str]] = None
    zoning: Optional[str] = None


class PropertyResponse(BaseModel):
    """Property information."""
    id: UUID
    name: str
    address: str
    city: str
    state: str
    property_type: Optional[str]
    total_sqft: Optional[int]
    available_sqft: Optional[int]
    price_per_sqft: Optional[float]
    lease_rate: Optional[float]
    zoning: Optional[str]
    features: List[str]
    description: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    is_available: bool

    class Config:
        from_attributes = True


class PropertyListResponse(BaseModel):
    """List of properties."""
    properties: List[PropertyResponse]
    total: int


# ============= Analytics Schemas =============

class AnalyticsOverview(BaseModel):
    """Overview analytics for dashboard."""
    total_conversations: int
    total_messages: int
    leads_captured: int
    conversion_rate: float
    avg_messages_per_conversation: float
    top_topics: List[dict]
    questions_by_category: dict


class ConversationAnalytics(BaseModel):
    """Analytics for a specific time period."""
    period_start: datetime
    period_end: datetime
    conversations_count: int
    leads_count: int
    messages_count: int
    avg_sentiment: Optional[float]
    top_questions: List[str]
    content_gaps: List[str]


# ============= Knowledge Base Schemas =============

class DocumentUploadRequest(BaseModel):
    """Document upload for knowledge base."""
    title: str
    content: str
    source: Optional[str] = None
    category: str
    doc_type: str = "manual"
    metadata: dict = {}


class DocumentResponse(BaseModel):
    """Document in knowledge base."""
    id: UUID
    title: str
    source: Optional[str]
    category: Optional[str]
    doc_type: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """List of documents."""
    documents: List[DocumentResponse]
    total: int


# ============= User Schemas =============

class UserResponse(BaseModel):
    """User information."""
    id: UUID
    email: str
    name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


# ============= General Schemas =============

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    environment: str
    database: str
    vector_store: str


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
