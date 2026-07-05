"""
SBI Vishwas — Conversations Router

Conversation management with streaming AI responses and cross-channel tracking.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.middleware import CurrentUser, PermissionChecker, get_current_active_user
from src.auth.rbac import Permission
from src.config.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, Channel
from src.database.engine import get_session
from src.database.models.conversation import Conversation, ConversationMessage

logger = structlog.get_logger(__name__)

router = APIRouter()


# =============================================================================
# Schemas
# =============================================================================


class ConversationCreateRequest(BaseModel):
    customer_id: uuid.UUID
    channel: str = Channel.WEB.value
    subject: str | None = None
    complaint_id: uuid.UUID | None = None


class MessageCreateRequest(BaseModel):
    content: str = Field(min_length=1)
    channel: str = Channel.WEB.value
    role: str = "user"
    content_type: str = "text"
    language: str | None = None
    attachments: list[dict] | None = None


class ConversationResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    channel: str
    channels_used: list[str]
    status: str
    subject: str | None
    complaint_id: uuid.UUID | None
    message_count: int
    last_message_at: datetime | None
    last_agent_type: str | None
    transfer_count: int
    resolved: bool
    satisfaction_score: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    content_type: str
    channel: str
    agent_type: str | None
    model_used: str | None
    confidence: float | None
    reasoning: str | None
    tool_calls: list[dict] | None
    language: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]
    total: int
    page: int
    page_size: int


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new conversation",
    dependencies=[Depends(PermissionChecker(Permission.CONVERSATION_WRITE.value))],
)
async def create_conversation(
    request: ConversationCreateRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ConversationResponse:
    """Start a new conversation thread for a customer."""
    conversation = Conversation(
        customer_id=request.customer_id,
        channel=request.channel,
        channels_used=[request.channel],
        status="active",
        subject=request.subject,
        complaint_id=request.complaint_id,
        created_by=str(current_user.id),
    )
    db.add(conversation)
    await db.flush()

    logger.info("Conversation started", conversation_id=str(conversation.id))

    return ConversationResponse.model_validate(conversation)


@router.get(
    "",
    response_model=ConversationListResponse,
    summary="List conversations",
    dependencies=[Depends(PermissionChecker(Permission.CONVERSATION_READ.value))],
)
async def list_conversations(
    db: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    customer_id: uuid.UUID | None = None,
    status_filter: str | None = Query(None, alias="status"),
    channel: str | None = None,
) -> ConversationListResponse:
    """List conversations with filtering and pagination."""
    query = select(Conversation).where(Conversation.is_deleted == False)

    if customer_id:
        query = query.where(Conversation.customer_id == customer_id)
    if status_filter:
        query = query.where(Conversation.status == status_filter)
    if channel:
        query = query.where(Conversation.channel == channel)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Conversation.updated_at.desc())

    result = await db.execute(query)
    conversations = result.scalars().all()

    return ConversationListResponse(
        items=[ConversationResponse.model_validate(c) for c in conversations],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get conversation",
    dependencies=[Depends(PermissionChecker(Permission.CONVERSATION_READ.value))],
)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ConversationResponse:
    """Get conversation details."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id, Conversation.is_deleted == False
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    return ConversationResponse.model_validate(conversation)


@router.get(
    "/{conversation_id}/messages",
    response_model=list[MessageResponse],
    summary="Get conversation messages",
    dependencies=[Depends(PermissionChecker(Permission.CONVERSATION_READ.value))],
)
async def get_messages(
    conversation_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(50, ge=1, le=200),
    before: uuid.UUID | None = None,
) -> list[MessageResponse]:
    """Get messages in a conversation with cursor-based pagination."""
    # Verify conversation exists
    conv_result = await db.execute(
        select(Conversation.id).where(Conversation.id == conversation_id)
    )
    if not conv_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    query = (
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at.asc())
        .limit(limit)
    )

    result = await db.execute(query)
    messages = result.scalars().all()

    return [MessageResponse.model_validate(m) for m in messages]


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message",
    dependencies=[Depends(PermissionChecker(Permission.CONVERSATION_WRITE.value))],
)
async def send_message(
    conversation_id: uuid.UUID,
    request: MessageCreateRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> MessageResponse:
    """
    Send a message in a conversation.
    If role is 'user', the system will process it through the agent pipeline.
    """
    # Verify conversation exists
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id, Conversation.is_deleted == False
        )
    )
    conversation = conv_result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    # Create message
    message = ConversationMessage(
        conversation_id=conversation_id,
        role=request.role,
        content=request.content,
        content_type=request.content_type,
        channel=request.channel,
        language=request.language,
        attachments=request.attachments,
    )
    db.add(message)

    # Update conversation
    conversation.message_count += 1
    conversation.last_message_at = datetime.now(timezone.utc)

    # Track channel usage
    if request.channel not in conversation.channels_used:
        conversation.channels_used = [*conversation.channels_used, request.channel]

    await db.flush()

    logger.info(
        "Message sent",
        conversation_id=str(conversation_id),
        role=request.role,
        channel=request.channel,
    )

    return MessageResponse.model_validate(message)
