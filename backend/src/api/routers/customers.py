"""
SBI Vishwas — Customers Router

Customer profile management with encrypted PII, search, and relationship tracking.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.encryption import encryption_service, pii_service
from src.auth.middleware import CurrentUser, PermissionChecker, get_current_active_user
from src.auth.rbac import Permission
from src.config.constants import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    AccountStatus,
    Channel,
    KYCStatus,
)
from src.database.engine import get_session
from src.database.models.customer import Customer

logger = structlog.get_logger(__name__)

router = APIRouter()


# =============================================================================
# Schemas
# =============================================================================


class CustomerCreateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    phone: str | None = None
    email: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    cif_number: str | None = None
    branch_code: str | None = None
    preferred_channel: str = Channel.BRANCH.value
    preferred_language: str = "hi"
    whatsapp_opted_in: bool = False
    sms_opted_in: bool = True
    consent_data_processing: bool = False
    consent_credit_scoring: bool = False
    segment: str | None = None


class CustomerUpdateRequest(BaseModel):
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    preferred_channel: str | None = None
    preferred_language: str | None = None
    whatsapp_opted_in: bool | None = None
    sms_opted_in: bool | None = None
    consent_data_processing: bool | None = None
    consent_credit_scoring: bool | None = None
    consent_marketing: bool | None = None
    segment: str | None = None


class CustomerResponse(BaseModel):
    id: uuid.UUID
    cif_number: str | None
    full_name: str  # Decrypted at response time
    phone_masked: str | None
    email_masked: str | None
    date_of_birth: date | None
    city: str | None
    state: str | None
    pincode: str | None
    branch_code: str | None
    kyc_status: str
    preferred_channel: str
    preferred_language: str
    whatsapp_opted_in: bool
    sms_opted_in: bool
    consent_data_processing: bool
    consent_credit_scoring: bool
    customer_since: date | None
    segment: str | None
    created_at: datetime
    account_count: int = 0

    class Config:
        from_attributes = True


class CustomerListResponse(BaseModel):
    items: list[CustomerResponse]
    total: int
    page: int
    page_size: int
    pages: int


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new customer",
    dependencies=[Depends(PermissionChecker(Permission.CUSTOMER_WRITE.value))],
)
async def create_customer(
    request: CustomerCreateRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> CustomerResponse:
    """Create a new customer profile with encrypted PII."""

    # Check for duplicate CIF
    if request.cif_number:
        existing = await db.execute(
            select(Customer).where(Customer.cif_number == request.cif_number)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Customer with CIF {request.cif_number} already exists",
            )

    # Encrypt PII
    customer = Customer(
        cif_number=request.cif_number,
        full_name_encrypted=encryption_service.encrypt(request.full_name),
        branch_code=request.branch_code or current_user.branch_code,
        date_of_birth=request.date_of_birth,
        gender=request.gender,
        city=request.city,
        state=request.state,
        pincode=request.pincode,
        preferred_channel=request.preferred_channel,
        preferred_language=request.preferred_language,
        whatsapp_opted_in=request.whatsapp_opted_in,
        sms_opted_in=request.sms_opted_in,
        consent_data_processing=request.consent_data_processing,
        consent_credit_scoring=request.consent_credit_scoring,
        customer_since=date.today(),
        segment=request.segment,
        created_by=str(current_user.id),
    )

    if request.phone:
        customer.phone_encrypted = encryption_service.encrypt(request.phone)
        customer.phone_hash = pii_service.hash_value(request.phone)

    if request.email:
        customer.email_encrypted = encryption_service.encrypt(request.email)
        customer.email_hash = pii_service.hash_value(request.email)

    if request.address:
        customer.address_encrypted = encryption_service.encrypt(request.address)

    if request.consent_data_processing:
        customer.consent_data_processing_at = datetime.now(timezone.utc)

    if request.consent_credit_scoring:
        customer.consent_credit_scoring_at = datetime.now(timezone.utc)

    db.add(customer)
    await db.flush()

    logger.info("Customer created", customer_id=str(customer.id), cif=request.cif_number)

    return _to_response(customer, request.full_name, request.phone, request.email)


@router.get(
    "",
    response_model=CustomerListResponse,
    summary="List customers",
    dependencies=[Depends(PermissionChecker(Permission.CUSTOMER_READ.value))],
)
async def list_customers(
    db: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    branch_code: str | None = None,
    kyc_status: str | None = None,
    state: str | None = None,
    search: str | None = None,
) -> CustomerListResponse:
    """List customers with filtering and pagination."""

    query = select(Customer).where(Customer.is_deleted == False)

    if branch_code:
        query = query.where(Customer.branch_code == branch_code)
    if kyc_status:
        query = query.where(Customer.kyc_status == kyc_status)
    if state:
        query = query.where(Customer.state == state)
    if search:
        # Search by CIF or hashed phone/email
        phone_hash = pii_service.hash_value(search)
        email_hash = pii_service.hash_value(search)
        query = query.where(
            or_(
                Customer.cif_number.ilike(f"%{search}%"),
                Customer.phone_hash == phone_hash,
                Customer.email_hash == email_hash,
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Customer.created_at.desc())

    result = await db.execute(query)
    customers = result.scalars().all()

    items = []
    for c in customers:
        try:
            full_name = encryption_service.decrypt(c.full_name_encrypted)
        except Exception:
            full_name = "[Decryption Error]"

        phone_masked = None
        if c.phone_encrypted:
            try:
                phone = encryption_service.decrypt(c.phone_encrypted)
                phone_masked = pii_service.mask_phone(phone)
            except Exception:
                phone_masked = "XXXXXX****"

        email_masked = None
        if c.email_encrypted:
            try:
                email = encryption_service.decrypt(c.email_encrypted)
                email_masked = pii_service.mask_email(email)
            except Exception:
                email_masked = "***@***.***"

        items.append(_to_response(c, full_name, phone_masked, email_masked, masked=True))

    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return CustomerListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Get customer by ID",
    dependencies=[Depends(PermissionChecker(Permission.CUSTOMER_READ.value))],
)
async def get_customer(
    customer_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> CustomerResponse:
    """Get a customer profile by ID with decrypted PII (masked)."""

    result = await db.execute(
        select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    full_name = encryption_service.decrypt(customer.full_name_encrypted)
    phone_masked = None
    if customer.phone_encrypted:
        phone = encryption_service.decrypt(customer.phone_encrypted)
        phone_masked = pii_service.mask_phone(phone)

    email_masked = None
    if customer.email_encrypted:
        email = encryption_service.decrypt(customer.email_encrypted)
        email_masked = pii_service.mask_email(email)

    return _to_response(customer, full_name, phone_masked, email_masked, masked=True)


@router.patch(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Update customer",
    dependencies=[Depends(PermissionChecker(Permission.CUSTOMER_WRITE.value))],
)
async def update_customer(
    customer_id: uuid.UUID,
    request: CustomerUpdateRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> CustomerResponse:
    """Update customer profile fields."""

    result = await db.execute(
        select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    update_data = request.model_dump(exclude_unset=True)

    # Handle encrypted fields
    if "phone" in update_data and update_data["phone"]:
        customer.phone_encrypted = encryption_service.encrypt(update_data.pop("phone"))
        customer.phone_hash = pii_service.hash_value(request.phone)
    elif "phone" in update_data:
        update_data.pop("phone")

    if "email" in update_data and update_data["email"]:
        customer.email_encrypted = encryption_service.encrypt(update_data.pop("email"))
        customer.email_hash = pii_service.hash_value(request.email)
    elif "email" in update_data:
        update_data.pop("email")

    if "address" in update_data and update_data["address"]:
        customer.address_encrypted = encryption_service.encrypt(update_data.pop("address"))
    elif "address" in update_data:
        update_data.pop("address")

    # Handle consent timestamps
    if "consent_data_processing" in update_data and update_data["consent_data_processing"]:
        customer.consent_data_processing_at = datetime.now(timezone.utc)
    if "consent_credit_scoring" in update_data and update_data["consent_credit_scoring"]:
        customer.consent_credit_scoring_at = datetime.now(timezone.utc)

    # Apply remaining fields
    for key, value in update_data.items():
        if hasattr(customer, key):
            setattr(customer, key, value)

    customer.updated_by = str(current_user.id)

    await db.flush()

    full_name = encryption_service.decrypt(customer.full_name_encrypted)
    logger.info("Customer updated", customer_id=str(customer_id))

    return _to_response(customer, full_name, None, None, masked=True)


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete customer",
    dependencies=[Depends(PermissionChecker(Permission.CUSTOMER_DELETE.value))],
)
async def delete_customer(
    customer_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Soft-delete a customer (DPDP right to erasure — marks as deleted)."""

    result = await db.execute(
        select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    customer.is_deleted = True
    customer.deleted_at = datetime.now(timezone.utc)
    customer.updated_by = str(current_user.id)

    logger.info("Customer soft-deleted", customer_id=str(customer_id))


# =============================================================================
# Helpers
# =============================================================================


def _to_response(
    customer: Customer,
    full_name: str,
    phone: str | None,
    email: str | None,
    masked: bool = False,
) -> CustomerResponse:
    """Convert a Customer model to a response with decrypted/masked PII."""
    account_count = len(customer.accounts) if customer.accounts else 0

    return CustomerResponse(
        id=customer.id,
        cif_number=customer.cif_number,
        full_name=full_name,
        phone_masked=phone,
        email_masked=email,
        date_of_birth=customer.date_of_birth,
        city=customer.city,
        state=customer.state,
        pincode=customer.pincode,
        branch_code=customer.branch_code,
        kyc_status=customer.kyc_status,
        preferred_channel=customer.preferred_channel,
        preferred_language=customer.preferred_language,
        whatsapp_opted_in=customer.whatsapp_opted_in,
        sms_opted_in=customer.sms_opted_in,
        consent_data_processing=customer.consent_data_processing,
        consent_credit_scoring=customer.consent_credit_scoring,
        customer_since=customer.customer_since,
        segment=customer.segment,
        created_at=customer.created_at,
        account_count=account_count,
    )
