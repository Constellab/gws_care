"""Unit tests for ExamService and ExamResultService."""

from datetime import date

from gws_care.exam.exam_dto import InterpretExamDTO, SaveExamDTO, UpdateExamSectionsDTO
from gws_care.exam.exam_result_dto import SaveExamResultDTO
from gws_care.exam.exam_result_service import ExamResultService
from gws_care.exam.exam_service import ExamService
from gws_care.exam.exam_type import ExamStatus, ExamType
from gws_care.patient.patient_dto import SavePatientDTO
from gws_care.patient.patient_service import PatientService
from gws_care.user.care_user_sync_service import CareUserSyncService
from gws_care.user.user import User
from gws_core import BadRequestException, BaseTestCase, NotFoundException

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_patient():
    return PatientService.create_patient(
        SavePatientDTO(last_name="Exam", first_name="Patient", date_of_birth=date(1985, 6, 15), gender="F")
    )


def _make_exam_dto(patient_id: str, **kwargs) -> SaveExamDTO:
    defaults = {
        "patient_id": patient_id,
        "exam_date": date.today(),
        "exam_type": ExamType.CLINICAL,
    }
    defaults.update(kwargs)
    return SaveExamDTO(**defaults)


def _get_doctor() -> User:
    """Return the first active non-sys user to act as a doctor."""
    return User.select().where(User.is_active == True).get()


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestExamService(BaseTestCase):
    """Tests for ExamService: CRUD, status transitions and result management."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    # ── create_exam ───────────────────────────────────────────────────────────

    def test_create_exam_happy_path(self):
        """Exam is created with TODO status and patient linked."""
        patient = _make_patient()
        exam = ExamService.create_exam(_make_exam_dto(str(patient.id)))

        self.assertIsNotNone(exam.id)
        self.assertEqual(exam.status, ExamStatus.TODO)
        self.assertEqual(str(exam.patient_id), str(patient.id))
        self.assertEqual(exam.exam_type, ExamType.CLINICAL)

    def test_create_exam_persists_fields(self):
        """Optional fields are persisted when provided."""
        patient = _make_patient()
        exam = ExamService.create_exam(
            _make_exam_dto(
                str(patient.id),
                weight=75.0,
                height=178.0,
                bmi=23.7,
                blood_pressure="120/80",
                reason_for_visit="Annual check",
            )
        )

        self.assertEqual(exam.weight, 75.0)
        self.assertEqual(exam.height, 178.0)
        self.assertAlmostEqual(exam.bmi, 23.7, places=1)
        self.assertEqual(exam.blood_pressure, "120/80")
        self.assertEqual(exam.reason_for_visit, "Annual check")

    def test_create_exam_unknown_patient(self):
        """Unknown patient_id raises BadRequestException."""
        with self.assertRaises(BadRequestException):
            ExamService.create_exam(
                _make_exam_dto("00000000-0000-0000-0000-000000000000")
            )

    # ── get_exam ──────────────────────────────────────────────────────────────

    def test_get_exam_not_found(self):
        """get_exam raises NotFoundException for unknown id."""
        with self.assertRaises(NotFoundException):
            ExamService.get_exam("00000000-0000-0000-0000-000000000000")

    # ── update_exam ───────────────────────────────────────────────────────────

    def test_update_exam(self):
        """update_exam changes mutable fields."""
        patient = _make_patient()
        exam = ExamService.create_exam(_make_exam_dto(str(patient.id)))
        updated = ExamService.update_exam(
            str(exam.id),
            _make_exam_dto(str(patient.id), exam_type=ExamType.BIOLOGY, weight=80.0, blood_pressure="120/80"),
        )

        self.assertEqual(updated.exam_type, ExamType.BIOLOGY)
        self.assertEqual(updated.weight, 80.0)
        self.assertEqual(updated.blood_pressure, "120/80")

    def test_update_exam_not_found(self):
        """update_exam raises NotFoundException for unknown exam id."""
        patient = _make_patient()
        with self.assertRaises(NotFoundException):
            ExamService.update_exam(
                "00000000-0000-0000-0000-000000000000",
                _make_exam_dto(str(patient.id)),
            )

    # ── update_sections ───────────────────────────────────────────────────────

    def test_update_sections(self):
        """update_sections updates medical sections and stores lab_results JSON."""
        patient = _make_patient()
        exam = ExamService.create_exam(_make_exam_dto(str(patient.id)))

        lab_rows = [
            {"id": "1", "parameter": "Hemoglobin", "unit": "g/dL", "value": "14", "reference_range": "13-17", "status": "normal"}
        ]
        dto = UpdateExamSectionsDTO(
            reason_for_visit="Headaches",
            weight=70.0,
            height=170.0,
            blood_pressure="130/85",
            lab_results=lab_rows,
        )
        updated = ExamService.update_sections(str(exam.id), dto)

        self.assertEqual(updated.reason_for_visit, "Headaches")
        self.assertEqual(updated.weight, 70.0)
        self.assertIsNotNone(updated.lab_results)
        self.assertEqual(len(updated.lab_results), 1)
        self.assertEqual(updated.lab_results[0]["parameter"], "Hemoglobin")

    def test_update_sections_clears_fields(self):
        """update_sections with None clears previously set fields."""
        patient = _make_patient()
        exam = ExamService.create_exam(
            _make_exam_dto(str(patient.id), weight=80.0, reason_for_visit="First visit")
        )
        ExamService.update_sections(str(exam.id), UpdateExamSectionsDTO(weight=None, reason_for_visit=None))
        refreshed = ExamService.get_exam(str(exam.id))

        self.assertIsNone(refreshed.reason_for_visit)
        self.assertIsNone(refreshed.weight)

    # ── set_in_progress_results ───────────────────────────────────────────────

    def test_set_pending(self):
        """set_in_progress_results transitions exam from TODO to IN_PROGRESS_RESULTS."""
        patient = _make_patient()
        exam = ExamService.create_exam(_make_exam_dto(str(patient.id)))
        self.assertEqual(exam.status, ExamStatus.TODO)

        pending = ExamService.set_in_progress_results(str(exam.id))
        self.assertEqual(pending.status, ExamStatus.IN_PROGRESS_RESULTS)

    # ── interpret_exam ────────────────────────────────────────────────────────

    def test_interpret_exam_happy_path(self):
        """interpret_exam sets DONE status, stores text and doctor FK."""
        patient = _make_patient()
        exam = ExamService.create_exam(_make_exam_dto(str(patient.id)))
        ExamService.set_in_progress_results(str(exam.id))
        doctor = _get_doctor()

        interpreted = ExamService.interpret_exam(
            str(exam.id),
            InterpretExamDTO(interpretation="Patient is healthy"),
            doctor,
        )

        self.assertEqual(interpreted.status, ExamStatus.DONE)
        self.assertEqual(interpreted.interpretation, "Patient is healthy")
        self.assertEqual(str(interpreted.interpreted_by_id), str(doctor.id))

    def test_interpret_exam_empty_text_raises(self):
        """Empty interpretation text raises BadRequestException."""
        patient = _make_patient()
        exam = ExamService.create_exam(_make_exam_dto(str(patient.id)))
        ExamService.set_in_progress_results(str(exam.id))
        doctor = _get_doctor()

        with self.assertRaises(BadRequestException):
            ExamService.interpret_exam(
                str(exam.id), InterpretExamDTO(interpretation=""), doctor
            )

    def test_interpret_exam_whitespace_text_raises(self):
        """Whitespace-only interpretation raises BadRequestException."""
        patient = _make_patient()
        exam = ExamService.create_exam(_make_exam_dto(str(patient.id)))
        ExamService.set_in_progress_results(str(exam.id))
        doctor = _get_doctor()

        with self.assertRaises(BadRequestException):
            ExamService.interpret_exam(
                str(exam.id), InterpretExamDTO(interpretation="   "), doctor
            )

    def test_interpret_exam_strips_whitespace(self):
        """Leading/trailing whitespace in interpretation is stripped."""
        patient = _make_patient()
        exam = ExamService.create_exam(_make_exam_dto(str(patient.id)))
        ExamService.set_in_progress_results(str(exam.id))
        doctor = _get_doctor()

        result = ExamService.interpret_exam(
            str(exam.id), InterpretExamDTO(interpretation="  All clear  "), doctor
        )
        self.assertEqual(result.interpretation, "All clear")

    # ── delete_exam ───────────────────────────────────────────────────────────

    def test_delete_exam(self):
        """delete_exam removes the record; subsequent get_exam raises NotFoundException."""
        patient = _make_patient()
        exam = ExamService.create_exam(_make_exam_dto(str(patient.id)))
        exam_id = str(exam.id)

        ExamService.delete_exam(exam_id)

        with self.assertRaises(NotFoundException):
            ExamService.get_exam(exam_id)

    def test_delete_exam_not_found(self):
        """delete_exam raises NotFoundException for unknown id."""
        with self.assertRaises(NotFoundException):
            ExamService.delete_exam("00000000-0000-0000-0000-000000000000")

    # ── list_exams_for_patient ────────────────────────────────────────────────

    def test_list_exams_for_patient(self):
        """Returns only that patient's exams, excluding other patients."""
        p1 = _make_patient()
        p2 = _make_patient()
        ExamService.create_exam(_make_exam_dto(str(p1.id)))
        ExamService.create_exam(_make_exam_dto(str(p2.id)))

        results = ExamService.list_exams_for_patient(str(p1.id))
        for e in results:
            self.assertEqual(str(e.patient_id), str(p1.id))

    def test_list_exams_for_patient_newest_first(self):
        """Exams are returned newest exam_date first."""
        patient = _make_patient()
        from datetime import timedelta
        old_date = date.today().replace(year=date.today().year - 1)
        new_date = date.today()
        exam_old = ExamService.create_exam(_make_exam_dto(str(patient.id), exam_date=old_date))
        exam_new = ExamService.create_exam(_make_exam_dto(str(patient.id), exam_date=new_date))

        results = ExamService.list_exams_for_patient(str(patient.id))
        self.assertEqual(str(results[0].id), str(exam_new.id))
        self.assertEqual(str(results[1].id), str(exam_old.id))

    # ── to_row_dto ────────────────────────────────────────────────────────────

    def test_to_row_dto_fields(self):
        """to_row_dto populates id, exam_date, exam_type, exam_type_label, status."""
        patient = _make_patient()
        exam = ExamService.create_exam(_make_exam_dto(str(patient.id), exam_type=ExamType.BIOLOGY))
        dto = ExamService.to_row_dto(exam)

        self.assertEqual(dto.id, str(exam.id))
        self.assertEqual(dto.exam_type, ExamType.BIOLOGY.value)
        self.assertEqual(dto.exam_type_label, ExamType.BIOLOGY.get_label())
        self.assertEqual(dto.status, ExamStatus.TODO.value)


