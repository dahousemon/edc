"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('role', sa.String(50), default='staff'),
        sa.Column('azure_id', sa.String(255), unique=True, nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Leads table
    op.create_table(
        'leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('company_name', sa.String(200), nullable=True),
        sa.Column('contact_name', sa.String(200), nullable=True),
        sa.Column('email', sa.String(200), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('space_requirements', sa.Text(), nullable=True),
        sa.Column('timeline', sa.String(100), nullable=True),
        sa.Column('budget', sa.String(100), nullable=True),
        sa.Column('location_preference', sa.String(200), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('score', sa.Integer(), default=0),
        sa.Column('status', sa.String(50), default='new'),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('source', sa.String(50), default='chatbot'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', sa.String(100), index=True),
        sa.Column('started_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('message_count', sa.Integer(), default=0),
        sa.Column('lead_captured', sa.Boolean(), default=False),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('leads.id'), nullable=True),
        sa.Column('topics', postgresql.JSON(), default=list),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('source', sa.String(50), default='website'),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('retrieved_docs', postgresql.JSON(), nullable=True),
        sa.Column('feedback', sa.String(20), nullable=True),
        sa.Column('metadata', postgresql.JSON(), default=dict),
    )

    # Documents table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('source', sa.String(500), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('doc_type', sa.String(50), nullable=True),
        sa.Column('chunk_index', sa.Integer(), default=0),
        sa.Column('total_chunks', sa.Integer(), default=1),
        sa.Column('parent_doc_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('embedding_id', sa.String(100), nullable=True),
        sa.Column('metadata', postgresql.JSON(), default=dict),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Properties table
    op.create_table(
        'properties',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(300), nullable=False),
        sa.Column('address', sa.String(500), nullable=False),
        sa.Column('city', sa.String(100), default='Aurora'),
        sa.Column('state', sa.String(50), default='CO'),
        sa.Column('zip_code', sa.String(20), nullable=True),
        sa.Column('property_type', sa.String(100), nullable=True),
        sa.Column('total_sqft', sa.Integer(), nullable=True),
        sa.Column('available_sqft', sa.Integer(), nullable=True),
        sa.Column('price_per_sqft', sa.Float(), nullable=True),
        sa.Column('lease_rate', sa.Float(), nullable=True),
        sa.Column('zoning', sa.String(50), nullable=True),
        sa.Column('year_built', sa.Integer(), nullable=True),
        sa.Column('features', postgresql.JSON(), default=list),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('contact_name', sa.String(200), nullable=True),
        sa.Column('contact_email', sa.String(200), nullable=True),
        sa.Column('contact_phone', sa.String(50), nullable=True),
        sa.Column('listing_url', sa.String(500), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('is_available', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Analytics table
    op.create_table(
        'analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_data', postgresql.JSON(), default=dict),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now()),
    )

    # Create indexes
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('ix_leads_status', 'leads', ['status'])
    op.create_index('ix_leads_score', 'leads', ['score'])
    op.create_index('ix_documents_category', 'documents', ['category'])
    op.create_index('ix_properties_type', 'properties', ['property_type'])
    op.create_index('ix_analytics_event_type', 'analytics', ['event_type'])
    op.create_index('ix_analytics_timestamp', 'analytics', ['timestamp'])


def downgrade() -> None:
    op.drop_table('analytics')
    op.drop_table('properties')
    op.drop_table('documents')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('leads')
    op.drop_table('users')
