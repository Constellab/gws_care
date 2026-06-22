"""State for the My Notifications patient portal page (/my-notifications).

Mirrors the admin NotificationsState structure (inbox / sent / compose / reply)
but scoped to the logged-in patient user:
  - Inbox  : messages received by this user  (recipient_user == user.id)
  - Sent   : messages sent     by this user  (sent_by       == user.id)
  - Compose: patient can reply to clinic messages or write a new message
"""

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


class DoctorPickerRowDTO(BaseModel):
    id: str
    full_name: str = ""
    specialization: str = ""


class NotificationLogRow(BaseModel):
    """Lightweight DTO used by both inbox and sent views."""

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


class PatientNotificationsState(RoleState):
    """State for the /my-notifications page."""

    # ── Inbox / Sent ─────────────────────────────────────────────────────────
    inbox_logs: list[NotificationLogRow] = []
    sent_logs: list[NotificationLogRow] = []
    is_loading_logs: bool = False
    error_message: str = ""

    # ── Sort / filter ─────────────────────────────────────────────────────────
    filter_type: str = "ALL"
    sort_column: str = "created_at"
    sort_ascending: bool = False

    # ── Compose ───────────────────────────────────────────────────────────────
    compose_mode: str = "clinic"   # "clinic" | "doctor"
    compose_subject: str = ""
    compose_body: str = ""
    is_sending: bool = False
    send_success: str = ""
    send_error: str = ""

    # ── Doctor picker (for compose) ───────────────────────────────────────────
    doc_picker_is_open: bool = False
    doc_picker_filter: str = ""
    doc_picker_rows: list[DoctorPickerRowDTO] = []
    doc_picker_is_loading: bool = False
    doc_picker_error: str = ""
    doc_picker_selected_id: str = ""
    doc_picker_selected_name: str = ""

    # ── Reply context ─────────────────────────────────────────────────────────
    reply_to_id: str = ""
    reply_to_subject: str = ""

    # ── Active tab ────────────────────────────────────────────────────────────
    active_tab: str = "inbox"

    # ── Page guard ────────────────────────────────────────────────────────────

    @rx.event
    async def on_load(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_patient_user, redirect_to="/dashboard")
        if redirect:
            return redirect
        await self._load_inbox_logs()
        await self._load_sent_logs()

    # ── Tab navigation ────────────────────────────────────────────────────────

    @rx.event
    async def set_active_tab(self, tab: str):
        self.active_tab = tab

    # ── Sort / filter events ──────────────────────────────────────────────────

    @rx.event
    async def set_filter_type(self, value: str):
        self.filter_type = value
        await self._load_inbox_logs()
        await self._load_sent_logs()

    @rx.event
    async def set_sort(self, column: str):
        """Toggle sort direction if already sorted by *column*, otherwise sort ascending."""
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column
            self.sort_ascending = True
        await self._load_inbox_logs()
        await self._load_sent_logs()

    # ── Reply ─────────────────────────────────────────────────────────────────

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

    # ── Compose events ────────────────────────────────────────────────────────

    @rx.event
    async def set_compose_mode(self, value: str | list[str]):
        self.compose_mode = value if isinstance(value, str) else value[0]
        self.send_success = ""
        self.send_error = ""

    # ── Doctor picker events ──────────────────────────────────────────────────

    @rx.event
    async def open_doctor_picker(self):
        self.doc_picker_filter = ""
        self.doc_picker_error = ""
        self.doc_picker_is_open = True
        await self._run_doc_search()

    @rx.event
    def close_doctor_picker(self):
        self.doc_picker_is_open = False

    @rx.event
    async def doc_picker_set_filter(self, value: str):
        self.doc_picker_filter = value
        await self._run_doc_search()

    @rx.event
    def doc_picker_confirm(self, doctor_id: str, name: str):
        self.doc_picker_selected_id = doctor_id
        self.doc_picker_selected_name = name
        self.doc_picker_is_open = False

    @rx.event
    def doc_picker_clear(self):
        self.doc_picker_selected_id = ""
        self.doc_picker_selected_name = ""

    async def _run_doc_search(self) -> None:
        self.doc_picker_is_loading = True
        self.doc_picker_error = ""
        try:
            patient_id = self._linked_patient_id
            if not patient_id:
                self.doc_picker_rows = []
                return
            with await self.authenticate_user():
                from gws_care.patient.patient_doctor_service import PatientDoctorService
                rows = PatientDoctorService.get_linked_doctors(patient_id)
                f = self.doc_picker_filter.strip().lower()
                self.doc_picker_rows = [
                    DoctorPickerRowDTO(
                        id=str(r.doctor_id),
                        full_name=r.doctor.get_full_name(),
                        specialization=r.doctor.specialization or "",
                    )
                    for r in rows
                    if not f
                    or f in r.doctor.get_full_name().lower()
                    or f in (r.doctor.specialization or "").lower()
                ]
        except Exception as e:
            self.doc_picker_error = str(e)
        finally:
            self.doc_picker_is_loading = False

    @rx.event
    async def set_compose_subject(self, value: str):
        self.compose_subject = value

    @rx.event
    async def set_compose_body(self, value: str):
        self.compose_body = value

    @rx.event
    async def send_message(self):
        """Send the composed message to the clinic / original sender."""
        if not await self.check_authentication():
            return
        self.is_sending = True
        self.send_success = ""
        self.send_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.notification.notification_enums import (
                    NotificationChannel,
                    NotificationType,
                )
                from gws_care.notification.notification_models import NotificationLog
                from gws_care.notification.notification_service import NotificationService
                from gws_care.user.user import User
                from gws_core import CurrentUserService

                if not self.compose_subject.strip():
                    self.send_error = "Subject is required."
                    return
                if not self.compose_body.strip():
                    self.send_error = "Message body is required."
                    return

                gws_user = CurrentUserService.get_and_check_current_user()
                user = User.get_or_none(User.id == gws_user.id)
                if user is None:
                    self.send_error = "Could not identify current user."
                    return

                # If replying, route response back to original sender
                parent_log = None
                recipient_user = None
                if self.reply_to_id:
                    parent_log = NotificationLog.get_or_none(
                        NotificationLog.id == self.reply_to_id
                    )
                    if parent_log and parent_log.sent_by_id:
                        recipient_user = User.get_or_none(User.id == parent_log.sent_by_id)

                # Resolve patient record for the log
                patient = None
                patient_id = self._linked_patient_id
                if patient_id:
                    from gws_care.patient.patient_service import PatientService
                    try:
                        patient = PatientService.get_patient(patient_id)
                    except Exception:
                        pass

                if self.compose_mode == "doctor":
                    # Send to doctor by email
                    from gws_care.doctor.medical_doctor import MedicalDoctor
                    doc = MedicalDoctor.get_or_none(MedicalDoctor.id == self.doc_picker_selected_id)
                    if doc is None or not doc.email:
                        self.send_error = "This doctor has no email address on file."
                        return
                    log = NotificationService._create_log(
                        notification_type=NotificationType.MANUAL_PATIENT,
                        channel=NotificationChannel.EMAIL,
                        subject=self.compose_subject,
                        body=self.compose_body,
                        recipient_email=doc.email,
                        recipient_phone=doc.phone,
                        recipient_name=doc.get_full_name(),
                        sent_by=user,
                        patient=patient,
                        parent_log=parent_log,
                    )
                    success = NotificationService._dispatch(
                        NotificationChannel.EMAIL.value,
                        doc.email, doc.phone, doc.get_full_name(),
                        self.compose_subject, self.compose_body,
                    )
                    NotificationService._finalise_log(log, success)
                    self.send_success = f"Message sent to {doc.get_full_name()}."
                else:
                    # Send to clinic (in-app, reply routing)
                    log = NotificationService._create_log(
                        notification_type=NotificationType.MANUAL_PATIENT,
                        channel=NotificationChannel.IN_APP,
                        subject=self.compose_subject,
                        body=self.compose_body,
                        recipient_email=None,
                        recipient_phone=None,
                        recipient_name=None,
                        sent_by=user,
                        patient=patient,
                        recipient_user=recipient_user,
                        parent_log=parent_log,
                    )
                    NotificationService._finalise_log(log, True)
                    if recipient_user:
                        NotificationService.create_bell(
                            str(recipient_user.id),
                            f"Reply from {user.first_name} {user.last_name}: {self.compose_subject}",
                            log=log,
                        )
                    self.send_success = "Message sent."
                self.compose_subject = ""
                self.compose_body = ""
                self.reply_to_id = ""
                self.reply_to_subject = ""
            await self._load_sent_logs()
        except Exception as e:
            self.send_error = f"Error: {e}"
        finally:
            self.is_sending = False

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _get_current_user(self):
        """Return the local User row for the currently authenticated user."""
        from gws_care.user.user import User
        from gws_core import CurrentUserService
        gws_user = CurrentUserService.get_and_check_current_user()
        return User.get_or_none(User.id == gws_user.id)

    async def _make_log_rows(self, logs) -> list[NotificationLogRow]:
        """Convert ORM log entries to sorted NotificationLogRow DTOs."""
        rows = []
        for log_entry in logs:
            body_text = log_entry.body or ""
            first_line = body_text.split("\n")[0][:120]
            rows.append(NotificationLogRow(
                id=str(log_entry.id),
                created_at=(
                    log_entry.created_at.strftime("%Y-%m-%d %H:%M")
                    if log_entry.created_at else ""
                ),
                notification_type=log_entry.notification_type.value,
                channel=log_entry.channel.value,
                status=log_entry.status.value,
                recipient_name=log_entry.recipient_name or "—",
                recipient_email=log_entry.recipient_email or "—",
                subject=log_entry.subject or "",
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
        """Load messages received by the current patient user."""
        self.is_loading_logs = True
        self.error_message = ""
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
        except Exception as e:
            self.error_message = f"Error loading inbox: {e}"
            self.inbox_logs = []
        finally:
            self.is_loading_logs = False

    async def _load_sent_logs(self):
        """Load messages sent by the current patient user."""
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
