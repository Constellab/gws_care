"""AuditService — write and query audit log entries (US-210)."""

from datetime import datetime

from gws_care.audit.audit_log import AuditAction, AuditLog


class AuditService:
    """Centralized service to create and query audit log entries."""

    @classmethod
    def log(
        cls,
        action: AuditAction | str,
        user_id: int | None = None,
        user_email: str | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
        details: str | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Write an audit log entry. Never raises — silently drops on DB error."""
        try:
            entry = AuditLog()
            entry.action = action.value if isinstance(action, AuditAction) else action
            entry.user_id = user_id
            entry.user_email = user_email
            entry.resource_type = resource_type
            entry.resource_id = resource_id
            entry.details = details
            entry.ip_address = ip_address
            entry.created_at = datetime.now()
            entry.save()
        except Exception as exc:
            print(f"[audit] Failed to write log entry (action={action}): {exc}")

    @classmethod
    def query(
        cls,
        action: str | None = None,
        user_id: int | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 200,
    ) -> list[AuditLog]:
        q = AuditLog.select().order_by(AuditLog.created_at.desc())
        if action:
            q = q.where(AuditLog.action == action)
        if user_id:
            q = q.where(AuditLog.user_id == user_id)
        if resource_type:
            q = q.where(AuditLog.resource_type == resource_type)
        if resource_id:
            q = q.where(AuditLog.resource_id == resource_id)
        if date_from:
            q = q.where(AuditLog.created_at >= date_from)
        if date_to:
            q = q.where(AuditLog.created_at <= date_to)
        return list(q.limit(limit))
