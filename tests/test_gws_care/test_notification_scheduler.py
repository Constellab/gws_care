"""Unit tests for the notification scheduler (Phase 5).

Covers:
  - send_daily_appointment_reminders: correct J-15, J-3, J-1 targeting
  - Idempotence: duplicate reminder not sent on second call
  - Skips already-done appointments
  - Skips patients without email
  - send_terrain_thank_you: creates log + bell
  - notify_certificate_available: creates log + bell
"""

from datetime import date, datetime, timedelta

from gws_care.account.account_dto import SaveAccountDTO
from gws_care.account.account_service import AccountService
from gws_care.appointment.appointment import Appointment
from gws_care.appointment.appointment_dto import SaveAppointmentDTO
from gws_care.appointment.appointment_service import AppointmentService
from gws_care.appointment.appointment_status import AppointmentStatus
from gws_care.campaign.campaign_dto import SaveCampaignDTO
from gws_care.campaign.campaign_service import CampaignService
from gws_care.certificate.medical_certificate import (
    MedicalCertificate,
    MedicalCertificateService,
    SaveMedicalCertificateDTO,
)
from gws_care.exam.exam_type import ExamType
from gws_care.notification.notification_enums import NotificationStatus, NotificationType
from gws_care.notification.notification_models import NotificationBell, NotificationLog
from gws_care.notification.notification_service import NotificationService
from gws_care.patient.patient_dto import SavePatientDTO
from gws_care.patient.patient_service import PatientService
from gws_care.role.care_role import CareRole
from gws_care.role.user_care_role import UserCareRole
from gws_care.role.user_role_service import UserRoleService
from gws_care.user.care_user_sync_service import CareUserSyncService
from gws_care.user.user import User
from gws_care.visit.campaign_visit_service import CampaignVisitService
from gws_core import BaseTestCase

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_patient_with_email(email: str = "patient@example.com"):
    return PatientService.create_patient(
        SavePatientDTO(
            last_name="Durand",
            first_name="Marie",
            date_of_birth=date(1985, 3, 12),
            gender="F",
            email=email,
            phone="+33600000000",
        )
    )


def _make_account():
    import uuid
    return AccountService.create_account(SaveAccountDTO(name=f"Scheduler Test Acct {uuid.uuid4().hex[:8]}"))


def _make_scheduled_appointment(patient, days_from_now: int) -> Appointment:
    """Create a SCHEDULED appointment exactly *days_from_now* days from today."""
    target_dt = (datetime.now() + timedelta(days=days_from_now)).strftime("%Y-%m-%dT09:00")
    return AppointmentService.create_appointment(
        SaveAppointmentDTO(
            patient_id=str(patient.id),
            scheduled_at=target_dt,
            exam_type=ExamType.CLINICAL.value,
        )
    )


# ── Tests — send_daily_appointment_reminders ──────────────────────────────────

