"""SQLAlchemy database models for Aurora EDC AI Assistant."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class User(Base):
    """Staff users for the internal portal."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    role = Column(String(50), default="staff")  # admin, staff
    azure_id = Column(String(255), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assigned_leads = relationship("Lead", back_populates="assigned_user")


class Conversation(Base):
    """Chat conversation sessions."""
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    message_count = Column(Integer, default=0)
    lead_captured = Column(Boolean, default=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True)
    topics = Column(JSON, default=list)  # Extracted topics discussed
    sentiment_score = Column(Float, nullable=True)
    source = Column(String(50), default="website")  # website, widget, api
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    lead = relationship("Lead", back_populates="conversation", foreign_keys=[lead_id])


class Message(Base):
    """Individual messages within a conversation."""
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    tokens_used = Column(Integer, nullable=True)
    retrieved_docs = Column(JSON, nullable=True)  # Documents used for RAG
    feedback = Column(String(20), nullable=True)  # thumbs_up, thumbs_down
    metadata = Column(JSON, default=dict)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class Lead(Base):
    """Captured leads from chat interactions."""
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=True)
    company_name = Column(String(200), nullable=True)
    contact_name = Column(String(200), nullable=True)
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    industry = Column(String(100), nullable=True)
    space_requirements = Column(Text, nullable=True)
    timeline = Column(String(100), nullable=True)
    budget = Column(String(100), nullable=True)
    location_preference = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    score = Column(Integer, default=0)  # 1-100 lead score
    status = Column(String(50), default="new")  # new, contacted, qualified, converted, closed
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    source = Column(String(50), default="chatbot")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="lead", foreign_keys=[Conversation.lead_id])
    assigned_user = relationship("User", back_populates="assigned_leads")


class Document(Base):
    """Knowledge base documents."""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(500), nullable=True)  # URL or file path
    category = Column(String(100), nullable=True)  # incentives, permits, properties, demographics
    doc_type = Column(String(50), nullable=True)  # webpage, pdf, csv, manual
    chunk_index = Column(Integer, default=0)
    total_chunks = Column(Integer, default=1)
    parent_doc_id = Column(UUID(as_uuid=True), nullable=True)
    embedding_id = Column(String(100), nullable=True)  # Reference to vector store
    metadata = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Analytics(Base):
    """Analytics events and metrics."""
    __tablename__ = "analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False)  # chat_started, lead_captured, question_asked
    event_data = Column(JSON, default=dict)
    conversation_id = Column(UUID(as_uuid=True), nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    session_id = Column(String(100), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Property(Base):
    """Commercial/industrial properties database."""
    __tablename__ = "properties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(300), nullable=False)
    address = Column(String(500), nullable=False)
    city = Column(String(100), default="Aurora")
    state = Column(String(50), default="CO")
    zip_code = Column(String(20), nullable=True)
    property_type = Column(String(100), nullable=True)  # industrial, office, retail, mixed-use
    total_sqft = Column(Integer, nullable=True)
    available_sqft = Column(Integer, nullable=True)
    price_per_sqft = Column(Float, nullable=True)
    lease_rate = Column(Float, nullable=True)
    zoning = Column(String(50), nullable=True)
    year_built = Column(Integer, nullable=True)
    features = Column(JSON, default=list)  # rail_access, highway_access, loading_docks, etc.
    description = Column(Text, nullable=True)
    contact_name = Column(String(200), nullable=True)
    contact_email = Column(String(200), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    listing_url = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Database engine and session
engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """Dependency for getting database sessions."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