class TestExamResultService(BaseTestCase):
    """Tests for ExamResultService: create/update/delete result + status cascade."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    def _create_exam(self):
        patient = _make_patient()
        return ExamService.create_exam(_make_exam_dto(str(patient.id)))

    # ── get_result_for_exam ───────────────────────────────────────────────────

    def test_get_result_none_when_no_result(self):
        """get_result_for_exam returns None when no result has been saved."""
        exam = self._create_exam()
        result = ExamResultService.get_result_for_exam(str(exam.id))
        self.assertIsNone(result)

    # ── save_result ───────────────────────────────────────────────────────────

    def test_save_result_creates_result(self):
        """save_result creates an ExamResult and auto-advances exam to IN_PROGRESS_INTERPRETATION."""
        exam = self._create_exam()
        self.assertEqual(exam.status, ExamStatus.TODO)

        result = ExamResultService.save_result(
            str(exam.id),
            SaveExamResultDTO(result_data={"hemoglobin": "14"}, image_paths=[]),
        )

        self.assertIsNotNone(result.id)
        self.assertEqual(result.result_data, {"hemoglobin": "14"})
        refreshed_exam = ExamService.get_exam(str(exam.id))
        self.assertEqual(refreshed_exam.status, ExamStatus.IN_PROGRESS_INTERPRETATION)

    def test_save_result_updates_existing(self):
        """Second save_result call overwrites result_data on the same record."""
        exam = self._create_exam()
        ExamResultService.save_result(
            str(exam.id),
            SaveExamResultDTO(result_data={"hemoglobin": "14"}, image_paths=[]),
        )
        ExamResultService.save_result(
            str(exam.id),
            SaveExamResultDTO(result_data={"hemoglobin": "15", "glucose": "5.5"}, image_paths=[]),
        )

        result = ExamResultService.get_result_for_exam(str(exam.id))
        self.assertEqual(result.result_data["hemoglobin"], "15")
        self.assertIn("glucose", result.result_data)

    def test_save_result_does_not_regress_status(self):
        """If exam is already IN_PROGRESS_INTERPRETATION, status stays after a second save."""
        exam = self._create_exam()
        ExamResultService.save_result(
            str(exam.id), SaveExamResultDTO(result_data={}, image_paths=[])
        )
        # Exam is now IN_PROGRESS_INTERPRETATION — save again
        ExamResultService.save_result(
            str(exam.id), SaveExamResultDTO(result_data={"note": "updated"}, image_paths=[])
        )
        refreshed = ExamService.get_exam(str(exam.id))
        self.assertEqual(refreshed.status, ExamStatus.IN_PROGRESS_INTERPRETATION)

    def test_save_result_stores_image_paths(self):
        """image_paths list is persisted in the ExamResult."""
        exam = self._create_exam()
        paths = ["path/to/image1.png", "path/to/image2.png"]
        result = ExamResultService.save_result(
            str(exam.id),
            SaveExamResultDTO(result_data={}, image_paths=paths),
        )
        self.assertEqual(result.image_paths, paths)

    # ── delete_result ─────────────────────────────────────────────────────────

    def test_delete_result_resets_status_to_draft(self):
        """delete_result removes ExamResult and resets exam to TODO."""
        exam = self._create_exam()
        ExamResultService.save_result(
            str(exam.id), SaveExamResultDTO(result_data={"x": "1"}, image_paths=[])
        )
        # Interpret first so we can verify interpretation is also cleared
        doctor = _get_doctor()
        ExamService.interpret_exam(str(exam.id), InterpretExamDTO(interpretation="Fine"), doctor)

        ExamResultService.delete_result(str(exam.id))

        refreshed = ExamService.get_exam(str(exam.id))
        self.assertEqual(refreshed.status, ExamStatus.TODO)
        self.assertIsNone(refreshed.interpretation)
        self.assertIsNone(refreshed.interpreted_by_id)

    def test_delete_result_no_op_when_no_result(self):
        """delete_result is safe to call when no result exists."""
        exam = self._create_exam()
        # Should not raise
        ExamResultService.delete_result(str(exam.id))
        self.assertEqual(ExamService.get_exam(str(exam.id)).status, ExamStatus.TODO)
