"""
SBI Vishwas — System Constants

All configurable business constants, SLA definitions, agent parameters,
and regulatory thresholds. Nothing is hardcoded in business logic —
everything references these constants.
"""

from __future__ import annotations

from enum import Enum, IntEnum
from typing import Final


# =============================================================================
# ACCOUNT TYPES
# =============================================================================

class AccountType(str, Enum):
    """SBI account types."""
    SAVINGS = "savings"
    CURRENT = "current"
    BSBD = "bsbd"  # Basic Savings Bank Deposit
    JAN_DHAN = "jan_dhan"  # PMJDY
    SALARY = "salary"
    FIXED_DEPOSIT = "fd"
    RECURRING_DEPOSIT = "rd"
    NRI = "nri"
    PPF = "ppf"


class AccountStatus(str, Enum):
    """Account lifecycle status."""
    ACTIVE = "active"
    DORMANT = "dormant"
    INACTIVE = "inactive"
    FROZEN = "frozen"
    CLOSED = "closed"
    PENDING_ACTIVATION = "pending_activation"
    REACTIVATED = "reactivated"


class DormancyCause(str, Enum):
    """Classified causes of account dormancy (Agent 5 output)."""
    NO_DBT_LINKAGE = "no_dbt_linkage"
    LOST_ACCESS = "lost_access"
    DUPLICATE_ACCOUNT = "duplicate_account"
    SEASONAL_INCOME = "seasonal_income"
    MIGRATED = "migrated"
    NO_ONGOING_NEED = "no_ongoing_need"
    KYC_EXPIRED = "kyc_expired"
    UNKNOWN = "unknown"


# =============================================================================
# COMPLAINT / GRIEVANCE
# =============================================================================

class ComplaintStatus(str, Enum):
    """Complaint lifecycle status."""
    FILED = "filed"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    ESCALATED_L1 = "escalated_l1"
    ESCALATED_L2 = "escalated_l2"
    ESCALATED_OMBUDSMAN = "escalated_ombudsman"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


class ComplaintCategory(str, Enum):
    """Complaint categories per RBI classification."""
    ACCOUNT_OPENING = "account_opening"
    FORCED_BUNDLING = "forced_bundling"
    SERVICE_DELAY = "service_delay"
    DIGITAL_CHANNEL = "digital_channel"
    CARD_ISSUE = "card_issue"
    TRANSACTION_DISPUTE = "transaction_dispute"
    COMMUNICATION_FAILURE = "communication_failure"
    STAFF_BEHAVIOR = "staff_behavior"
    KYC_ISSUE = "kyc_issue"
    LOAN_RELATED = "loan_related"
    INSURANCE_RELATED = "insurance_related"
    OTHER = "other"


class EscalationLevel(IntEnum):
    """Internal escalation hierarchy."""
    BRANCH = 0
    LEVEL_1 = 1  # Branch Manager
    LEVEL_2 = 2  # Regional Manager
    LEVEL_3 = 3  # Circle Head
    OMBUDSMAN = 4  # RBI Banking Ombudsman


# =============================================================================
# AGENTS
# =============================================================================

class AgentType(str, Enum):
    """All agent types in the system."""
    # Phase A — Onboarding Advocate
    JOURNEY_TRACKER = "journey_tracker"
    POLICY_COMPLIANCE = "policy_compliance"
    PROACTIVE_COMMUNICATION = "proactive_communication"
    ESCALATION_ADVOCATE = "escalation_advocate"

    # Phase B — Reactivation & Credit Readiness
    DIAGNOSIS = "diagnosis"
    READINESS = "readiness"
    CHANNEL_JOURNEY = "channel_journey"
    GRADUATION = "graduation"

    # Shared / Infrastructure
    SUPERVISOR = "supervisor"
    PLANNER = "planner"
    REFLECTION = "reflection"
    AUDIT_GUARDIAN = "audit_guardian"
    CONVERSATION = "conversation"
    KNOWLEDGE = "knowledge"
    NOTIFICATION = "notification"


class AgentStatus(str, Enum):
    """Agent execution status."""
    PENDING = "pending"
    RUNNING = "running"
    WAITING_HUMAN = "waiting_human"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


# =============================================================================
# WORKFLOW
# =============================================================================

class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"


