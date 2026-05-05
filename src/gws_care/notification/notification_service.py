"""Notification service: send emails, SMS, WhatsApp via Brevo or SMTP, store logs."""

from __future__ import annotations

from gws_core import BadRequestException

from gws_care.notification.notification_dto import (
    BrevoConfigDTO,
    NotificationPreferenceDTO,
    SendCustomMessageDTO,
    SendManualNotificationDTO,
)
from gws_care.notification.notification_enums import (
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)
from gws_care.notification.notification_models import (
    NotificationBell,
    NotificationLog,
    NotificationPreference,
)
from gws_care.user.user import User


class NotificationService:
    """Core notification service: send, log and inspect notifications."""

    # ── Email delivery (SMTP) ─────────────────────────────────────────────────

    @classmethod
    def _send_email(cls, to_email: str, subject: str, body: str) -> bool:
        """Attempt to send a plain-text email via the configured SMTP server.

        Reads SmtpConfig from the database. Returns True on success, False on failure.
        If no SMTP host is configured, logs a warning and returns False.
        """
        import smtplib
        from email.mime.text import MIMEText

        try:
            from gws_care.notification.notification_models import SmtpConfig
            config = SmtpConfig.get_or_none()
            if config is None or not config.host:
                print("[NotificationService] No SMTP host configured — email not sent.")
                return False

            from_addr = config.from_email or config.username or "noreply@constellab.care"
            from_name = config.from_name or "Constellab Care"

            msg = MIMEText(body, "plain", "utf-8")
            msg["Subject"] = subject
            msg["From"] = f"{from_name} <{from_addr}>"
            msg["To"] = to_email

            port = config.port if config.port else 587
            if config.use_tls:
                server = smtplib.SMTP(config.host, port, timeout=15)
                server.starttls()
            else:
                server = smtplib.SMTP(config.host, port, timeout=15)

            # Resolve credentials from Constellab Credentials store
            smtp_username = config.username
            smtp_password = None
            if config.credentials_name:
                try:
                    from gws_core.credentials.credentials import Credentials
                    from gws_core.credentials.credentials_type import CredentialsType
                    creds = Credentials.find_by_name_and_check(
                        config.credentials_name, CredentialsType.BASIC
                    )
                    basic = creds.get_data_object()
                    smtp_username = basic.username or smtp_username
                    smtp_password = basic.password
                except Exception as cred_exc:
                    print(f"[NotificationService] Could not load credentials '{config.credentials_name}': {cred_exc}")

            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)

            server.sendmail(from_addr, [to_email], msg.as_string())
            server.quit()
            return True
        except Exception as exc:
            print(f"[NotificationService] Email send failed to {to_email}: {exc}")
            return False

    # ── Brevo helpers ─────────────────────────────────────────────────────────

    @classmethod
    def _get_brevo_api_key(cls) -> str | None:
        """Resolve the Brevo API key from Constellab Credentials. Returns None if not configured."""
        from gws_care.notification.notification_models import BrevoConfig
        config = BrevoConfig.get_or_none()
        if config is None or not config.credentials_name:
            return None
        try:
            from gws_core.credentials.credentials import Credentials
            from gws_core.credentials.credentials_type import CredentialsType
            creds = Credentials.find_by_name_and_check(config.credentials_name, CredentialsType.BASIC)
            basic = creds.get_data_object()
            return basic.password
        except Exception as exc:
            print(f"[NotificationService] Could not load Brevo credentials: {exc}")
            return None

    @classmethod
    def _send_brevo_email(cls, to_email: str, to_name: str | None, subject: str, body: str) -> bool:
        """Send a transactional email via the Brevo API."""
        import json
        import urllib.request

        api_key = cls._get_brevo_api_key()
        if not api_key:
            print("[NotificationService] Brevo API key not configured — email not sent.")
            return False

        from gws_care.notification.notification_models import BrevoConfig
        config = BrevoConfig.get_or_none()
        from_email = (config.from_email if config else None) or "noreply@constellab.care"
        from_name = (config.from_name if config else None) or "Constellab Care"

        payload = json.dumps({
            "sender": {"name": from_name, "email": from_email},
            "to": [{"email": to_email, "name": to_name or ""}],
            "subject": subject,
            "textContent": body,
        }).encode("utf-8")

        try:
            req = urllib.request.Request(
                "https://api.brevo.com/v3/smtp/email",
                data=payload,
                headers={"api-key": api_key, "content-type": "application/json", "accept": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status < 300
        except Exception as exc:
            print(f"[NotificationService] Brevo email failed to {to_email}: {exc}")
            return False

    @classmethod
    def _send_brevo_sms(cls, to_phone: str, body: str) -> bool:
        """Send a transactional SMS via the Brevo API. to_phone must be E.164 (e.g. +33612345678)."""
        import json
        import urllib.request

        api_key = cls._get_brevo_api_key()
        if not api_key:
            print("[NotificationService] Brevo API key not configured — SMS not sent.")
            return False

        from gws_care.notification.notification_models import BrevoConfig
        config = BrevoConfig.get_or_none()
        sender = (config.sms_sender if config else None) or "ConstellCare"

        payload = json.dumps({
            "sender": sender,
            "recipient": to_phone,
            "content": body,
            "type": "transactional",
        }).encode("utf-8")

        try:
            req = urllib.request.Request(
                "https://api.brevo.com/v3/transactionalSMS/sms",
                data=payload,
                headers={"api-key": api_key, "content-type": "application/json", "accept": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status < 300
        except Exception as exc:
            print(f"[NotificationService] Brevo SMS failed to {to_phone}: {exc}")
            return False

    @classmethod
    def _send_brevo_whatsapp(cls, to_phone: str, body: str) -> bool:
        """Send a transactional WhatsApp message via the Brevo API. to_phone must be E.164."""
        import json
        import urllib.request

        api_key = cls._get_brevo_api_key()
        if not api_key:
            print("[NotificationService] Brevo API key not configured — WhatsApp not sent.")
            return False

        payload = json.dumps({
            "recipientPhoneNumber": to_phone,
            "text": body,
        }).encode("utf-8")

        try:
            req = urllib.request.Request(
                "https://api.brevo.com/v3/whatsapp/sendMessage",
                data=payload,
                headers={"api-key": api_key, "content-type": "application/json", "accept": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status < 300
        except Exception as exc:
            print(f"[NotificationService] Brevo WhatsApp failed to {to_phone}: {exc}")
            return False

    @classmethod
    def _dispatch(
        cls,
        channel: str,
        to_email: str | None,
        to_phone: str | None,
        to_name: str | None,
        subject: str,
        body: str,
    ) -> bool:
        """Route a message to the appropriate transport based on channel."""
        if channel == NotificationChannel.SMS.value:
            if not to_phone:
                print("[NotificationService] SMS requested but no phone number available.")
                return False
            return cls._send_brevo_sms(to_phone, body)
        elif channel == NotificationChannel.WHATSAPP.value:
            if not to_phone:
                print("[NotificationService] WhatsApp requested but no phone number available.")
                return False
            return cls._send_brevo_whatsapp(to_phone, body)
        else:
            # Default: email — try Brevo first, fall back to SMTP
            brevo_key = cls._get_brevo_api_key()
            if brevo_key and to_email:
                return cls._send_brevo_email(to_email, to_name, subject, body)
            elif to_email:
                return cls._send_email(to_email, subject, body)
            else:
                print("[NotificationService] Email requested but no email address available.")
                return False

    # ── Logging helpers ───────────────────────────────────────────────────────

    @classmethod
    def _create_log(
        cls,
        notification_type: NotificationType,
        channel: NotificationChannel,
        subject: str,
        body: str,
        recipient_email: str | None,
        recipient_phone: str | None,
        recipient_name: str | None,
        sent_by: User | None,
        patient=None,
        account=None,
        appointment=None,
        extra_data: dict | None = None,
    ) -> NotificationLog:
        log = NotificationLog()
        log.notification_type = notification_type
        log.channel = channel
        log.status = NotificationStatus.PENDING
        log.subject = subject
        log.body = body
        log.recipient_email = recipient_email
        log.recipient_phone = recipient_phone
        log.recipient_name = recipient_name
        log.sent_by = sent_by
        log.patient = patient
        log.account = account
        log.related_appointment = appointment
        log.extra_data = extra_data
        log.save()
        return log

    @classmethod
    def _finalise_log(cls, log: NotificationLog, success: bool, error: str | None = None) -> None:
        log.status = NotificationStatus.SENT if success else NotificationStatus.FAILED
        log.error_message = error
        log.save()

    # ── Manual sending ────────────────────────────────────────────────────────

    @classmethod
    def send_to_patient(cls, dto: SendCustomMessageDTO, sent_by: User) -> NotificationLog:
        """Send a message to a single patient via the requested channel."""
        from gws_care.patient.patient_service import PatientService

        if not dto.subject.strip():
            raise BadRequestException("Subject is required")
        if not dto.body.strip():
            raise BadRequestException("Message body is required")

        channel = dto.channel or NotificationChannel.EMAIL.value
        patient = PatientService.get_patient(dto.patient_id)

        if channel == NotificationChannel.EMAIL.value and not patient.email:
            raise BadRequestException(
                f"Patient {patient.get_full_name()} has no email address configured."
            )
        if channel in (NotificationChannel.SMS.value, NotificationChannel.WHATSAPP.value) and not patient.phone:
            raise BadRequestException(
                f"Patient {patient.get_full_name()} has no phone number configured."
            )

        log = cls._create_log(
            notification_type=NotificationType.MANUAL_PATIENT,
            channel=NotificationChannel(channel),
            subject=dto.subject,
            body=dto.body,
            recipient_email=patient.email,
            recipient_phone=patient.phone,
            recipient_name=patient.get_full_name(),
            sent_by=sent_by,
            patient=patient,
        )
        success = cls._dispatch(channel, patient.email, patient.phone, patient.get_full_name(), dto.subject, dto.body)
        cls._finalise_log(log, success)
        return log

    @classmethod
    def send_to_account(cls, dto: SendManualNotificationDTO, sent_by: User) -> list[NotificationLog]:
        """Send a message to all patients linked to an account via the requested channel."""
        from gws_care.account.account_service import AccountService
        from gws_care.patient.patient_service import PatientService

        if not dto.subject.strip():
            raise BadRequestException("Subject is required")
        if not dto.body.strip():
            raise BadRequestException("Message body is required")
        if not dto.account_id:
            raise BadRequestException("Account is required")

        channel = dto.channel or NotificationChannel.EMAIL.value
        account = AccountService.get_account(dto.account_id)
        patients = PatientService.list_patients_for_account(dto.account_id)
        logs = []

        for patient in patients:
            use_phone = channel in (NotificationChannel.SMS.value, NotificationChannel.WHATSAPP.value)
            if use_phone and not patient.phone:
                continue
            if not use_phone and not patient.email:
                continue

            log = cls._create_log(
                notification_type=NotificationType.MANUAL_ACCOUNT,
                channel=NotificationChannel(channel),
                subject=dto.subject,
                body=dto.body,
                recipient_email=patient.email,
                recipient_phone=patient.phone,
                recipient_name=patient.get_full_name(),
                sent_by=sent_by,
                patient=patient,
                account=account,
            )
            success = cls._dispatch(channel, patient.email, patient.phone, patient.get_full_name(), dto.subject, dto.body)
            cls._finalise_log(log, success)
            logs.append(log)

        return logs

    # ── Appointment reminders ─────────────────────────────────────────────────

    @classmethod
    def send_appointment_reminder(
        cls, appointment, days_before: int, sent_by: User | None = None
    ) -> NotificationLog | None:
        """Send a reminder email for a single appointment.

        Returns None if the patient has no email.
        """
        patient = appointment.patient
        if not patient.email:
            return None

        subject = f"Appointment reminder – {days_before} day(s) to go"
        body = (
            f"Dear {patient.get_full_name()},\n\n"
            f"This is a reminder that you have an appointment scheduled on "
            f"{appointment.scheduled_at.strftime('%A %d %B %Y at %H:%M')}.\n\n"
            f"Exam type: {appointment.exam_type.get_label()}\n\n"
            f"Please contact us if you need to reschedule.\n\nBest regards,\nConstellab Care"
        )

        log = cls._create_log(
            notification_type=NotificationType.APPOINTMENT_REMINDER,
            channel=NotificationChannel.EMAIL,
            subject=subject,
            body=body,
            recipient_email=patient.email,
            recipient_phone=patient.phone,
            recipient_name=patient.get_full_name(),
            sent_by=sent_by,
            patient=patient,
            appointment=appointment,
            extra_data={"days_before": days_before},
        )
        success = cls._dispatch(NotificationChannel.EMAIL.value, patient.email, patient.phone, patient.get_full_name(), subject, body)
        cls._finalise_log(log, success)
        return log

    @classmethod
    def process_appointment_reminders(cls, user: User) -> int:
        """Send reminders for all upcoming appointments matching user preferences.

        Skips appointments that already have a reminder logged for the same
        (appointment_id, days_before) combination today.

        Returns the number of reminders dispatched.
        """
        from datetime import date, timedelta

        pref = cls.get_or_create_preference(str(user.id))
        if not pref.email_reminders_enabled or not pref.reminder_days:
            return 0

        from gws_care.appointment.appointment import Appointment
        from gws_care.appointment.appointment_status import AppointmentStatus

        count = 0
        today = date.today()

        for days in pref.reminder_days:
            target_date = today + timedelta(days=days)
            target_dt_start = f"{target_date.isoformat()}T00:00:00"
            target_dt_end = f"{target_date.isoformat()}T23:59:59"

            upcoming = list(
                Appointment.select()
                .where(
                    Appointment.scheduled_at >= target_dt_start,
                    Appointment.scheduled_at <= target_dt_end,
                    Appointment.status == AppointmentStatus.SCHEDULED,
                )
            )

            for appt in upcoming:
                # Skip if already sent a reminder for this appt + days combo today
                already_sent = (
                    NotificationLog.select()
                    .where(
                        NotificationLog.related_appointment == appt.id,
                        NotificationLog.notification_type == NotificationType.APPOINTMENT_REMINDER,
                        NotificationLog.status == NotificationStatus.SENT,
                    )
                    .where(
                        NotificationLog.extra_data.cast("CHAR").contains(f'"days_before": {days}')
                    )
                    .exists()
                )
                if already_sent:
                    continue

                cls.send_appointment_reminder(appt, days_before=days, sent_by=user)
                count += 1

        return count

    # ── Preferences ───────────────────────────────────────────────────────────

    @classmethod
    def get_or_create_preference(cls, user_id: str) -> NotificationPreference:
        pref, _ = NotificationPreference.get_or_create(user_id=user_id)
        return pref

    @classmethod
    def save_preference(cls, user_id: str, dto: NotificationPreferenceDTO) -> NotificationPreference:
        # Validate: days must be positive integers
        for d in dto.reminder_days:
            if not isinstance(d, int) or d <= 0:
                raise BadRequestException("Reminder days must be positive integers")
        pref = cls.get_or_create_preference(user_id)
        pref.reminder_days = sorted(set(dto.reminder_days), reverse=True)
        pref.email_reminders_enabled = dto.email_reminders_enabled
        pref.save()
        return pref

    # ── History ───────────────────────────────────────────────────────────────

    @classmethod
    def list_logs(
        cls,
        patient_id: str | None = None,
        account_id: str | None = None,
        notification_type: str | None = None,
        limit: int = 100,
    ) -> list[NotificationLog]:
        query = NotificationLog.select().order_by(NotificationLog.created_at.desc())
        if patient_id:
            query = query.where(NotificationLog.patient == patient_id)
        if account_id:
            query = query.where(NotificationLog.account == account_id)
        if notification_type and notification_type != "ALL":
            query = query.where(NotificationLog.notification_type == notification_type)
        return list(query.limit(limit))

    # ── Bell notifications ────────────────────────────────────────────────────

    @classmethod
    def get_bell_notifications(cls, user_id: str, unread_only: bool = False) -> list[NotificationBell]:
        query = (
            NotificationBell.select()
            .where(NotificationBell.user == user_id)
            .order_by(NotificationBell.created_at.desc())
            .limit(50)
        )
        if unread_only:
            query = query.where(NotificationBell.is_read == False)
        return list(query)

    @classmethod
    def mark_all_read(cls, user_id: str) -> None:
        NotificationBell.update(is_read=True).where(
            NotificationBell.user == user_id,
            NotificationBell.is_read == False,
        ).execute()

    @classmethod
    def mark_bell_read(cls, bell_id: str) -> None:
        NotificationBell.update(is_read=True).where(NotificationBell.id == bell_id).execute()

    @classmethod
    def create_bell(cls, user_id: str, message: str, log: NotificationLog | None = None) -> NotificationBell:
        bell = NotificationBell()
        bell.user_id = user_id
        bell.message = message
        bell.is_read = False
        bell.related_log = log
        bell.save()
        return bell

    @classmethod
    def unread_count(cls, user_id: str) -> int:
        return (
            NotificationBell.select()
            .where(NotificationBell.user == user_id, NotificationBell.is_read == False)
            .count()
        )

    # ── SMTP Configuration ────────────────────────────────────────────────────

    @classmethod
    def get_smtp_config(cls):
        """Return the current SMTP configuration as a SmtpConfigDTO."""
        from gws_care.notification.notification_dto import SmtpConfigDTO
        from gws_care.notification.notification_models import SmtpConfig

        record = SmtpConfig.get_or_none()
        if record is None:
            return SmtpConfigDTO()
        return SmtpConfigDTO(
            host=record.host or "",
            port=record.port if record.port is not None else 587,
            username=record.username or "",
            credentials_name=record.credentials_name or "",
            use_tls=record.use_tls,
            from_email=record.from_email or "",
            from_name=record.from_name or "",
        )

    @classmethod
    def save_smtp_config(cls, dto) -> None:
        """Persist the SMTP configuration (creates or updates the singleton record)."""
        from gws_care.notification.notification_models import SmtpConfig

        record = SmtpConfig.get_or_none()
        if record is None:
            record = SmtpConfig()
        record.host = dto.host
        record.port = dto.port
        record.username = dto.username
        record.credentials_name = dto.credentials_name
        record.use_tls = dto.use_tls
        record.from_email = dto.from_email
        record.from_name = dto.from_name
        record.save()

    # ── Brevo Configuration ───────────────────────────────────────────────────

    @classmethod
    def get_brevo_config(cls) -> BrevoConfigDTO:
        """Return the current Brevo configuration as a BrevoConfigDTO."""
        from gws_care.notification.notification_models import BrevoConfig

        record = BrevoConfig.get_or_none()
        if record is None:
            return BrevoConfigDTO()
        return BrevoConfigDTO(
            credentials_name=record.credentials_name or "",
            from_email=record.from_email or "",
            from_name=record.from_name or "",
            sms_sender=record.sms_sender or "",
        )

    @classmethod
    def save_brevo_config(cls, dto: BrevoConfigDTO) -> None:
        """Persist the Brevo configuration (creates or updates the singleton record)."""
        from gws_care.notification.notification_models import BrevoConfig

        record = BrevoConfig.get_or_none()
        if record is None:
            record = BrevoConfig()
        record.credentials_name = dto.credentials_name
        record.from_email = dto.from_email
        record.from_name = dto.from_name
        record.sms_sender = dto.sms_sender
        record.save()