class TestAppointmentReminderScheduler(BaseTestCase):
    """Tests for NotificationService.send_daily_appointment_reminders."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    def _count_logs_for(self, patient, notif_type: NotificationType) -> int:
        return (
            NotificationLog.select()
            .where(
                NotificationLog.patient == patient.id,
                NotificationLog.notification_type == notif_type,
            )
            .count()
        )

    def test_j15_reminder_sent_for_appointment_15_days_out(self):
        """A J-15 reminder is sent for an appointment scheduled 15 days from today."""
        patient = _make_patient_with_email()
        _make_scheduled_appointment(patient, 15)

        count = NotificationService.send_daily_appointment_reminders()
        self.assertGreaterEqual(count, 1)

        logs = self._count_logs_for(patient, NotificationType.APPOINTMENT_REMINDER_15D)
        self.assertEqual(logs, 1)

    def test_j3_reminder_sent_for_appointment_3_days_out(self):
        """A J-3 reminder is sent for an appointment scheduled 3 days from today."""
        patient = _make_patient_with_email()
        _make_scheduled_appointment(patient, 3)

        count = NotificationService.send_daily_appointment_reminders()
        self.assertGreaterEqual(count, 1)

        logs = self._count_logs_for(patient, NotificationType.APPOINTMENT_REMINDER_3D)
        self.assertEqual(logs, 1)

    def test_j1_reminder_sent_for_appointment_1_day_out(self):
        """A J-1 reminder is sent for an appointment scheduled 1 day from today."""
        patient = _make_patient_with_email()
        _make_scheduled_appointment(patient, 1)

        count = NotificationService.send_daily_appointment_reminders()
        self.assertGreaterEqual(count, 1)

        logs = self._count_logs_for(patient, NotificationType.APPOINTMENT_REMINDER_1D)
        self.assertEqual(logs, 1)

    def test_no_reminder_for_appointment_5_days_out(self):
        """No reminder is sent for an appointment 5 days out (not a trigger day)."""
        patient = _make_patient_with_email("other5@example.com")
        _make_scheduled_appointment(patient, 5)

        NotificationService.send_daily_appointment_reminders()

        total_logs = (
            NotificationLog.select()
            .where(NotificationLog.patient == patient.id)
            .count()
        )
        self.assertEqual(total_logs, 0)

    def test_no_reminder_for_appointment_in_the_past(self):
        """No reminder is sent for a past appointment."""
        patient = _make_patient_with_email("past@example.com")
        # Directly create a past appointment bypassing service validation
        past_dt = datetime.now() - timedelta(days=2)
        appt = Appointment()
        appt.patient = patient
        appt.scheduled_at = past_dt
        appt.exam_type = ExamType.CLINICAL
        appt.status = AppointmentStatus.SCHEDULED
        appt.save()

        NotificationService.send_daily_appointment_reminders()

        logs = self._count_logs_for(patient, NotificationType.APPOINTMENT_REMINDER_1D)
        self.assertEqual(logs, 0)

    def test_idempotence_j15_not_sent_twice(self):
        """Calling send_daily_appointment_reminders twice does not duplicate J-15 reminders."""
        patient = _make_patient_with_email("idempotent@example.com")
        _make_scheduled_appointment(patient, 15)

        NotificationService.send_daily_appointment_reminders()
        NotificationService.send_daily_appointment_reminders()

        logs = self._count_logs_for(patient, NotificationType.APPOINTMENT_REMINDER_15D)
        self.assertEqual(logs, 1, "Idempotence: reminder should only appear once")

    def test_idempotence_j3_not_sent_twice(self):
        """J-3 reminder is idempotent."""
        patient = _make_patient_with_email("idem3@example.com")
        _make_scheduled_appointment(patient, 3)

        NotificationService.send_daily_appointment_reminders()
        NotificationService.send_daily_appointment_reminders()

        logs = self._count_logs_for(patient, NotificationType.APPOINTMENT_REMINDER_3D)
        self.assertEqual(logs, 1)

    def test_idempotence_j1_not_sent_twice(self):
        """J-1 reminder is idempotent."""
        patient = _make_patient_with_email("idem1@example.com")
        _make_scheduled_appointment(patient, 1)

        NotificationService.send_daily_appointment_reminders()
        NotificationService.send_daily_appointment_reminders()

        logs = self._count_logs_for(patient, NotificationType.APPOINTMENT_REMINDER_1D)
        self.assertEqual(logs, 1)

    def test_done_appointment_not_reminded(self):
        """A DONE appointment does not trigger a reminder."""
        patient = _make_patient_with_email("done@example.com")
        appt = _make_scheduled_appointment(patient, 15)
        # Mark as done directly
        appt.status = AppointmentStatus.DONE
        appt.save()

        NotificationService.send_daily_appointment_reminders()

        logs = self._count_logs_for(patient, NotificationType.APPOINTMENT_REMINDER_15D)
        self.assertEqual(logs, 0)

    def test_cancelled_appointment_not_reminded(self):
        """A CANCELLED appointment does not trigger a reminder."""
        patient = _make_patient_with_email("cancelled@example.com")
        appt = _make_scheduled_appointment(patient, 3)
        appt.status = AppointmentStatus.CANCELLED
        appt.save()

        NotificationService.send_daily_appointment_reminders()

        logs = self._count_logs_for(patient, NotificationType.APPOINTMENT_REMINDER_3D)
        self.assertEqual(logs, 0)

    def test_patient_without_email_skipped(self):
        """A patient with no email address is not reminded (no log created)."""
        patient = PatientService.create_patient(
            SavePatientDTO(
                last_name="Noemail",
                first_name="Jean",
                date_of_birth=date(1970, 1, 1),
                gender="M",
                email=None,
            )
        )
        _make_scheduled_appointment(patient, 15)

        NotificationService.send_daily_appointment_reminders()

        logs = (
            NotificationLog.select()
            .where(NotificationLog.patient == patient.id)
            .count()
        )
        self.assertEqual(logs, 0)

    def test_returns_count_of_dispatched_reminders(self):
        """The return value equals the number of reminders actually dispatched."""
        patient_a = _make_patient_with_email("count1@example.com")
        patient_b = _make_patient_with_email("count2@example.com")
        _make_scheduled_appointment(patient_a, 15)
        _make_scheduled_appointment(patient_b, 15)

        count = NotificationService.send_daily_appointment_reminders()
        self.assertGreaterEqual(count, 2)

    def test_log_content_j1_contains_patient_name_and_days(self):
        """The J-1 notification log body mentions the patient name and 1 day."""
        patient = _make_patient_with_email("content@example.com")
        _make_scheduled_appointment(patient, 1)

        NotificationService.send_daily_appointment_reminders()

        log = (
            NotificationLog.select()
            .where(
                NotificationLog.patient == patient.id,
                NotificationLog.notification_type == NotificationType.APPOINTMENT_REMINDER_1D,
            )
            .first()
        )
        self.assertIsNotNone(log)
        self.assertIn("Marie", log.body)
        self.assertIn("1", log.body)

    def test_log_notification_type_matches_days(self):
        """A J-15 log has type APPOINTMENT_REMINDER_15D, not 3D or 1D."""
        patient = _make_patient_with_email("typechk@example.com")
        _make_scheduled_appointment(patient, 15)

        NotificationService.send_daily_appointment_reminders()

        log = (
            NotificationLog.select()
            .where(NotificationLog.patient == patient.id)
            .first()
        )
        self.assertIsNotNone(log)
        self.assertEqual(log.notification_type, NotificationType.APPOINTMENT_REMINDER_15D)

    def test_multiple_days_each_patient_gets_own_reminder(self):
        """Two patients with appointments on different trigger days both get reminded."""
        p15 = _make_patient_with_email("p15@example.com")
        p3 = _make_patient_with_email("p3@example.com")
        _make_scheduled_appointment(p15, 15)
        _make_scheduled_appointment(p3, 3)

        NotificationService.send_daily_appointment_reminders()

        self.assertEqual(self._count_logs_for(p15, NotificationType.APPOINTMENT_REMINDER_15D), 1)
        self.assertEqual(self._count_logs_for(p3, NotificationType.APPOINTMENT_REMINDER_3D), 1)
        # No cross-contamination
        self.assertEqual(self._count_logs_for(p15, NotificationType.APPOINTMENT_REMINDER_3D), 0)
        self.assertEqual(self._count_logs_for(p3, NotificationType.APPOINTMENT_REMINDER_15D), 0)


# ── Tests — send_terrain_thank_you ────────────────────────────────────────────

class TestTerrainThankYou(BaseTestCase):
    """Tests for NotificationService.send_terrain_thank_you."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    def _make_visit(self):
        """Returns (patient, visit) with email."""
        account = _make_account()
        patient = _make_patient_with_email("terrain@example.com")
        p = patient
        PatientService.add_account(str(p.id), str(account.id))

        campaign = CampaignService.create_campaign(
            SaveCampaignDTO(
                name="Terrain Camp",
                account_id=str(account.id),
                start_date="2025-09-01",
                end_date="2025-09-30",
            )
        )
        CampaignService.add_patient(str(campaign.id), str(p.id))
        visit = CampaignVisitService.create_visit(str(campaign.id), str(p.id))
        return p, visit

    def test_terrain_thank_you_creates_notification_log(self):
        """send_terrain_thank_you creates a NotificationLog for the patient."""
        patient, visit = self._make_visit()

        NotificationService.send_terrain_thank_you(patient, visit)

        logs = list(
            NotificationLog.select().where(
                NotificationLog.patient == patient.id,
                NotificationLog.notification_type == NotificationType.TERRAIN_THANK_YOU,
            )
        )
        self.assertEqual(len(logs), 1)

    def test_terrain_thank_you_log_contains_visit_number(self):
        """The notification body references the visit number."""
        patient, visit = self._make_visit()

        NotificationService.send_terrain_thank_you(patient, visit)

        log = (
            NotificationLog.select()
            .where(
                NotificationLog.patient == patient.id,
                NotificationLog.notification_type == NotificationType.TERRAIN_THANK_YOU,
            )
            .first()
        )
        self.assertIsNotNone(log)
        self.assertIn(visit.visit_number, log.body)

    def test_terrain_thank_you_creates_bell_for_patient_role_user(self):
        """A bell notification is created for the user linked as PATIENT."""
        patient, visit = self._make_visit()
        user = User.select().first()
        # Link the user to the patient as PATIENT role
        UserRoleService.assign_role(str(user.id), CareRole.PATIENT)
        role_entry = UserCareRole.get(UserCareRole.user == user.id, UserCareRole.role == CareRole.PATIENT)
        role_entry.linked_patient_id = str(patient.id)
        role_entry.save()

        bells_before = NotificationBell.select().count()
        NotificationService.send_terrain_thank_you(patient, visit)
        bells_after = NotificationBell.select().count()

        self.assertGreater(bells_after, bells_before)

    def test_terrain_thank_you_no_log_if_no_email(self):
        """If the patient has no email, no email log is created (but bell may be)."""
        account = _make_account()
        patient_no_email = PatientService.create_patient(
            SavePatientDTO(
                last_name="Noemail",
                first_name="Pierre",
                date_of_birth=date(1970, 1, 1),
                gender="M",
            )
        )
        p = patient_no_email
        PatientService.add_account(str(p.id), str(account.id))

        campaign = CampaignService.create_campaign(
            SaveCampaignDTO(
                name="NoEmail Camp",
                account_id=str(account.id),
                start_date="2025-09-01",
                end_date="2025-09-30",
            )
        )
        CampaignService.add_patient(str(campaign.id), str(p.id))
        visit = CampaignVisitService.create_visit(str(campaign.id), str(p.id))

        NotificationService.send_terrain_thank_you(p, visit)

        email_logs = (
            NotificationLog.select()
            .where(
                NotificationLog.patient == p.id,
                NotificationLog.notification_type == NotificationType.TERRAIN_THANK_YOU,
            )
            .count()
        )
        self.assertEqual(email_logs, 0)