class ApprovalStatus(str, Enum):
    """Human approval decision status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ESCALATED = "escalated"


# =============================================================================
# CHANNELS
# =============================================================================

class Channel(str, Enum):
    """Customer contact channels."""
    BRANCH = "branch"
    CALL_CENTER = "call_center"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"
    YONO = "yono"
    IVR = "ivr"
    USSD = "ussd"
    BANK_MITRA = "bank_mitra"
    WEB = "web"


# =============================================================================
# CREDIT PRODUCTS
# =============================================================================

class CreditProduct(str, Enum):
    """Credit products for graduation path."""
    KCC = "kcc"  # Kisan Credit Card
    KCC_TOPUP = "kcc_topup"
    MUDRA = "mudra"
    PERSONAL_LOAN = "personal_loan"
    OVERDRAFT = "overdraft"


# =============================================================================
# KYC
# =============================================================================

class KYCStatus(str, Enum):
    """KYC verification status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    EXPIRED = "expired"
    FAILED = "failed"
    PENDING_REVIEW = "pending_review"


# =============================================================================
# NOTIFICATION
# =============================================================================

class NotificationType(str, Enum):
    """Notification types."""
    ACCOUNT_OPENED = "account_opened"
    CARD_DISPATCHED = "card_dispatched"
    COMPLAINT_ACKNOWLEDGED = "complaint_acknowledged"
    COMPLAINT_RESOLVED = "complaint_resolved"
    COMPLAINT_ESCALATED = "complaint_escalated"
    KYC_REMINDER = "kyc_reminder"
    DORMANCY_REACTIVATION = "dormancy_reactivation"
    CREDIT_READINESS = "credit_readiness"
    POLICY_UPDATE = "policy_update"
    GENERAL = "general"


class NotificationStatus(str, Enum):
    """Notification delivery status."""
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


# =============================================================================
# POLICY COMPLIANCE
# =============================================================================

class PolicyDeviationType(str, Enum):
    """Types of policy deviations detected by Agent 2."""
    FORCED_BUNDLING = "forced_bundling"
    INCORRECT_DOCUMENT_DEMAND = "incorrect_document_demand"
    INCORRECT_FEE = "incorrect_fee"
    PROCESS_VIOLATION = "process_violation"
    UNAUTHORIZED_REQUIREMENT = "unauthorized_requirement"
    MISLEADING_INFORMATION = "misleading_information"


class PolicySeverity(str, Enum):
    """Severity of policy deviation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# MEMORY TYPES
# =============================================================================

class MemoryType(str, Enum):
    """Agent memory categories."""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    CONVERSATION = "conversation"
    RELATIONSHIP = "relationship"
    KNOWLEDGE = "knowledge"


# =============================================================================
# AUDIT
# =============================================================================

class AuditAction(str, Enum):
    """Auditable actions for immutable audit trail."""
    AGENT_INVOKED = "agent_invoked"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    TOOL_CALLED = "tool_called"
    TOOL_COMPLETED = "tool_completed"
    POLICY_CHECK = "policy_check"
    POLICY_DEVIATION = "policy_deviation"
    ESCALATION_TRIGGERED = "escalation_triggered"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_DECIDED = "approval_decided"
    NOTIFICATION_SENT = "notification_sent"
    CREDIT_SCORE_COMPUTED = "credit_score_computed"
    CREDIT_APPLICATION_PREPARED = "credit_application_prepared"
    DATA_ACCESSED = "data_accessed"
    DATA_MODIFIED = "data_modified"
    LOGIN = "login"
    LOGOUT = "logout"
    PERMISSION_CHANGE = "permission_change"


# =============================================================================
# SYSTEM LIMITS
# =============================================================================

# Maximum items per page in paginated APIs
MAX_PAGE_SIZE: Final[int] = 100
DEFAULT_PAGE_SIZE: Final[int] = 20

# Agent execution limits
MAX_AGENT_CHAIN_DEPTH: Final[int] = 15
MAX_PARALLEL_AGENTS: Final[int] = 5
MAX_TOOL_CALLS_PER_AGENT: Final[int] = 20

# Memory limits
MAX_SHORT_TERM_MESSAGES: Final[int] = 50
MEMORY_DECAY_HALF_LIFE_DAYS: Final[int] = 30
MEMORY_SUMMARIZE_THRESHOLD: Final[int] = 100

# Document processing
MAX_DOCUMENT_SIZE_MB: Final[int] = 50
MAX_CHUNK_SIZE: Final[int] = 1000
CHUNK_OVERLAP: Final[int] = 200

# Knowledge base
MAX_RAG_RESULTS: Final[int] = 10
RAG_SIMILARITY_THRESHOLD: Final[float] = 0.7

# Credit readiness
READINESS_SCORE_WEIGHTS: Final[dict[str, float]] = {
    "dbt_regularity": 0.30,
    "account_balance_trend": 0.20,
    "transaction_frequency": 0.15,
    "prior_credit_conduct": 0.15,
    "digital_engagement": 0.10,
    "kyc_completeness": 0.10,
}
