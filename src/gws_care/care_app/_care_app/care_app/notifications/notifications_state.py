"""State for the Notifications page (history + preferences + compose)."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class NotificationLogRow(BaseModel):
    id: str
    created_at: str
    notification_type: str
    channel: str
    status: str
    recipient_name: str
    recipient_email: str
    subject: str
    sent_by_name: str


class AccountOption(BaseModel):
    id: str
    name: str


class PatientOption(BaseModel):
    id: str
    display: str   # "LAST First (PAT-XXXX)"
    email: str


class NotificationsState(ReflexMainState):
    """State for the /notifications page."""

    # ── History tab ───────────────────────────────────────────────────────────
    logs: list[NotificationLogRow] = []
    is_loading_logs: bool = False
    filter_type: str = "ALL"
    sort_column: str = "created_at"
    sort_ascending: bool = False

    # ── Preferences tab ───────────────────────────────────────────────────────
    pref_enabled: bool = True
    pref_new_day: str = ""          # input field for adding a new reminder day
    pref_days: list[int] = []
    is_saving_pref: bool = False
    pref_success: str = ""
    pref_error: str = ""

    # ── Compose tab ───────────────────────────────────────────────────────────
    compose_mode: str = "patient"   # "patient" | "account"
    compose_channel: str = "EMAIL"   # "EMAIL" | "SMS" | "WHATSAPP"
    compose_patient_id: str = ""
    compose_account_id: str = ""
    compose_subject: str = ""
    compose_body: str = ""
    is_sending: bool = False
    send_success: str = ""
    send_error: str = ""

    # ── Selects ───────────────────────────────────────────────────────────────
    patients: list[PatientOption] = []
    accounts: list[AccountOption] = []

    # ── Reminders ─────────────────────────────────────────────────────────────
    reminder_result: str = ""
    is_processing_reminders: bool = False

    # ── SMTP Configuration ────────────────────────────────────────────────────
    smtp_host: str = ""
    smtp_port: str = "587"
    smtp_username: str = ""
    smtp_credentials_name: str = ""
    smtp_use_tls: bool = True
    smtp_from_email: str = ""
    smtp_from_name: str = ""
    is_saving_smtp: bool = False
    smtp_success: str = ""
    smtp_error: str = ""

    # ── Brevo Configuration ───────────────────────────────────────────────────
    brevo_credentials_name: str = ""
    brevo_from_email: str = ""
    brevo_from_name: str = ""
    brevo_sms_sender: str = ""
    is_saving_brevo: bool = False
    brevo_success: str = ""
    brevo_error: str = ""

    # ── Active tab ────────────────────────────────────────────────────────────
    active_tab: str = "history"

    @rx.event
    async def on_load(self):
        await self._load_patients_and_accounts()
        await self._load_logs()
        await self._load_preferences()
        await self._load_smtp_config()
        await self._load_brevo_config()

    @rx.event
    async def set_active_tab(self, tab: str):
        self.active_tab = tab

    # ── History ───────────────────────────────────────────────────────────────

    @rx.event
    async def set_filter_type(self, value: str):
        self.filter_type = value
        await self._load_logs()

    @rx.event
    async def set_sort(self, column: str):
        """Sort by column; toggle direction if already sorted by the same column."""
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column
            self.sort_ascending = True
        await self._load_logs()

    async def _load_logs(self):
        self.is_loading_logs = True
        try:
            with await self.authenticate_user():
                from gws_care.notification.notification_service import NotificationService
                logs = NotificationService.list_logs(
                    notification_type=self.filter_type if self.filter_type != "ALL" else None,
                )
                rows = [
                    NotificationLogRow(
                        id=str(l.id),
                        created_at=l.created_at.strftime("%Y-%m-%d %H:%M") if l.created_at else "",
                        notification_type=l.notification_type.value,
                        channel=l.channel.value,
                        status=l.status.value,
                        recipient_name=l.recipient_name or "—",
                        recipient_email=l.recipient_email or "—",
                        subject=l.subject,
                        sent_by_name=(
                            f"{l.sent_by.first_name} {l.sent_by.last_name}"
                            if l.sent_by_id else "System"
                        ),
                    )
                    for l in logs
                ]
                sort_col = self.sort_column
                self.logs = sorted(
                    rows,
                    key=lambda row: (getattr(row, sort_col) or "").lower(),
                    reverse=not self.sort_ascending,
                )
        except Exception as e:
            self.logs = []
        finally:
            self.is_loading_logs = False

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
            await self._load_logs()
        except Exception as e:
            self.reminder_result = f"Error: {e}"
        finally:
            self.is_processing_reminders = False

    # ── Compose ───────────────────────────────────────────────────────────────

    @rx.event
    async def set_compose_mode(self, value: str | list[str]):
        self.compose_mode = value if isinstance(value, str) else value[0]
        self.compose_patient_id = ""
        self.compose_account_id = ""
        self.send_success = ""
        self.send_error = ""

    @rx.event
    async def set_compose_channel(self, value: str | list[str]):
        self.compose_channel = value if isinstance(value, str) else value[0]
        self.send_success = ""
        self.send_error = ""

    @rx.event
    async def set_compose_patient(self, value: str):
        self.compose_patient_id = value

    @rx.event
    async def set_compose_account(self, value: str):
        self.compose_account_id = value

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
                from gws_care.notification.notification_service import NotificationService
                user = await self._get_current_user()
                if user is None:
                    self.send_error = "Could not identify current user."
                    return

                if self.compose_mode == "patient":
                    from gws_care.notification.notification_dto import SendCustomMessageDTO
                    NotificationService.send_to_patient(
                        SendCustomMessageDTO(
                            patient_id=self.compose_patient_id,
                            subject=self.compose_subject,
                            body=self.compose_body,
                            channel=self.compose_channel,
                        ),
                        sent_by=user,
                    )
                    self.send_success = "Message sent to patient."
                else:
                    from gws_care.notification.notification_dto import SendManualNotificationDTO
                    logs = NotificationService.send_to_account(
                        SendManualNotificationDTO(
                            account_id=self.compose_account_id,
                            subject=self.compose_subject,
                            body=self.compose_body,
                            channel=self.compose_channel,
                        ),
                        sent_by=user,
                    )
                    sent_count = sum(1 for l in logs if l.status.value == "SENT")
                    self.send_success = f"Message sent to {sent_count} recipient(s)."

                self.compose_subject = ""
                self.compose_body = ""
            await self._load_logs()
        except Exception as e:
            self.send_error = f"Error: {e}"
        finally:
            self.is_sending = False

    # ── Loaders ───────────────────────────────────────────────────────────────

    async def _load_smtp_config(self):
        try:
            from gws_care.notification.notification_service import NotificationService
            cfg = NotificationService.get_smtp_config()
            self.smtp_host = cfg.host
            self.smtp_port = str(cfg.port)
            self.smtp_username = cfg.username
            self.smtp_credentials_name = cfg.credentials_name
            self.smtp_use_tls = cfg.use_tls
            self.smtp_from_email = cfg.from_email
            self.smtp_from_name = cfg.from_name
        except Exception:
            pass

    @rx.event
    async def set_smtp_host(self, value: str):
        self.smtp_host = value

    @rx.event
    async def set_smtp_port(self, value: str):
        self.smtp_port = value

    @rx.event
    async def set_smtp_username(self, value: str):
        self.smtp_username = value

    @rx.event
    async def set_smtp_credentials_name(self, value: str):
        self.smtp_credentials_name = value

    @rx.event
    async def set_smtp_use_tls(self, value: bool):
        self.smtp_use_tls = value

    @rx.event
    async def set_smtp_from_email(self, value: str):
        self.smtp_from_email = value

    @rx.event
    async def set_smtp_from_name(self, value: str):
        self.smtp_from_name = value

    @rx.event
    async def save_smtp_config(self):
        self.is_saving_smtp = True
        self.smtp_success = ""
        self.smtp_error = ""
        try:
            from gws_care.notification.notification_dto import SmtpConfigDTO
            from gws_care.notification.notification_service import NotificationService
            try:
                port = int(self.smtp_port)
            except (ValueError, TypeError):
                self.smtp_error = "Port must be a valid integer."
                return
            NotificationService.save_smtp_config(SmtpConfigDTO(
                host=self.smtp_host,
                port=port,
                username=self.smtp_username,
                credentials_name=self.smtp_credentials_name,
                use_tls=self.smtp_use_tls,
                from_email=self.smtp_from_email,
                from_name=self.smtp_from_name,
            ))
            self.smtp_success = "SMTP configuration saved."
        except Exception as e:
            self.smtp_error = f"Error: {e}"
        finally:
            self.is_saving_smtp = False

    # ── Brevo config loaders / setters ────────────────────────────────────────

    async def _load_brevo_config(self):
        try:
            from gws_care.notification.notification_service import NotificationService
            cfg = NotificationService.get_brevo_config()
            self.brevo_credentials_name = cfg.credentials_name
            self.brevo_from_email = cfg.from_email
            self.brevo_from_name = cfg.from_name
            self.brevo_sms_sender = cfg.sms_sender
        except Exception:
            pass

    @rx.event
    async def set_brevo_credentials_name(self, value: str):
        self.brevo_credentials_name = value

    @rx.event
    async def set_brevo_from_email(self, value: str):
        self.brevo_from_email = value

    @rx.event
    async def set_brevo_from_name(self, value: str):
        self.brevo_from_name = value

    @rx.event
    async def set_brevo_sms_sender(self, value: str):
        self.brevo_sms_sender = value

    @rx.event
    async def save_brevo_config(self):
        self.is_saving_brevo = True
        self.brevo_success = ""
        self.brevo_error = ""
        try:
            from gws_care.notification.notification_dto import BrevoConfigDTO
            from gws_care.notification.notification_service import NotificationService
            NotificationService.save_brevo_config(BrevoConfigDTO(
                credentials_name=self.brevo_credentials_name,
                from_email=self.brevo_from_email,
                from_name=self.brevo_from_name,
                sms_sender=self.brevo_sms_sender,
            ))
            self.brevo_success = "Brevo configuration saved."
        except Exception as e:
            self.brevo_error = f"Error: {e}"
        finally:
            self.is_saving_brevo = False

    async def _load_patients_and_accounts(self):
        try:
            with await self.authenticate_user():
                from gws_care.account.account_service import AccountService
                from gws_care.patient.patient_service import PatientService
                self.accounts = [
                    AccountOption(id=str(a.id), name=a.name)
                    for a in AccountService.list_accounts()
                ]
                self.patients = [
                    PatientOption(
                        id=str(p.id),
                        display=f"{p.last_name} {p.first_name} ({p.patient_number})",
                        email=p.email or "",
                    )
                    for p in PatientService.search_patients()
                ]
        except Exception:
            pass