# ── Tests — notify_certificate_available ─────────────────────────────────────

class TestCertificateAvailableNotification(BaseTestCase):
    """Tests for NotificationService.notify_certificate_available."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    def _make_cert(self, email: str = "cert@example.com"):
        patient = _make_patient_with_email(email)
        user = User.select().first()
        cert = MedicalCertificateService.create_certificate(
            SaveMedicalCertificateDTO(
                patient_id=str(patient.id),
                issue_date=date.today().isoformat(),
                conclusion="Aptitude confirmée.",
                is_fit_for_work=True,
            ),
            user,
        )
        return patient, cert

    def test_certificate_notification_creates_log(self):
        """notify_certificate_available creates a CERTIFICATE_AVAILABLE log."""
        patient, cert = self._make_cert()

        # The notification is automatically triggered in create_certificate.
        # Count how many logs exist for this patient with that type.
        logs = (
            NotificationLog.select()
            .where(
                NotificationLog.patient == patient.id,
                NotificationLog.notification_type == NotificationType.CERTIFICATE_AVAILABLE,
            )
            .count()
        )
        self.assertGreaterEqual(logs, 1)

    def test_certificate_notification_log_body_contains_date(self):
        """The certificate notification body contains the issue date."""
        patient, cert = self._make_cert("datecheck@example.com")

        log = (
            NotificationLog.select()
            .where(
                NotificationLog.patient == patient.id,
                NotificationLog.notification_type == NotificationType.CERTIFICATE_AVAILABLE,
            )
            .first()
        )
        self.assertIsNotNone(log)
        # Issue date should appear in body (formatted as dd/mm/yyyy)
        formatted = date.today().strftime("%d/%m/%Y")
        self.assertIn(formatted, log.body)

    def test_certificate_notification_channel_is_email(self):
        """The certificate notification is sent via EMAIL channel."""
        from gws_care.notification.notification_enums import NotificationChannel
        patient, cert = self._make_cert("channel@example.com")

        log = (
            NotificationLog.select()
            .where(
                NotificationLog.patient == patient.id,
                NotificationLog.notification_type == NotificationType.CERTIFICATE_AVAILABLE,
            )
            .first()
        )
        self.assertIsNotNone(log)
        self.assertEqual(log.channel, NotificationChannel.EMAIL)
