"""State for the notification bell in the sidebar."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class BellEntryDTO(BaseModel):
    id: str
    message: str
    is_read: bool
    created_at: str


class BellState(ReflexMainState):
    """Manages the notification bell shown in the sidebar."""

    unread_count: int = 0
    bell_entries: list[BellEntryDTO] = []
    bell_open: bool = False

    @rx.event
    async def load_bell(self):
        """Refresh unread count and recent bell entries."""
        try:
            with await self.authenticate_user():
                from gws_care.notification.notification_service import NotificationService
                from gws_care.user.user import User
                from gws_core import CurrentUserService

                gws_user = CurrentUserService.get_and_check_current_user()
                user = User.get_or_none(User.id == gws_user.id)
                if user is None:
                    return

                self.unread_count = NotificationService.unread_count(str(user.id))
                bells = NotificationService.get_bell_notifications(str(user.id))
                self.bell_entries = [
                    BellEntryDTO(
                        id=str(b.id),
                        message=b.message,
                        is_read=b.is_read,
                        created_at=b.created_at.strftime("%Y-%m-%d %H:%M") if b.created_at else "",
                    )
                    for b in bells[:10]
                ]
        except Exception as exc:
            pass

    @rx.event
    async def toggle_bell(self):
        self.bell_open = not self.bell_open

    @rx.event
    async def close_bell(self):
        self.bell_open = False

    @rx.event
    async def mark_all_read(self):
        try:
            with await self.authenticate_user():
                from gws_care.notification.notification_service import NotificationService
                from gws_care.user.user import User
                from gws_core import CurrentUserService

                gws_user = CurrentUserService.get_and_check_current_user()
                user = User.get_or_none(User.id == gws_user.id)
                if user is None:
                    return

                NotificationService.mark_all_read(str(user.id))
                self.unread_count = 0
                for entry in self.bell_entries:
                    entry.is_read = True
        except Exception as exc:
            pass
