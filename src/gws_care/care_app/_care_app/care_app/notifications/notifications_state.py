"""State for the Notifications page (inbox, sent, compose, preferences)."""

import reflex as rx
from pydantic import BaseModel

from ..common.account_picker_state import AccountPickerRowDTO
from ..common.combined_picker_state import CombinedPickerState
from ..common.patient_picker_state import PatientPickerRowDTO


class NotificationLogRow(BaseModel):
    id: str
    created_at: str
    notification_type: str
    channel: str
    status: str
    recipient_name: str
    recipient_email: str
    subject: str
    body_preview: str
    sent_by_name: str
    parent_log_id: str


class NotificationsState(CombinedPickerState):
    """State for the /notifications page."""

    # ── Patient picker vars (declared here for independent state storage) ─────
    picker_patients: list[PatientPickerRowDTO] = []
    picker_is_loading: bool = False
    picker_error: str = ""
    picker_filter_name: str = ""
    picker_filter_number: str = ""
    picker_account_id: str = ""
    picker_is_open: bool = False
    picker_selected_id: str = ""
    picker_selected_label: str = ""

    # ── Account picker vars (declared here for independent state storage) ─────
    acct_picker_is_open: bool = False
    acct_picker_filter: str = ""
    acct_picker_accounts: list[AccountPickerRowDTO] = []
    acct_picker_is_loading: bool = False
    acct_picker_error: str = ""
    acct_picker_selected_id: str = ""
    acct_picker_selected_name: str = ""

    # ── Patient picker events ─────────────────────────────────────────────────────

    @rx.event
    async def open_patient_picker(self):
        await self._open_patient_picker()

    @rx.event
    def close_patient_picker(self):
        self.picker_is_open = False

    @rx.event
    async def picker_clear_selection(self):
        self.picker_selected_id = ""
        self.picker_selected_label = ""

    @rx.event
    async def picker_set_filter_name(self, value: str):
        await self._picker_set_filter_name(value)

    @rx.event
    async def picker_set_filter_number(self, value: str):
        await self._picker_set_filter_number(value)

    @rx.event
    async def picker_clear_filters(self):
        await self._picker_clear_filters()

    @rx.event
    def picker_select_patient(self, patient_id: str, label: str):
        self.picker_selected_id = patient_id
        self.picker_selected_label = label
        self.picker_is_open = False

    # ── Account picker events ─────────────────────────────────────────────────────

    @rx.event
    async def open_account_picker(self):
        await self._open_account_picker()

    @rx.event
    def close_account_picker(self):
        self.acct_picker_is_open = False

    @rx.event
    async def acct_picker_set_filter(self, value: str):
        await self._acct_picker_set_filter(value)

    @rx.event
    async def acct_picker_confirm(self, account_id: str, name: str):
        await self._acct_picker_confirm(account_id, name)

    @rx.event
    async def acct_picker_clear(self):
        await self._acct_picker_clear()

    # ── Inbox / Sent box ──────────────────────────────────────────────────────
    inbox_logs: list[NotificationLogRow] = []
    sent_logs: list[NotificationLogRow] = []
    is_loading_logs: bool = False
    history_box: str = "inbox"      # "inbox" | "sent"
    filter_type: str = "ALL"
    sort_column: str = "created_at"
    sort_ascending: bool = False

    # ── Preferences tab ───────────────────────────────────────────────────────
    pref_enabled: bool = True
    pref_new_day: str = ""
    pref_days: list[int] = []
    is_saving_pref: bool = False
    pref_success: str = ""
    pref_error: str = ""

    # ── Compose tab ───────────────────────────────────────────────────────────
    compose_mode: str = "patient"   # "patient" | "account"
    compose_subject: str = ""
    compose_body: str = ""
    is_sending: bool = False
    send_success: str = ""
    send_error: str = ""

    # ── Reply context ─────────────────────────────────────────────────────────
    reply_to_id: str = ""
    reply_to_subject: str = ""

    # ── Reminders ─────────────────────────────────────────────────────────────
    reminder_result: str = ""
    is_processing_reminders: bool = False

    # ── Active tab ────────────────────────────────────────────────────────────
    active_tab: str = "inbox"

    @rx.event
    async def on_load(self):
        await self._load_inbox_logs()
        await self._load_sent_logs()
        await self._load_preferences()

    @rx.event
    async def set_active_tab(self, tab: str):
        self.active_tab = tab

    @rx.event
    async def set_history_box(self, box: str):
        self.history_box = box

    # ── Inbox / Sent ────────────────────────────────────────────────────────────

    @rx.event
    async def set_filter_type(self, value: str):
        self.filter_type = value
        await self._load_inbox_logs()
        await self._load_sent_logs()

    @rx.event
    async def set_sort(self, column: str):
        """Sort by column; toggle direction if already sorted by the same column."""
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column
            self.sort_ascending = True
        await self._load_inbox_logs()
        await self._load_sent_logs()

    async def _make_log_rows(self, logs) -> list[NotificationLogRow]:
        rows = []
        for log_entry in logs:
            body_text = log_entry.body or ""
            first_line = body_text.split("\n")[0][:120]
            rows.append(NotificationLogRow(
                id=str(log_entry.id),
                created_at=log_entry.created_at.strftime("%Y-%m-%d %H:%M") if log_entry.created_at else "",
                notification_type=log_entry.notification_type.value,
                channel=log_entry.channel.value,
                status=log_entry.status.value,
                recipient_name=log_entry.recipient_name or "—",
                recipient_email=log_entry.recipient_email or "—",
                subject=log_entry.subject,
                body_preview=first_line,
                sent_by_name=(
                    f"{log_entry.sent_by.first_name} {log_entry.sent_by.last_name}"
                    if log_entry.sent_by_id else "System"
                ),
                parent_log_id=str(log_entry.parent_log_id) if log_entry.parent_log_id else "",
            ))
        sort_col = self.sort_column
        return sorted(
            rows,
            key=lambda row: (getattr(row, sort_col) or "").lower(),
            reverse=not self.sort_ascending,
        )

    async def _load_inbox_logs(self):
        self.is_loading_logs = True
        try:
            with await self.authenticate_user():
                from gws_care.notification.notification_service import NotificationService
                user = await self._get_current_user()
                if user is None:
                    self.inbox_logs = []
                    return
                logs = NotificationService.list_inbox_logs(
                    user_id=str(user.id),
                    notification_type=self.filter_type if self.filter_type != "ALL" else None,
                )
                self.inbox_logs = await self._make_log_rows(logs)
        except Exception:
            self.inbox_logs = []
        finally:
            self.is_loading_logs = False

    async def _load_sent_logs(self):
        try:
            with await self.authenticate_user():
                from gws_care.notification.notification_service import NotificationService
                user = await self._get_current_user()
                if user is None:
                    self.sent_logs = []
                    return
                logs = NotificationService.list_sent_logs(
                    user_id=str(user.id),
                    notification_type=self.filter_type if self.filter_type != "ALL" else None,
                )
                self.sent_logs = await self._make_log_rows(logs)
        except Exception:
            self.sent_logs = []

    # ── Preferences ───────────────────────────────────────────────────────────

    async def _load_preferences(self):
        try:
            with await self.authenticate_user():
                from gws_care.notification.notification_service import NotificationService
                user = await self._get_current_user()
                if user is None:
                    return
                pref = NotificationService.get_or_create_preference(str(user.id))
                self.pref_enabled = pref.email_reminders_enabled
                self.pref_days = list(pref.reminder_days or [])
        except Exception:
            pass

    async def _get_current_user(self):
        from gws_care.user.user import User
        from gws_core import CurrentUserService
        gws_user = CurrentUserService.get_and_check_current_user()
        return User.get_or_none(User.id == gws_user.id)

    @rx.event
    async def set_pref_enabled(self, value: bool):
        self.pref_enabled = value

    @rx.event
    async def set_pref_new_day(self, value: str):
        self.pref_new_day = value

    @rx.event
    async def add_reminder_day(self):
        """Add a day to the reminder list."""
        try:
            day = int(self.pref_new_day)
        except (ValueError, TypeError):
            self.pref_error = "Please enter a valid positive integer."
            return
        if day <= 0:
            self.pref_error = "Day must be a positive number."
            return
        if day in self.pref_days:
            self.pref_error = f"{day} is already in the list."
            return
        self.pref_days = sorted(set(self.pref_days + [day]), reverse=True)
        self.pref_new_day = ""
        self.pref_error = ""

    @rx.event
    async def remove_reminder_day(self, day: int):
        """Remove a day from the reminder list."""
        self.pref_days = [d for d in self.pref_days if d != day]

    @rx.event
    async def save_preferences(self):
        self.is_saving_pref = True
        self.pref_success = ""
        self.pref_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.notification.notification_dto import NotificationPreferenceDTO
                from gws_care.notification.notification_service import NotificationService
                user = await self._get_current_user()
                if user is None:
                    self.pref_error = "Could not identify current user."
                    return
                NotificationService.save_preference(
                    str(user.id),
                    NotificationPreferenceDTO(
                        reminder_days=self.pref_days,
                        email_reminders_enabled=self.pref_enabled,
                    ),
                )
                self.pref_success = "Preferences saved."
        except Exception as e:
            self.pref_error = f"Error: {e}"
        finally:
            self.is_saving_pref = False

    @rx.event
    async def process_reminders(self):
        """Manually trigger appointment reminder sending."""
        self.is_processing_reminders = True
        self.reminder_result = ""
        try:
            with await self.authenticate_user():
                from gws_care.notification.notification_service import NotificationService
                user = await self._get_current_user()
                if user is None:
                    self.reminder_result = "Could not identify current user."
                    return
                count = NotificationService.process_appointment_reminders(user)
                self.reminder_result = f"{count} reminder(s) sent."
            await self._load_sent_logs()
        except Exception as e:
            self.reminder_result = f"Error: {e}"
        finally:
            self.is_processing_reminders = False

    # ── Compose ───────────────────────────────────────────────────────────────

    @rx.event
    async def set_compose_mode(self, value: str | list[str]):
        self.compose_mode = value if isinstance(value, str) else value[0]
        self.send_success = ""
        self.send_error = ""

    @rx.event
    async def open_reply(self, log_id: str, subject: str):
        """Pre-fill compose form for a reply to the given message."""
        self.reply_to_id = log_id
        prefix = "Re: " if not subject.startswith("Re: ") else ""
        self.reply_to_subject = prefix + subject
        self.compose_subject = self.reply_to_subject
        self.compose_body = ""
        self.send_success = ""
        self.send_error = ""
        self.active_tab = "compose"

    @rx.event
    async def clear_reply(self):
        """Clear reply context."""
        self.reply_to_id = ""
        self.reply_to_subject = ""

    async def _on_account_picked(self, account_id: str) -> None:
        """Account picker callback: store selected account for compose tab."""
        # acct_picker_selected_id is already set by the base class; we just accept it.
        pass

    @rx.event
    async def set_compose_subject(self, value: str):
        self.compose_subject = value

    @rx.event
    async def set_compose_body(self, value: str):
        self.compose_body = value

    @rx.event
    async def send_message(self):
        """Send the composed message."""
        self.is_sending = True
        self.send_success = ""
        self.send_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.notification.notification_models import NotificationLog
                from gws_care.notification.notification_service import NotificationService
                user = await self._get_current_user()
                if user is None:
                    self.send_error = "Could not identify current user."
                    return

                parent_log = None
                if self.reply_to_id:
                    parent_log = NotificationLog.get_or_none(NotificationLog.id == self.reply_to_id)

                if self.compose_mode == "patient":
                    from gws_care.notification.notification_dto import SendCustomMessageDTO
                    NotificationService.send_to_patient(
                        SendCustomMessageDTO(
                            patient_id=self.picker_selected_id,
                            subject=self.compose_subject,
                            body=self.compose_body,
                        ),
                        sent_by=user,
                        parent_log=parent_log,
                    )
                    self.send_success = "Message sent to patient."
                else:
                    from gws_care.notification.notification_dto import SendManualNotificationDTO
                    logs = NotificationService.send_to_account(
                        SendManualNotificationDTO(
                            account_id=self.acct_picker_selected_id,
                            subject=self.compose_subject,
                            body=self.compose_body,
                        ),
                        sent_by=user,
                    )
                    self.send_success = f"Message sent to {len(logs)} recipient(s)."

                self.compose_subject = ""
                self.compose_body = ""
                self.reply_to_id = ""
                self.reply_to_subject = ""
            await self._load_sent_logs()
        except Exception as e:
            self.send_error = f"Error: {e}"
        finally:
            self.is_sending = False


