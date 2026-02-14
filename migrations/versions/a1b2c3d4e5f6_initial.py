"""initial

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2024-02-14 12:00:00.000000

"""
"""integrations and triggers

Revision ID: 6cd7f1390221
Revises: af05779232de
Create Date: 2026-02-04 07:23:44.404449

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6cd7f1390221'
down_revision: Union[str, None] = 'af05779232de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create new tables
    op.create_table('connections',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('provider_key', sa.String(length=64), nullable=False),
    sa.Column('auth_schema_key', sa.String(length=64), nullable=False),
    sa.Column('encrypted_credentials', sa.Text(), nullable=False),
    sa.Column('encrypted_token', sa.Text(), nullable=True),
    sa.Column('connection_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('connection_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('auth_status', sa.String(length=32), nullable=False, server_default='valid'),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'),nullable=True),
    sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_validated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_connections_auth_schema_key'), 'connections', ['auth_schema_key'], unique=False)
    op.create_index(op.f('ix_connections_deleted_at'), 'connections', ['deleted_at'], unique=False)
    op.create_index(op.f('ix_connections_id'), 'connections', ['id'], unique=False)
    op.create_index(op.f('ix_connections_provider_key'), 'connections', ['provider_key'], unique=False)
    op.create_index(op.f('ix_connections_auth_status'), 'connections', ['auth_status'], unique=False)
    op.create_index(op.f('ix_connections_is_active'), 'connections', ['is_active'], unique=False)
    op.create_index('ix_connections_connection_metadata_gin', 'connections', ['connection_metadata'], unique=False, postgresql_using='gin')
    op.create_table('tool_bindings',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('agent_id', sa.UUID(), nullable=False),
    sa.Column('connection_id', sa.UUID(), nullable=False),
    sa.Column('provider_key', sa.String(length=64), nullable=False),
    sa.Column('tool_key', sa.String(length=128), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['connection_id'], ['connections.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('agent_id', 'tool_key', name='uq_agent_tool_key')
    )
    op.create_index(op.f('ix_tool_bindings_agent_id'), 'tool_bindings', ['agent_id'], unique=False)
    op.create_index(op.f('ix_tool_bindings_connection_id'), 'tool_bindings', ['connection_id'], unique=False)
    op.create_index(op.f('ix_tool_bindings_id'), 'tool_bindings', ['id'], unique=False)
    op.create_index(op.f('ix_tool_bindings_provider_key'), 'tool_bindings', ['provider_key'], unique=False)
    op.create_index(op.f('ix_tool_bindings_tool_key'), 'tool_bindings', ['tool_key'], unique=False)
    op.create_table('task_sources',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('agent_id', sa.UUID(), nullable=False),
    sa.Column('connection_id', sa.UUID(), nullable=False),
    sa.Column('provider_key', sa.String(length=64), nullable=False),
    sa.Column('trigger_key', sa.String(length=128), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('resource_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
    sa.Column('filter_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
    sa.Column('schedule_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
    sa.Column('processing_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
    sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
    sa.Column('status', sa.String(length=32), nullable=False, server_default='ok'),
    sa.Column('cursor', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
    sa.Column('task_source_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
    sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('last_error', sa.Text(), nullable=True),
    sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['connection_id'], ['connections.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_sources_agent_id'), 'task_sources', ['agent_id'], unique=False)
    op.create_index(op.f('ix_task_sources_connection_id'), 'task_sources', ['connection_id'], unique=False)
    op.create_index(op.f('ix_task_sources_id'), 'task_sources', ['id'], unique=False)
    op.create_index(op.f('ix_task_sources_provider_key'), 'task_sources', ['provider_key'], unique=False)
    op.create_index(op.f('ix_task_sources_trigger_key'), 'task_sources', ['trigger_key'], unique=False)
    op.create_index(op.f('ix_task_sources_enabled'), 'task_sources', ['enabled'], unique=False)
    op.create_index(op.f('ix_task_sources_status'), 'task_sources', ['status'], unique=False)
    op.create_index(op.f('ix_task_sources_deleted_at'), 'task_sources', ['deleted_at'], unique=False)
    op.create_table('event_inbox',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('task_source_id', sa.UUID(), nullable=False),
    sa.Column('external_event_id', sa.String(length=255), nullable=False),
    sa.Column('dedupe_key', sa.String(length=255), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
    sa.Column('event_inbox_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
    sa.Column('status', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{"state": "pending", "attempts": 0}'),
    sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['task_source_id'], ['task_sources.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('dedupe_key', name='uq_event_inbox_dedupe_key')
    )
    op.create_index(op.f('ix_event_inbox_task_source_id'), 'event_inbox', ['task_source_id'], unique=False)
    op.create_index(op.f('ix_event_inbox_dedupe_key'), 'event_inbox', ['dedupe_key'], unique=False)
    op.create_index(op.f('ix_event_inbox_created_at'), 'event_inbox', ['created_at'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # Step 1: Drop old/legacy tables first (if they exist from previous migrations)
    # CASCADE automatically drops all indexes, constraints, and dependent objects
    op.execute("DROP TABLE IF EXISTS agent_tool_bindings CASCADE")
    op.execute("DROP TABLE IF EXISTS trigger_inbox CASCADE")
    op.execute("DROP TABLE IF EXISTS agent_triggers CASCADE")
    op.execute("DROP TABLE IF EXISTS triggers CASCADE")
    op.execute("DROP TABLE IF EXISTS tools CASCADE")
    op.execute("DROP TABLE IF EXISTS integration_catalogs CASCADE")
    
    # Step 2: Drop new tables (created by this migration)
    op.drop_index(op.f('ix_event_inbox_created_at'), table_name='event_inbox')
    op.drop_index(op.f('ix_event_inbox_dedupe_key'), table_name='event_inbox')
    op.drop_index(op.f('ix_event_inbox_task_source_id'), table_name='event_inbox')
    op.drop_table('event_inbox')
    op.drop_index(op.f('ix_task_sources_deleted_at'), table_name='task_sources')
    op.drop_index(op.f('ix_task_sources_status'), table_name='task_sources')
    op.drop_index(op.f('ix_task_sources_enabled'), table_name='task_sources')
    op.drop_index(op.f('ix_task_sources_trigger_key'), table_name='task_sources')
    op.drop_index(op.f('ix_task_sources_provider_key'), table_name='task_sources')
    op.drop_index(op.f('ix_task_sources_id'), table_name='task_sources')
    op.drop_index(op.f('ix_task_sources_connection_id'), table_name='task_sources')
    op.drop_index(op.f('ix_task_sources_agent_id'), table_name='task_sources')
    op.drop_table('task_sources')
    op.drop_index(op.f('ix_tool_bindings_tool_key'), table_name='tool_bindings')
    op.drop_index(op.f('ix_tool_bindings_provider_key'), table_name='tool_bindings')
    op.drop_index(op.f('ix_tool_bindings_id'), table_name='tool_bindings')
    op.drop_index(op.f('ix_tool_bindings_connection_id'), table_name='tool_bindings')
    op.drop_index(op.f('ix_tool_bindings_agent_id'), table_name='tool_bindings')
    op.drop_table('tool_bindings')
    op.drop_index('ix_connections_connection_metadata_gin', table_name='connections', postgresql_using='gin')
    op.drop_index(op.f('ix_connections_is_active'), table_name='connections')
    op.drop_index(op.f('ix_connections_auth_status'), table_name='connections')
    op.drop_index(op.f('ix_connections_provider_key'), table_name='connections')
    op.drop_index(op.f('ix_connections_id'), table_name='connections')
    op.drop_index(op.f('ix_connections_deleted_at'), table_name='connections')
    op.drop_index(op.f('ix_connections_auth_schema_key'), table_name='connections')
    op.drop_table('connections')
    # ### end Alembic commands ###