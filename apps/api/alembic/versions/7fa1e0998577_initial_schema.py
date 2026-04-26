"""initial schema

Revision ID: 7fa1e0998577
Revises: 
Create Date: 2026-04-06 01:52:01.855618
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7fa1e0998577'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'legal_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('short_code', sa.String(length=50), nullable=False),
        sa.Column('jurisdiction', sa.String(length=100), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('version_label', sa.String(length=100), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_legal_documents_id', 'legal_documents', ['id'])
    op.create_index('ix_legal_documents_short_code', 'legal_documents', ['short_code'], unique=True)
    op.create_index('ix_legal_documents_title', 'legal_documents', ['title'])

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('NLS_STUDENT', 'LAWYER', 'POLICE', 'ADMIN', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_role', 'users', ['role'])

    op.create_table(
        'conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('mode', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_conversations_id', 'conversations', ['id'])
    op.create_index('ix_conversations_mode', 'conversations', ['mode'])
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'])

    op.create_table(
        'legal_chunks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('section_label', sa.String(length=100), nullable=True),
        sa.Column('citation', sa.String(length=255), nullable=False),
        sa.Column('topic', sa.String(length=100), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),

        # ✅ FIXED HERE (NO VECTOR)
        sa.Column('embedding', sa.Text(), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['legal_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_legal_chunks_citation', 'legal_chunks', ['citation'])
    op.create_index('ix_legal_chunks_document_id', 'legal_chunks', ['document_id'])
    op.create_index('ix_legal_chunks_id', 'legal_chunks', ['id'])
    op.create_index('ix_legal_chunks_section_label', 'legal_chunks', ['section_label'])
    op.create_index('ix_legal_chunks_topic', 'legal_chunks', ['topic'])

    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('ix_messages_id', 'messages', ['id'])


def downgrade() -> None:
    op.drop_table('messages')
    op.drop_table('legal_chunks')
    op.drop_table('conversations')
    op.drop_table('users')
    op.drop_table('legal_documents')