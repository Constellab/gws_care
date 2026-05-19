"""Audit log page state (US-210)."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class AuditLogRowVM(BaseModel):
    id: int
    user_email: str
    action: str
    action_label: str
    resource_type: str
    resource_id: str
    details: str
    ip_address: str
    created_at: str


class AuditState(ReflexMainState):
    logs: list[AuditLogRowVM] = []
    is_loading: bool = False
    error: str = ""
    filter_action: str = ""
    filter_user: str = ""
    filter_resource_type: str = ""

    @rx.event
    async def on_load(self):
        await self._load()

    @rx.event
    def set_filter_action(self, v: str):
        self.filter_action = "" if v == "__all__" else v

    @rx.event
    def set_filter_user(self, v: str):
        self.filter_user = v

    @rx.event
    def set_filter_resource(self, v: str):
        self.filter_resource_type = v

    @rx.event
    async def apply_filters(self):
        await self._load()

    async def _load(self):
        if not await self.check_authentication():
            return
        self.is_loading = True
        self.error = ""
        try:
            with await self.authenticate_user():
                from gws_care.audit.audit_log import AuditAction, AuditLog
                query = AuditLog.select().order_by(AuditLog.created_at.desc())
                if self.filter_action:
                    query = query.where(AuditLog.action == self.filter_action)
                if self.filter_user:
                    query = query.where(AuditLog.user_email.contains(self.filter_user))
                if self.filter_resource_type:
                    query = query.where(AuditLog.resource_type == self.filter_resource_type)
                rows = []
                for log in query.limit(200):
                    try:
                        action_label = AuditAction(log.action).get_label()
                    except ValueError:
                        action_label = log.action
                    rows.append(AuditLogRowVM(
                        id=log.id,
                        user_email=log.user_email or "",
                        action=log.action,
                        action_label=action_label,
                        resource_type=log.resource_type or "",
                        resource_id=str(log.resource_id) if log.resource_id else "",
                        details=log.details or "",
                        ip_address=log.ip_address or "",
                        created_at=log.created_at.strftime("%d/%m/%Y %H:%M") if log.created_at else "",
                    ))
                self.logs = rows
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_loading = False
