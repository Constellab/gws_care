"""State for the Notifications page (inbox, sent, compose, preferences)."""

import reflex as rx
from pydantic import BaseModel

from ..common.account_picker_state import AccountPickerRowDTO
from ..common.combined_picker_state import CombinedPickerState
from ..common.patient_picker_state import PatientPickerRowDTO


class DoctorPickerRowDTO(BaseModel):
    id: str
    full_name: str = ""
    specialization: str = ""


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
    compose_mode: str = "patient"   # "patient" | "account" | "doctor"
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

    # ── Reminders ─────────────────────────────────────────────────────────────
    reminder_result: str = ""
    is_processing_reminders: bool = False

    # ── SMTP configuration (admin only) ───────────────────────────────────────
    smtp_host: str = ""
    smtp_port: str = "587"
    smtp_credentials_name: str = ""
    smtp_use_tls: bool = True
    smtp_from_email: str = ""
    smtp_from_name: str = ""
    smtp_is_loading: bool = False
    smtp_is_saving: bool = False
    smtp_success: str = ""
    smtp_error: str = ""
    smtp_test_result: str = ""
    smtp_is_testing: bool = False

    # ── Active tab ────────────────────────────────────────────────────────────
    active_tab: str = "inbox"

    @rx.event
    async def on_load(self):
        await self._load_roles()
        await self._load_inbox_logs()
        await self._load_sent_logs()
        await self._load_preferences()
        if self.is_admin:
            await self._load_smtp_config()

    @rx.event
    async def load_settings(self):
        """Load preferences and SMTP config for the /settings admin panel."""
        await self._load_roles()
        await self._load_preferences()
        if self.is_admin:
            await self._load_smtp_config()

    # ── SMTP configuration events (admin only) ────────────────────────────────

    async def _load_smtp_config(self) -> None:
        self.smtp_is_loading = True
        self.smtp_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.notification.notification_service import NotificationService
                dto = NotificationService.get_smtp_config()
                self.smtp_host = dto.host or ""
                self.smtp_port = str(dto.port) if dto.port else "587"
                self.smtp_credentials_name = dto.credentials_name or ""
                self.smtp_use_tls = dto.use_tls
                self.smtp_from_email = dto.from_email or ""
                self.smtp_from_name = dto.from_name or ""
        except Exception as e:
            print(f"[NotificationsState] Failed to load SMTP config: {e}")
            self.smtp_error = f"Failed to load SMTP config: {e}"
        finally:
            self.smtp_is_loading = False

    @rx.event
    def smtp_set_host(self, value: str):
        self.smtp_host = value
        self.smtp_success = ""
        self.smtp_error = ""

    @rx.event
    def smtp_set_port(self, value: str):
        self.smtp_port = value
        self.smtp_success = ""
        self.smtp_error = ""

    @rx.event
    def smtp_set_credentials_name(self, value: str):
        self.smtp_credentials_name = value
        self.smtp_success = ""
        self.smtp_error = ""

    @rx.event
    def smtp_set_use_tls(self, value: bool):
        self.smtp_use_tls = value

    @rx.event
    def smtp_set_from_email(self, value: str):
        self.smtp_from_email = value
        self.smtp_success = ""
        self.smtp_error = ""

    @rx.event
    def smtp_set_from_name(self, value: str):
        self.smtp_from_name = value
        self.smtp_success = ""
        self.smtp_error = ""

    @rx.event
    async def save_smtp_config(self):
        if not self.is_admin:
            return
        if not self.smtp_host.strip():
            self.smtp_error = "Host is required."
            return
        self.smtp_is_saving = True
        self.smtp_success = ""
        self.smtp_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.notification.notification_dto import SmtpConfigDTO
                from gws_care.notification.notification_service import NotificationService
                try:
                    port = int(self.smtp_port)
                except (ValueError, TypeError):
                    port = 587
                dto = SmtpConfigDTO(
                    host=self.smtp_host.strip(),
                    port=port,
                    credentials_name=self.smtp_credentials_name.strip(),
                    use_tls=self.smtp_use_tls,
                    from_email=self.smtp_from_email.strip(),
                    from_name=self.smtp_from_name.strip(),
                )
                NotificationService.save_smtp_config(dto)
                self.smtp_success = "SMTP configuration saved."
        except Exception as e:
            self.smtp_error = f"Error: {e}"
        finally:
            self.smtp_is_saving = False

    @rx.event
    async def test_smtp_connection(self):
        if not self.is_admin:
            return
        if not self.smtp_host.strip():
            self.smtp_test_result = "Error: host is required."
            return
        self.smtp_is_testing = True
        self.smtp_test_result = ""
        try:
            import smtplib
            try:
                port = int(self.smtp_port)
            except (ValueError, TypeError):
                port = 587
            if self.smtp_use_tls:
                server = smtplib.SMTP(self.smtp_host.strip(), port, timeout=10)
                server.starttls()
            else:
                server = smtplib.SMTP(self.smtp_host.strip(), port, timeout=10)
            server.quit()
            self.smtp_test_result = "Connection successful."
        except Exception as e:
            self.smtp_test_result = f"Connection failed: {e}"
        finally:
            self.smtp_is_testing = False

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
        self.pref_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.notification.notification_service import NotificationService
                user = await self._get_current_user()
                if user is None:
                    return
                pref = NotificationService.get_or_create_preference(str(user.id))
                self.pref_enabled = pref.email_reminders_enabled
                self.pref_days = list(pref.reminder_days or [])
        except Exception as e:
            print(f"[NotificationsState] Failed to load preferences: {e}")
            self.pref_error = f"Failed to load preferences: {e}"

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
        pass

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
            with await self.authenticate_user():
                from gws_care.doctor.medical_doctor_service import MedicalDoctorService
                doctors = MedicalDoctorService.list_doctors(active_only=True)
                f = self.doc_picker_filter.strip().lower()
                self.doc_picker_rows = [
                    DoctorPickerRowDTO(
                        id=d.id,
                        full_name=d.full_name,
                        specialization=d.specialization or "",
                    )
                    for d in doctors
                    if not f or f in d.full_name.lower() or f in (d.specialization or "").lower()
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
                elif self.compose_mode == "doctor":
                    from gws_care.doctor.medical_doctor import MedicalDoctor
                    from gws_care.notification.notification_enums import (
                        NotificationChannel,
                        NotificationStatus,
                        NotificationType,
                    )
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
                    )
                    success = NotificationService._dispatch(
                        NotificationChannel.EMAIL.value,
                        doc.email, doc.phone, doc.get_full_name(),
                        self.compose_subject, self.compose_body,
                    )
                    NotificationService._finalise_log(log, success)
                    self.send_success = f"Message sent to {doc.get_full_name()}."
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


