"""
SBI Vishwas — Communication Tools

Tools for dispatching multi-channel notifications and triggering escalations.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from src.agents.tools.core import BaseTool, register_tool


class NotificationInput(BaseModel):
    customer_id: str = Field(description="UUID of the customer.")
    channel: str = Field(description="Channel to use: sms, email, whatsapp, yono_push.")
    subject: str = Field(default="", description="Subject line (for email).")
    message: str = Field(description="The complete message to send.")
    notification_type: str = Field(default="status_update", description="Type of notification.")


@register_tool
class NotificationTool(BaseTool):
    """Tool to queue customer notifications."""
    
    name = "notification_tool"
    description = "Send a proactive status update, alert, or reminder to a customer via their preferred channel."
    args_schema = NotificationInput

    async def arun(self, customer_id: str, channel: str, message: str, subject: str = "", notification_type: str = "status_update") -> str:
        """Queue a notification in the database."""
        from src.database.engine import get_transactional_session
        from src.database.models.domain import Notification
        import uuid

        try:
            cid = uuid.UUID(customer_id)
            async with get_transactional_session() as session:
                notification = Notification(
                    customer_id=cid,
                    channel=channel,
                    notification_type=notification_type,
                    subject=subject,
                    body=message,
                    status="queued"
                )
                session.add(notification)
                
            return f"Successfully queued {notification_type} notification via {channel}."
            
        except Exception as e:
            return f"Failed to queue notification: {str(e)}"


class EscalationInput(BaseModel):
    complaint_id: str = Field(description="UUID of the complaint.")
    target_level: int = Field(description="Hierarchical level to escalate to (1-4).")
    reason: str = Field(description="Reason for escalation.")
    internal_notes: str = Field(description="Notes for the receiving party.")


@register_tool
class EscalationTool(BaseTool):
    """Tool to formally escalate complaints."""
    
    name = "escalation_tool"
    description = "Escalate a complaint to a higher hierarchical level when SLA is at risk."
    args_schema = EscalationInput

    async def arun(self, complaint_id: str, target_level: int, reason: str, internal_notes: str) -> str:
        """Update complaint level in database."""
        from sqlalchemy import select
        from src.database.engine import get_transactional_session
        from src.database.models.complaint import Complaint, ComplaintEscalation
        import uuid

        try:
            cid = uuid.UUID(complaint_id)
            async with get_transactional_session() as session:
                result = await session.execute(select(Complaint).where(Complaint.id == cid))
                complaint = result.scalar_one_or_none()
                
                if not complaint:
                    return f"Complaint {complaint_id} not found."
                
                # Create escalation record
                escalation = ComplaintEscalation(
                    complaint_id=cid,
                    from_level=complaint.escalation_level,
                    to_level=target_level,
                    reason=reason,
                    notes=internal_notes
                )
                session.add(escalation)
                
                # Update complaint
                complaint.escalation_level = target_level
                
            return f"Complaint escalated to level {target_level} successfully."
            
        except Exception as e:
            return f"Escalation failed: {str(e)}"
