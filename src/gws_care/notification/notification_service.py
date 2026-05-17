"""Notification service: send emails via SMTP, store logs."""

from __future__ import annotations

from gws_core import BadRequestException

from gws_care.notification.notification_dto import (
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

    @classmethod
    def _send_email_with_attachment(
        cls,
        to_email: str,
        subject: str,
        body: str,
        pdf_bytes: bytes,
        filename: str,
    ) -> bool:
        """Send an email with a PDF attachment via the configured SMTP server."""
        import smtplib
        from email import encoders
        from email.mime.base import MIMEBase
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        try:
            from gws_care.notification.notification_models import SmtpConfig
            config = SmtpConfig.get_or_none()
            if config is None or not config.host:
                print("[NotificationService] No SMTP host configured — email not sent.")
                return False

            from_addr = config.from_email or config.username or "noreply@constellab.care"
            from_name = config.from_name or "Constellab Care"

            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"] = f"{from_name} <{from_addr}>"
            msg["To"] = to_email
            msg.attach(MIMEText(body, "plain", "utf-8"))

            part = MIMEBase("application", "pdf")
            part.set_payload(pdf_bytes)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment", filename=filename)
            msg.attach(part)

            port = config.port if config.port else 587
            if config.use_tls:
                server = smtplib.SMTP(config.host, port, timeout=15)
                server.starttls()
            else:
                server = smtplib.SMTP(config.host, port, timeout=15)

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
            print(f"[NotificationService] Email (with attachment) send failed to {to_email}: {exc}")
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
        """Route an email message via SMTP."""
        # Only EMAIL channel is supported
        if to_email:
            return cls._send_email(to_email, subject, body)
        else:
            print("[NotificationService] Email requested but no email address available.")
            return False

    @classmethod
    def _dispatch_with_pdf(
        cls,
        to_email: str,
        to_name: str | None,
        subject: str,
        body: str,
        pdf_bytes: bytes,
        filename: str,
    ) -> bool:
        """Send email with PDF attachment via SMTP."""
        return cls._send_email_with_attachment(to_email, subject, body, pdf_bytes, filename)

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
        """Send an email message to a single patient."""
        from gws_care.patient.patient_service import PatientService

        if not dto.subject.strip():
            raise BadRequestException("Subject is required")
        if not dto.body.strip():
            raise BadRequestException("Message body is required")

        patient = PatientService.get_patient(dto.patient_id)

        if not patient.email:
            raise BadRequestException(
                f"Patient {patient.get_full_name()} has no email address configured."
            )

        log = cls._create_log(
            notification_type=NotificationType.MANUAL_PATIENT,
            channel=NotificationChannel.EMAIL,
            subject=dto.subject,
            body=dto.body,
            recipient_email=patient.email,
            recipient_phone=patient.phone,
            recipient_name=patient.get_full_name(),
            sent_by=sent_by,
            patient=patient,
        )
        success = cls._dispatch(
            NotificationChannel.EMAIL.value,
            patient.email,
            patient.phone,
            patient.get_full_name(),
            dto.subject,
            dto.body,
        )
        cls._finalise_log(log, success)
        return log

    @classmethod
    def send_pdf_to_patient(
        cls,
        patient_id: str,
        subject: str,
        body: str,
        pdf_bytes: bytes,
        filename: str,
        sent_by: User | None = None,
    ) -> NotificationLog:
        """Send an email with a PDF attachment to a patient."""
        from gws_care.patient.patient_service import PatientService

        patient = PatientService.get_patient(patient_id)
        if not patient.email:
            raise BadRequestException(
                f"Patient {patient.get_full_name()} has no email address configured."
            )

        log = cls._create_log(
            notification_type=NotificationType.MANUAL_PATIENT,
            channel=NotificationChannel.EMAIL,
            subject=subject,
            body=body,
            recipient_email=patient.email,
            recipient_phone=patient.phone,
            recipient_name=patient.get_full_name(),
            sent_by=sent_by,
            patient=patient,
        )
        success = cls._dispatch_with_pdf(
            patient.email,
            patient.get_full_name(),
            subject,
            body,
            pdf_bytes,
            filename,
        )
        cls._finalise_log(log, success)
        return log

    @classmethod
    def send_to_account(cls, dto: SendManualNotificationDTO, sent_by: User) -> list[NotificationLog]:
        """Send an email message to all patients linked to an account."""
        from gws_care.account.account_service import AccountService
        from gws_care.patient.patient_service import PatientService

        if not dto.subject.strip():
            raise BadRequestException("Subject is required")
        if not dto.body.strip():
            raise BadRequestException("Message body is required")
        if not dto.account_id:
            raise BadRequestException("Account is required")

        account = AccountService.get_account(dto.account_id)
        patients = PatientService.list_patients_for_account(dto.account_id)
        logs = []

        for patient in patients:
            if not patient.email:
                continue

            log = cls._create_log(
                notification_type=NotificationType.MANUAL_ACCOUNT,
                channel=NotificationChannel.EMAIL,
                subject=dto.subject,
                body=dto.body,
                recipient_email=patient.email,
                recipient_phone=patient.phone,
                recipient_name=patient.get_full_name(),
                sent_by=sent_by,
                patient=patient,
                account=account,
            )
            success = cls._dispatch(
                NotificationChannel.EMAIL.value,
                patient.email,
                patient.phone,
                patient.get_full_name(),
                dto.subject,
                dto.body,
            )
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

    # ── Phase 5 — Typed appointment reminders (J-15, J-3, J-1) ──────────────

    # Map: days_before → NotificationType (for idempotency)
    _REMINDER_TYPE_MAP = {
        15: NotificationType.APPOINTMENT_REMINDER_15D,
        3: NotificationType.APPOINTMENT_REMINDER_3D,
        1: NotificationType.APPOINTMENT_REMINDER_1D,
    }

    @classmethod
    def send_daily_appointment_reminders(cls) -> int:
        """
        Daily scheduler method: send appointment reminders at J-15, J-3, and J-1.

        Each reminder is idempotent — a second call on the same day for the same
        (appointment, NotificationType) pair will be skipped.

        Returns the number of reminders dispatched.
        """
        from datetime import date, timedelta

        from gws_care.appointment.appointment import Appointment
        from gws_care.appointment.appointment_status import AppointmentStatus

        count = 0
        today = date.today()

        for days_before, notif_type in cls._REMINDER_TYPE_MAP.items():
            target_date = today + timedelta(days=days_before)
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
                # Skip if already attempted this typed reminder for this appointment
                already_sent = (
                    NotificationLog.select()
                    .where(
                        NotificationLog.related_appointment == appt.id,
                        NotificationLog.notification_type == notif_type,
                    )
                    .exists()
                )
                if already_sent:
                    continue

                patient = appt.patient
                if not patient.email:
                    continue

                subject = f"[Constellab Care] Rappel de rendez-vous — J-{days_before}"
                body = (
                    f"Cher(e) {patient.get_full_name()},\n\n"
                    f"Nous vous rappelons que vous avez un rendez-vous prévu dans {days_before} jour(s), "
                    f"le {appt.scheduled_at.strftime('%A %d %B %Y à %H:%M')}.\n\n"
                    f"Type d'examen : {appt.exam_type.get_label()}\n\n"
                    f"Contactez-nous si vous devez modifier ce rendez-vous.\n\nCordialement,\nConstellab Care"
                )

                log = cls._create_log(
                    notification_type=notif_type,
                    channel=NotificationChannel.EMAIL,
                    subject=subject,
                    body=body,
                    recipient_email=patient.email,
                    recipient_phone=patient.phone,
                    recipient_name=patient.get_full_name(),
                    sent_by=None,
                    patient=patient,
                    appointment=appt,
                    extra_data={"days_before": days_before},
                )
                success = cls._dispatch(
                    NotificationChannel.EMAIL.value,
                    patient.email,
                    patient.phone,
                    patient.get_full_name(),
                    subject,
                    body,
                )
                cls._finalise_log(log, success)
                count += 1

        return count

    # ── Phase 5 — Terrain thank-you ───────────────────────────────────────────

    @classmethod
    def send_terrain_thank_you(cls, patient, visit, sent_by: User | None = None) -> None:
        """Email + in-app bell to a patient after their on-site visit is completed."""
        from gws_care.role.care_role import CareRole
        from gws_care.role.user_care_role import UserCareRole

        patient_name = patient.get_full_name()
        subject = "[Constellab Care] Merci pour votre visite on-site"
        body = (
            f"Cher(e) {patient_name},\n\n"
            f"Merci d'avoir participé à la visite on-site #{visit.visit_number}.\n"
            f"Vos prélèvements ont bien été enregistrés. "
            f"Vous serez informé(e) dès que vos résultats seront disponibles.\n\n"
            f"Cordialement,\nConstellab Care"
        )
        message = f"Merci pour votre participation à la visite on-site #{visit.visit_number}."

        log = None
        if patient.email:
            log = cls._create_log(
                notification_type=NotificationType.TERRAIN_THANK_YOU,
                channel=NotificationChannel.EMAIL,
                subject=subject,
                body=body,
                recipient_email=patient.email,
                recipient_phone=patient.phone,
                recipient_name=patient_name,
                sent_by=sent_by,
                patient=patient,
                extra_data={"visit_id": str(visit.id)},
            )
            success = cls._dispatch(NotificationChannel.EMAIL.value, patient.email, patient.phone, patient_name, subject, body)
            cls._finalise_log(log, success)

        # Bell to PATIENT role user linked to this patient
        patient_roles = list(UserCareRole.select().where(
            UserCareRole.role == CareRole.PATIENT,
            UserCareRole.linked_patient_id == str(patient.id),
        ))
        for role_entry in patient_roles:
            cls.create_bell(str(role_entry.user_id), message, log=log)

    # ── Phase 5 — Certificate available ──────────────────────────────────────

    @classmethod
    def notify_certificate_available(cls, certificate, patient, sent_by: User | None = None) -> None:
        """Email + in-app bell to a patient when a medical certificate is issued."""
        from gws_care.role.care_role import CareRole
        from gws_care.role.user_care_role import UserCareRole

        patient_name = patient.get_full_name()
        subject = "[Constellab Care] Votre certificat médical est disponible"
        body = (
            f"Cher(e) {patient_name},\n\n"
            f"Votre certificat médical daté du {certificate.issue_date.strftime('%d/%m/%Y')} "
            f"est maintenant disponible.\n"
            f"Vous pouvez le consulter et le télécharger depuis votre espace Constellab Care.\n\n"
            f"Cordialement,\nConstellab Care"
        )
        message = f"Votre certificat médical du {certificate.issue_date.strftime('%d/%m/%Y')} est disponible."

        log = None
        if patient.email:
            log = cls._create_log(
                notification_type=NotificationType.CERTIFICATE_AVAILABLE,
                channel=NotificationChannel.EMAIL,
                subject=subject,
                body=body,
                recipient_email=patient.email,
                recipient_phone=patient.phone,
                recipient_name=patient_name,
                sent_by=sent_by,
                patient=patient,
                extra_data={"certificate_id": str(certificate.id)},
            )
            success = cls._dispatch(NotificationChannel.EMAIL.value, patient.email, patient.phone, patient_name, subject, body)
            cls._finalise_log(log, success)

        # Bell to PATIENT role user linked to this patient
        patient_roles = list(UserCareRole.select().where(
            UserCareRole.role == CareRole.PATIENT,
            UserCareRole.linked_patient_id == str(patient.id),
        ))
        for role_entry in patient_roles:
            cls.create_bell(str(role_entry.user_id), message, log=log)

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

    # ── Phase 2 — Validation workflow notifications ───────────────────────────

    @classmethod
    def notify_lab_done_to_doctors(cls, program, sent_by: User | None = None) -> None:
        """Bell notification to every DOCTOR user when a program moves to LAB_DONE.

        Also attempts to send an email to each doctor user if an email address is set.
        """
        from gws_care.role.care_role import CareRole
        from gws_care.role.user_care_role import UserCareRole

        campaign_name = program.name
        message = f"La campagne « {campaign_name} » est prête pour validation Clinic Doctor."
        subject = f"[Constellab Care] Program pending validation — {program_name}"
        body = (
            f"Bonjour,\n\n"
            f"La campagne « {campaign_name} » a été validée par le laboratoire.\n"
            f"Tous les résultats sont disponibles et attendent votre validation Clinic Doctor.\n\n"
            f"Veuillez vous connecter à Constellab Care pour procéder.\n\n"
            f"Cordialement,\nConstellab Care"
        )

        log = cls._create_log(
            notification_type=NotificationType.LAB_DONE,
            channel=NotificationChannel.IN_APP,
            subject=subject,
            body=message,
            recipient_email=None,
            recipient_phone=None,
            recipient_name=None,
            sent_by=sent_by,
            extra_data={"program_id": str(program.id)},
        )

        doctor_roles = list(UserCareRole.select(UserCareRole, UserCareRole.user).join(UserCareRole.user.rel_model).where(
            UserCareRole.role == CareRole.DOCTOR
        ))

        for role_entry in doctor_roles:
            cls.create_bell(str(role_entry.user_id), message, log=log)
            user = role_entry.user
            if hasattr(user, "email") and user.email:
                cls._dispatch(NotificationChannel.EMAIL.value, user.email, None, None, subject, body)

    @classmethod
    def notify_clinic_validated_to_account_admins(cls, program, sent_by: User | None = None) -> None:
        """Bell notification to ACCOUNT_ADMIN users of the program's account when clinic validates."""
        from gws_care.role.care_role import CareRole
        from gws_care.role.user_care_role import UserCareRole

        campaign_name = program.name
        account_id = str(program.account_id)
        message = f"La campagne « {campaign_name} » est validée par le Clinic Doctor — vos résultats sont disponibles."
        subject = f"[Constellab Care] Résultats disponibles — {campaign_name}"
        body = (
            f"Bonjour,\n\n"
            f"La campagne « {campaign_name} » a été validée par le Clinic Doctor.\n"
            f"Les résultats sont maintenant disponibles pour validation Company Doctor.\n\n"
            f"Veuillez vous connecter à Constellab Care pour procéder.\n\n"
            f"Cordialement,\nConstellab Care"
        )

        log = cls._create_log(
            notification_type=NotificationType.CAMPAIGN_CLINIC_VALIDATED,
            channel=NotificationChannel.IN_APP,
            subject=subject,
            body=message,
            recipient_email=None,
            recipient_phone=None,
            recipient_name=None,
            sent_by=sent_by,
            extra_data={"program_id": str(program.id)},
        )

        admin_roles = list(UserCareRole.select(UserCareRole, UserCareRole.user).join(UserCareRole.user.rel_model).where(
            UserCareRole.role == CareRole.ACCOUNT_ADMIN,
            UserCareRole.linked_account_id == account_id,
        ))

        for role_entry in admin_roles:
            cls.create_bell(str(role_entry.user_id), message, log=log)
            user = role_entry.user
            if hasattr(user, "email") and user.email:
                cls._dispatch(NotificationChannel.EMAIL.value, user.email, None, None, subject, body)

    @classmethod
    def notify_results_available_to_patient(cls, visit, patient, sent_by: User | None = None) -> None:
        """Email + bell notification to the Patient user when doctor company validates their visit."""
        from gws_care.role.care_role import CareRole
        from gws_care.role.user_care_role import UserCareRole

        patient_name = patient.get_full_name()
        message = f"Vos résultats médicaux sont disponibles — visite #{visit.visit_number}."
        subject = "[Constellab Care] Vos résultats médicaux sont disponibles"
        body = (
            f"Cher(e) {patient_name},\n\n"
            f"Vos résultats médicaux pour la visite #{visit.visit_number} ont été validés "
            f"par le Company Doctor.\n"
            f"Vous pouvez les consulter en vous connectant à votre espace Constellab Care.\n\n"
            f"Cordialement,\nConstellab Care"
        )

        # Email directly to patient
        log = None
        if patient.email:
            log = cls._create_log(
                notification_type=NotificationType.RESULTS_AVAILABLE,
                channel=NotificationChannel.EMAIL,
                subject=subject,
                body=body,
                recipient_email=patient.email,
                recipient_phone=patient.phone,
                recipient_name=patient_name,
                sent_by=sent_by,
                patient=patient,
                extra_data={"visit_id": str(visit.id)},
            )
            success = cls._dispatch(NotificationChannel.EMAIL.value, patient.email, patient.phone, patient_name, subject, body)
            cls._finalise_log(log, success)

        # Bell to the PATIENT role user linked to this patient
        patient_role_entries = list(UserCareRole.select().where(
            UserCareRole.role == CareRole.PATIENT,
            UserCareRole.linked_patient_id == str(patient.id),
        ))
        for role_entry in patient_role_entries:
            cls.create_bell(str(role_entry.user_id), message, log=log)

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



