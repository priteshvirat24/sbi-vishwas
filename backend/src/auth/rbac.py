"""
SBI Vishwas — RBAC & ABAC

Role-Based and Attribute-Based Access Control for enterprise-grade authorization.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel


# =============================================================================
# PERMISSIONS
# =============================================================================


class Permission(str, Enum):
    """Fine-grained permissions for RBAC."""

    # Customer management
    CUSTOMER_READ = "customer:read"
    CUSTOMER_WRITE = "customer:write"
    CUSTOMER_DELETE = "customer:delete"
    CUSTOMER_EXPORT = "customer:export"

    # Account management
    ACCOUNT_READ = "account:read"
    ACCOUNT_WRITE = "account:write"
    ACCOUNT_DORMANCY_MANAGE = "account:dormancy:manage"

    # Complaint management
    COMPLAINT_READ = "complaint:read"
    COMPLAINT_WRITE = "complaint:write"
    COMPLAINT_ESCALATE = "complaint:escalate"
    COMPLAINT_RESOLVE = "complaint:resolve"

    # Conversation
    CONVERSATION_READ = "conversation:read"
    CONVERSATION_WRITE = "conversation:write"

    # Workflow
    WORKFLOW_READ = "workflow:read"
    WORKFLOW_EXECUTE = "workflow:execute"
    WORKFLOW_CANCEL = "workflow:cancel"

    # Agent
    AGENT_READ = "agent:read"
    AGENT_EXECUTE = "agent:execute"
    AGENT_CONFIGURE = "agent:configure"

    # Approval
    APPROVAL_READ = "approval:read"
    APPROVAL_DECIDE = "approval:decide"
    APPROVAL_DELEGATE = "approval:delegate"

    # Knowledge
    KNOWLEDGE_READ = "knowledge:read"
    KNOWLEDGE_WRITE = "knowledge:write"
    KNOWLEDGE_DELETE = "knowledge:delete"

    # Policy
    POLICY_READ = "policy:read"
    POLICY_WRITE = "policy:write"
    POLICY_CHECK_VIEW = "policy:check:view"

    # Notification
    NOTIFICATION_READ = "notification:read"
    NOTIFICATION_SEND = "notification:send"

    # Audit
    AUDIT_READ = "audit:read"
    AUDIT_EXPORT = "audit:export"

    # Admin
    ADMIN_USER_MANAGE = "admin:user:manage"
    ADMIN_ROLE_MANAGE = "admin:role:manage"
    ADMIN_SYSTEM_CONFIG = "admin:system:config"
    ADMIN_FULL = "admin:full"


# =============================================================================
# ROLE DEFINITIONS
# =============================================================================


class SystemRole(str, Enum):
    """Pre-defined system roles."""
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    BRANCH_MANAGER = "branch_manager"
    RELATIONSHIP_MANAGER = "relationship_manager"
    AGENT_OPERATOR = "agent_operator"
    AUDITOR = "auditor"
    CUSTOMER_SUPPORT = "customer_support"
    POLICY_MANAGER = "policy_manager"
    VIEWER = "viewer"


# Permission matrix — maps roles to their default permissions
ROLE_PERMISSIONS: dict[str, list[str]] = {
    SystemRole.SUPERADMIN.value: [p.value for p in Permission],  # All permissions

    SystemRole.ADMIN.value: [
        Permission.CUSTOMER_READ.value, Permission.CUSTOMER_WRITE.value,
        Permission.ACCOUNT_READ.value, Permission.ACCOUNT_WRITE.value,
        Permission.COMPLAINT_READ.value, Permission.COMPLAINT_WRITE.value,
        Permission.COMPLAINT_ESCALATE.value, Permission.COMPLAINT_RESOLVE.value,
        Permission.CONVERSATION_READ.value,
        Permission.WORKFLOW_READ.value, Permission.WORKFLOW_EXECUTE.value,
        Permission.AGENT_READ.value, Permission.AGENT_EXECUTE.value, Permission.AGENT_CONFIGURE.value,
        Permission.APPROVAL_READ.value, Permission.APPROVAL_DECIDE.value,
        Permission.KNOWLEDGE_READ.value, Permission.KNOWLEDGE_WRITE.value,
        Permission.POLICY_READ.value, Permission.POLICY_WRITE.value, Permission.POLICY_CHECK_VIEW.value,
        Permission.NOTIFICATION_READ.value, Permission.NOTIFICATION_SEND.value,
        Permission.AUDIT_READ.value,
        Permission.ADMIN_USER_MANAGE.value, Permission.ADMIN_ROLE_MANAGE.value,
    ],

    SystemRole.BRANCH_MANAGER.value: [
        Permission.CUSTOMER_READ.value, Permission.CUSTOMER_WRITE.value,
        Permission.ACCOUNT_READ.value,
        Permission.COMPLAINT_READ.value, Permission.COMPLAINT_WRITE.value,
        Permission.COMPLAINT_ESCALATE.value, Permission.COMPLAINT_RESOLVE.value,
        Permission.CONVERSATION_READ.value,
        Permission.WORKFLOW_READ.value,
        Permission.APPROVAL_READ.value, Permission.APPROVAL_DECIDE.value,
        Permission.POLICY_READ.value, Permission.POLICY_CHECK_VIEW.value,
        Permission.NOTIFICATION_READ.value,
        Permission.AUDIT_READ.value,
    ],

    SystemRole.RELATIONSHIP_MANAGER.value: [
        Permission.CUSTOMER_READ.value, Permission.CUSTOMER_WRITE.value,
        Permission.ACCOUNT_READ.value,
        Permission.COMPLAINT_READ.value, Permission.COMPLAINT_WRITE.value,
        Permission.CONVERSATION_READ.value, Permission.CONVERSATION_WRITE.value,
        Permission.WORKFLOW_READ.value,
        Permission.APPROVAL_READ.value,
        Permission.KNOWLEDGE_READ.value,
        Permission.POLICY_READ.value,
        Permission.NOTIFICATION_READ.value,
    ],

    SystemRole.AGENT_OPERATOR.value: [
        Permission.AGENT_READ.value, Permission.AGENT_EXECUTE.value, Permission.AGENT_CONFIGURE.value,
        Permission.WORKFLOW_READ.value, Permission.WORKFLOW_EXECUTE.value,
        Permission.KNOWLEDGE_READ.value, Permission.KNOWLEDGE_WRITE.value,
        Permission.POLICY_READ.value,
        Permission.AUDIT_READ.value,
    ],

    SystemRole.AUDITOR.value: [
        Permission.CUSTOMER_READ.value,
        Permission.ACCOUNT_READ.value,
        Permission.COMPLAINT_READ.value,
        Permission.CONVERSATION_READ.value,
        Permission.WORKFLOW_READ.value,
        Permission.AGENT_READ.value,
        Permission.APPROVAL_READ.value,
        Permission.KNOWLEDGE_READ.value,
        Permission.POLICY_READ.value, Permission.POLICY_CHECK_VIEW.value,
        Permission.NOTIFICATION_READ.value,
        Permission.AUDIT_READ.value, Permission.AUDIT_EXPORT.value,
    ],

    SystemRole.CUSTOMER_SUPPORT.value: [
        Permission.CUSTOMER_READ.value,
        Permission.ACCOUNT_READ.value,
        Permission.COMPLAINT_READ.value, Permission.COMPLAINT_WRITE.value,
        Permission.CONVERSATION_READ.value, Permission.CONVERSATION_WRITE.value,
        Permission.WORKFLOW_READ.value,
        Permission.KNOWLEDGE_READ.value,
        Permission.POLICY_READ.value,
        Permission.NOTIFICATION_READ.value, Permission.NOTIFICATION_SEND.value,
    ],

    SystemRole.POLICY_MANAGER.value: [
        Permission.POLICY_READ.value, Permission.POLICY_WRITE.value, Permission.POLICY_CHECK_VIEW.value,
        Permission.KNOWLEDGE_READ.value, Permission.KNOWLEDGE_WRITE.value, Permission.KNOWLEDGE_DELETE.value,
        Permission.AUDIT_READ.value,
    ],

    SystemRole.VIEWER.value: [
        Permission.CUSTOMER_READ.value,
        Permission.ACCOUNT_READ.value,
        Permission.COMPLAINT_READ.value,
        Permission.WORKFLOW_READ.value,
        Permission.KNOWLEDGE_READ.value,
        Permission.POLICY_READ.value,
    ],
}


# =============================================================================
# ABAC
# =============================================================================


class ABACCondition(BaseModel):
    """Attribute-based access control condition."""
    attribute: str
    operator: str  # eq, neq, in, not_in, gt, lt, gte, lte, contains
    value: Any


class ABACPolicy(BaseModel):
    """An ABAC policy with conditions that must all be satisfied."""
    name: str
    description: str
    conditions: list[ABACCondition]
    effect: str = "allow"  # allow or deny


def evaluate_abac_conditions(
    conditions: list[ABACCondition],
    context: dict[str, Any],
) -> bool:
    """
    Evaluate ABAC conditions against a request context.

    All conditions must be satisfied for the policy to match.
    """
    for condition in conditions:
        ctx_value = context.get(condition.attribute)
        if ctx_value is None:
            return False

        match condition.operator:
            case "eq":
                if ctx_value != condition.value:
                    return False
            case "neq":
                if ctx_value == condition.value:
                    return False
            case "in":
                if ctx_value not in condition.value:
                    return False
            case "not_in":
                if ctx_value in condition.value:
                    return False
            case "gt":
                if not (ctx_value > condition.value):
                    return False
            case "lt":
                if not (ctx_value < condition.value):
                    return False
            case "gte":
                if not (ctx_value >= condition.value):
                    return False
            case "lte":
                if not (ctx_value <= condition.value):
                    return False
            case "contains":
                if condition.value not in ctx_value:
                    return False
            case _:
                return False

    return True


def check_permission(
    user_permissions: list[str],
    required_permission: str,
) -> bool:
    """Check if a user has a specific permission."""
    if Permission.ADMIN_FULL.value in user_permissions:
        return True
    return required_permission in user_permissions


def check_any_permission(
    user_permissions: list[str],
    required_permissions: list[str],
) -> bool:
    """Check if a user has any of the required permissions."""
    if Permission.ADMIN_FULL.value in user_permissions:
        return True
    return any(p in user_permissions for p in required_permissions)
