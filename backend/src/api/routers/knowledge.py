"""
SBI Vishwas — Knowledge Router

Knowledge base management, search, and policy document endpoints.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.middleware import PermissionChecker, get_current_active_user, CurrentUser
from src.auth.rbac import Permission
from src.config.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from src.database.engine import get_session
from src.database.models.domain import KnowledgeEntry, PolicyDocument, PolicyCheck

logger = structlog.get_logger(__name__)

router = APIRouter()


class KnowledgeEntryResponse(BaseModel):
    id: uuid.UUID
    title: str
    category: str
    source_type: str
    content: str
    summary: str | None
    version: str
    is_active: bool
    is_embedded: bool
    chunk_count: int
    tags: list[str] | None
    language: str
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=500)
    category: str
    source_type: str = "policy"
    content: str = Field(min_length=10)
    summary: str | None = None
    source_url: str | None = None
    tags: list[str] | None = None
    language: str = "en"


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=2)
    category: str | None = None
    limit: int = Field(10, ge=1, le=50)


class KnowledgeSearchResult(BaseModel):
    id: uuid.UUID
    title: str
    category: str
    content_snippet: str
    relevance_score: float
    citation: str | None


class PolicyCheckResponse(BaseModel):
    id: uuid.UUID
    check_type: str
    statement_checked: str
    is_deviation: bool
    deviation_type: str | None
    severity: str | None
    confidence: float
    policy_citation: str | None
    correct_policy: str | None
    branch_code: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeListResponse(BaseModel):
    items: list[KnowledgeEntryResponse]
    total: int
    page: int
    page_size: int


@router.post(
    "/entries",
    response_model=KnowledgeEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a knowledge entry",
    dependencies=[Depends(PermissionChecker(Permission.KNOWLEDGE_WRITE.value))],
)
async def create_knowledge_entry(
    request: KnowledgeCreateRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> KnowledgeEntryResponse:
    """Add a new entry to the knowledge base."""
    entry = KnowledgeEntry(
        title=request.title,
        category=request.category,
        source_type=request.source_type,
        content=request.content,
        summary=request.summary,
        source_url=request.source_url,
        tags=request.tags,
        language=request.language,
        created_by=str(current_user.id),
    )
    db.add(entry)
    await db.flush()

    logger.info("Knowledge entry created", entry_id=str(entry.id), title=request.title)
    return KnowledgeEntryResponse.model_validate(entry)


@router.get(
    "/entries",
    response_model=KnowledgeListResponse,
    summary="List knowledge entries",
    dependencies=[Depends(PermissionChecker(Permission.KNOWLEDGE_READ.value))],
)
async def list_knowledge_entries(
    db: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    category: str | None = None,
    source_type: str | None = None,
    is_active: bool = True,
) -> KnowledgeListResponse:
    """List knowledge base entries with filtering."""
    query = select(KnowledgeEntry).where(
        KnowledgeEntry.is_deleted == False,
        KnowledgeEntry.is_active == is_active,
    )

    if category:
        query = query.where(KnowledgeEntry.category == category)
    if source_type:
        query = query.where(KnowledgeEntry.source_type == source_type)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(KnowledgeEntry.created_at.desc())

    result = await db.execute(query)
    entries = result.scalars().all()

    return KnowledgeListResponse(
        items=[KnowledgeEntryResponse.model_validate(e) for e in entries],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/search",
    response_model=list[KnowledgeSearchResult],
    summary="Search knowledge base",
    dependencies=[Depends(PermissionChecker(Permission.KNOWLEDGE_READ.value))],
)
async def search_knowledge(
    request: KnowledgeSearchRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[KnowledgeSearchResult]:
    """
    Search the knowledge base. Uses semantic search (Qdrant) when available,
    falls back to full-text SQL search.
    """
    # SQL-based search fallback (semantic search via RAG engine is in Phase 3)
    query = (
        select(KnowledgeEntry)
        .where(
            KnowledgeEntry.is_deleted == False,
            KnowledgeEntry.is_active == True,
            KnowledgeEntry.content.ilike(f"%{request.query}%"),
        )
        .limit(request.limit)
    )

    if request.category:
        query = query.where(KnowledgeEntry.category == request.category)

    result = await db.execute(query)
    entries = result.scalars().all()

    return [
        KnowledgeSearchResult(
            id=entry.id,
            title=entry.title,
            category=entry.category,
            content_snippet=entry.content[:300] + "..." if len(entry.content) > 300 else entry.content,
            relevance_score=0.8,  # Placeholder — replaced by vector similarity in Phase 3
            citation=f"[{entry.title}] ({entry.source_url})" if entry.source_url else f"[{entry.title}]",
        )
        for entry in entries
    ]


@router.get(
    "/policy-checks",
    response_model=list[PolicyCheckResponse],
    summary="List policy compliance checks",
    dependencies=[Depends(PermissionChecker(Permission.POLICY_CHECK_VIEW.value))],
)
async def list_policy_checks(
    db: Annotated[AsyncSession, Depends(get_session)],
    branch_code: str | None = None,
    is_deviation: bool | None = None,
    limit: int = Query(50, ge=1, le=200),
) -> list[PolicyCheckResponse]:
    """List policy compliance checks — the branch dashboard data source."""
    query = select(PolicyCheck).where(PolicyCheck.is_deleted == False)

    if branch_code:
        query = query.where(PolicyCheck.branch_code == branch_code)
    if is_deviation is not None:
        query = query.where(PolicyCheck.is_deviation == is_deviation)

    query = query.order_by(PolicyCheck.created_at.desc()).limit(limit)

    result = await db.execute(query)
    checks = result.scalars().all()

    return [PolicyCheckResponse.model_validate(c) for c in checks]
