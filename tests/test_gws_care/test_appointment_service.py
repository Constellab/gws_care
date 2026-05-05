"""Unit tests for AppointmentService."""

from datetime import datetime, timedelta

from gws_care.account.account_dto import SaveAccountDTO
from gws_care.account.account_service import AccountService
from gws_care.appointment.appointment_dto import SaveAppointmentDTO
from gws_care.appointment.appointment_service import AppointmentService
from gws_care.appointment.appointment_status import AppointmentStatus
from gws_care.exam.exam_type import ExamType
from gws_care.patient.patient_dto import SavePatientDTO
from gws_care.patient.patient_service import PatientService
from gws_care.user.care_user_sync_service import CareUserSyncService
from gws_core import BadRequestException, BaseTestCase, NotFoundException

# ── Helpers ───────────────────────────────────────────────────────────────────

_tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")


def _make_patient():
    from datetime import date
    return PatientService.create_patient(
        SavePatientDTO(last_name="Test", first_name="Patient", date_of_birth=date(1990, 1, 1), gender="M")
    )


def _make_account():
    return AccountService.create_account(SaveAccountDTO(name="TestApptAcct"))


def _make_appt_dto(patient_id: str, **kwargs) -> SaveAppointmentDTO:
    defaults = {
        "patient_id": patient_id,
        "scheduled_at": _tomorrow,
        "exam_type": ExamType.CLINICAL.value,
    }
    defaults.update(kwargs)
    return SaveAppointmentDTO(**defaults)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestAppointmentService(BaseTestCase):
    """Tests for AppointmentService: creation, editing, status transitions and filters."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    # ── create_appointment ────────────────────────────────────────────────────

    def test_create_appointment_happy_path(self):
        """Appointment is created with SCHEDULED status and correct fields."""
        patient = _make_patient()
        appt = AppointmentService.create_appointment(_make_appt_dto(str(patient.id)))

        self.assertIsNotNone(appt.id)
        self.assertEqual(appt.status, AppointmentStatus.SCHEDULED)
        self.assertEqual(str(appt.patient_id), str(patient.id))
        self.assertEqual(appt.exam_type, ExamType.CLINICAL)

    def test_create_appointment_with_notes(self):
        """Notes are persisted."""
        patient = _make_patient()
        appt = AppointmentService.create_appointment(
            _make_appt_dto(str(patient.id), notes="Routine check")
        )
        self.assertEqual(appt.notes, "Routine check")

    def test_create_appointment_with_account(self):
        """billing_account is persisted when provided."""
        patient = _make_patient()
        account = _make_account()
        appt = AppointmentService.create_appointment(
            _make_appt_dto(str(patient.id), account_id=str(account.id))
        )
        self.assertEqual(str(appt.billing_account_id), str(account.id))

    def test_create_appointment_unknown_patient(self):
        """Unknown patient_id raises BadRequestException."""
        with self.assertRaises(BadRequestException):
            AppointmentService.create_appointment(
                _make_appt_dto("00000000-0000-0000-0000-000000000000")
            )

    def test_create_appointment_invalid_exam_type(self):
        """Invalid exam_type raises BadRequestException."""
        patient = _make_patient()
        with self.assertRaises(BadRequestException):
            AppointmentService.create_appointment(
                _make_appt_dto(str(patient.id), exam_type="not_valid")
            )

    def test_create_appointment_bad_datetime(self):
        """Malformed scheduled_at raises BadRequestException."""
        patient = _make_patient()
        with self.assertRaises(BadRequestException):
            AppointmentService.create_appointment(
                _make_appt_dto(str(patient.id), scheduled_at="not-a-date")
            )

    # ── get_appointment ───────────────────────────────────────────────────────

    def test_get_appointment_not_found(self):
        """NotFoundException raised for unknown appointment id."""
        with self.assertRaises(NotFoundException):
            AppointmentService.get_appointment("00000000-0000-0000-0000-000000000000")

    # ── update_appointment ────────────────────────────────────────────────────

    def test_update_appointment_when_scheduled(self):
        """Appointment can be updated while in SCHEDULED status."""
        patient = _make_patient()
        appt = AppointmentService.create_appointment(_make_appt_dto(str(patient.id)))
        new_time = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M")

        updated = AppointmentService.update_appointment(
            str(appt.id),
            _make_appt_dto(str(patient.id), scheduled_at=new_time, exam_type=ExamType.BIOLOGY.value, notes="Updated"),
        )

        self.assertEqual(updated.exam_type, ExamType.BIOLOGY)
        self.assertEqual(updated.notes, "Updated")

    def test_update_appointment_when_done_raises(self):
        """Updating a DONE appointment raises BadRequestException."""
        patient = _make_patient()
        appt = AppointmentService.create_appointment(_make_appt_dto(str(patient.id)))
        AppointmentService.set_status(str(appt.id), AppointmentStatus.DONE)

        with self.assertRaises(BadRequestException):
            AppointmentService.update_appointment(
                str(appt.id), _make_appt_dto(str(patient.id))
            )

    def test_update_appointment_when_cancelled_raises(self):
        """Updating a CANCELLED appointment raises BadRequestException."""
        patient = _make_patient()
        appt = AppointmentService.create_appointment(_make_appt_dto(str(patient.id)))
        AppointmentService.set_status(str(appt.id), AppointmentStatus.CANCELLED)

        with self.assertRaises(BadRequestException):
            AppointmentService.update_appointment(
                str(appt.id), _make_appt_dto(str(patient.id))
            )

    # ── set_status / lifecycle transitions ────────────────────────────────────

    def test_set_status_to_in_progress(self):
        """SCHEDULED → IN_PROGRESS transition persisted correctly."""
        patient = _make_patient()
        appt = AppointmentService.create_appointment(_make_appt_dto(str(patient.id)))
        updated = AppointmentService.set_status(str(appt.id), AppointmentStatus.IN_PROGRESS)
        self.assertEqual(updated.status, AppointmentStatus.IN_PROGRESS)

    def test_set_status_to_done(self):
        """Appointment can be moved to DONE."""
        patient = _make_patient()
        appt = AppointmentService.create_appointment(_make_appt_dto(str(patient.id)))
        AppointmentService.set_status(str(appt.id), AppointmentStatus.IN_PROGRESS)
        done = AppointmentService.set_status(str(appt.id), AppointmentStatus.DONE)
        self.assertEqual(done.status, AppointmentStatus.DONE)

    def test_set_status_to_cancelled(self):
        """Appointment can be CANCELLED from SCHEDULED."""
        patient = _make_patient()
        appt = AppointmentService.create_appointment(_make_appt_dto(str(patient.id)))
        cancelled = AppointmentService.set_status(str(appt.id), AppointmentStatus.CANCELLED)
        self.assertEqual(cancelled.status, AppointmentStatus.CANCELLED)

    def test_cancel_appointment_helper(self):
        """cancel_appointment convenience method works."""
        patient = _make_patient()
        appt = AppointmentService.create_appointment(_make_appt_dto(str(patient.id)))
        cancelled = AppointmentService.cancel_appointment(str(appt.id))
        self.assertEqual(cancelled.status, AppointmentStatus.CANCELLED)

    def test_complete_appointment_helper(self):
        """complete_appointment convenience method works."""
        patient = _make_patient()
        appt = AppointmentService.create_appointment(_make_appt_dto(str(patient.id)))
        done = AppointmentService.complete_appointment(str(appt.id))
        self.assertEqual(done.status, AppointmentStatus.DONE)

    # ── list_all ──────────────────────────────────────────────────────────────

    def test_list_all_no_filters(self):
        """list_all() with no filters returns all appointments."""
        patient = _make_patient()
        AppointmentService.create_appointment(_make_appt_dto(str(patient.id)))
        AppointmentService.create_appointment(_make_appt_dto(str(patient.id)))
        results = AppointmentService.list_all()
        self.assertGreaterEqual(len(results), 2)

    def test_list_all_filter_by_status(self):
        """list_all(status=CANCELLED) returns only CANCELLED appointments."""
        patient = _make_patient()
        appt = AppointmentService.create_appointment(_make_appt_dto(str(patient.id)))
        AppointmentService.set_status(str(appt.id), AppointmentStatus.CANCELLED)
        # Create another that stays SCHEDULED
        AppointmentService.create_appointment(_make_appt_dto(str(patient.id)))

        results = AppointmentService.list_all(status=AppointmentStatus.CANCELLED)
        for a in results:
            self.assertEqual(a.status, AppointmentStatus.CANCELLED)
        ids = [str(a.id) for a in results]
        self.assertIn(str(appt.id), ids)

    def test_list_all_filter_by_search_last_name(self):
        """list_all(search=...) matches patient last_name."""
        from datetime import date
        patient = PatientService.create_patient(
            SavePatientDTO(last_name="Uniqname", first_name="Search", date_of_birth=date(1985, 1, 1), gender="M")
        )
        AppointmentService.create_appointment(_make_appt_dto(str(patient.id)))

        results = AppointmentService.list_all(search="Uniqname")
        patient_ids = [str(a.patient_id) for a in results]
        self.assertIn(str(patient.id), patient_ids)

    def test_list_all_filter_by_account_id(self):
        """list_all(account_id=...) returns only that account's appointments."""
        patient = _make_patient()
        account = _make_account()
        appt_with_acc = AppointmentService.create_appointment(
            _make_appt_dto(str(patient.id), account_id=str(account.id))
        )
        AppointmentService.create_appointment(_make_appt_dto(str(patient.id)))  # no account

        results = AppointmentService.list_all(account_id=str(account.id))
        ids = [str(a.id) for a in results]
        self.assertIn(str(appt_with_acc.id), ids)
        for a in results:
            self.assertEqual(str(a.billing_account_id), str(account.id))

    def test_list_all_ordered_by_scheduled_at_asc(self):
        """list_all returns appointments ordered soonest first."""
        from datetime import date as d
        patient = _make_patient()
        later = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%dT%H:%M")
        sooner = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
        appt_later = AppointmentService.create_appointment(_make_appt_dto(str(patient.id), scheduled_at=later))
        appt_sooner = AppointmentService.create_appointment(_make_appt_dto(str(patient.id), scheduled_at=sooner))

        results = AppointmentService.list_all()
        # Find relative position of our two appointments
        ids = [str(a.id) for a in results]
        idx_sooner = ids.index(str(appt_sooner.id))
        idx_later = ids.index(str(appt_later.id))
        self.assertLess(idx_sooner, idx_later)

    # ── list_for_patient ──────────────────────────────────────────────────────

    def test_list_for_patient(self):
        """list_for_patient returns only that patient's appointments."""
        p1 = _make_patient()
        p2 = _make_patient()
        AppointmentService.create_appointment(_make_appt_dto(str(p1.id)))
        AppointmentService.create_appointment(_make_appt_dto(str(p2.id)))

        results = AppointmentService.list_for_patient(str(p1.id))
        for a in results:
            self.assertEqual(str(a.patient_id), str(p1.id))

    def test_list_for_patient_newest_first(self):
        """list_for_patient returns appointments newest first."""
        patient = _make_patient()
        sooner = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
        later = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%dT%H:%M")
        appt_sooner = AppointmentService.create_appointment(_make_appt_dto(str(patient.id), scheduled_at=sooner))
        appt_later = AppointmentService.create_appointment(_make_appt_dto(str(patient.id), scheduled_at=later))

        results = AppointmentService.list_for_patient(str(patient.id))
        # Newest (later) should be first
        self.assertEqual(str(results[0].id), str(appt_later.id))
        self.assertEqual(str(results[1].id), str(appt_sooner.id))

    # ── to_row_dto ────────────────────────────────────────────────────────────

    def test_to_row_dto_fields(self):
        """to_row_dto populates all expected fields."""
        patient = _make_patient()
        account = _make_account()
        appt = AppointmentService.create_appointment(
            _make_appt_dto(str(patient.id), account_id=str(account.id))
        )
        dto = AppointmentService.to_row_dto(appt)

        self.assertEqual(dto.id, str(appt.id))
        self.assertEqual(dto.patient_id, str(patient.id))
        self.assertIn("TEST", dto.patient_name)   # last_name is uppercased
        self.assertEqual(dto.account_name, "TestApptAcct")
        self.assertEqual(dto.exam_type_label, ExamType.CLINICAL.get_label())
        self.assertEqual(dto.status, AppointmentStatus.SCHEDULED.value)

    def test_to_row_dto_no_account(self):
        """to_row_dto with no billing account sets account_name to None."""
        patient = _make_patient()
        appt = AppointmentService.create_appointment(_make_appt_dto(str(patient.id)))
        dto = AppointmentService.to_row_dto(appt)
        self.assertIsNone(dto.account_name)
