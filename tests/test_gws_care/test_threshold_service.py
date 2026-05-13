"""Unit tests for ThresholdService and appreciation auto-calculation in ExamResultService."""

from datetime import date

from gws_care.exam.appreciation import Appreciation
from gws_care.exam.exam_dto import SaveExamDTO
from gws_care.exam.exam_result_dto import OverrideAppreciationDTO, SaveExamResultDTO
from gws_care.exam.exam_result_service import ExamResultService
from gws_care.exam.exam_service import ExamService
from gws_care.exam.exam_type import ExamType
from gws_care.exam.exam_type_dto import SaveExamTypeModelDTO
from gws_care.exam.exam_type_service import ExamTypeService
from gws_care.exam.threshold_service import ThresholdService
from gws_care.patient.patient_dto import SavePatientDTO
from gws_care.patient.patient_service import PatientService
from gws_care.user.care_user_sync_service import CareUserSyncService
from gws_core import BaseTestCase, NotFoundException

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_patient():
    return PatientService.create_patient(
        SavePatientDTO(last_name="Threshold", first_name="Test", date_of_birth=date(1985, 1, 1), gender="M")
    )


def _make_exam_type_with_thresholds(code: str = "GLU") -> "ExamTypeModel":
    """Biology exam type with full threshold set (e.g. blood glucose mmol/L)."""
    return ExamTypeService.create_exam_type(
        SaveExamTypeModelDTO(
            code=code,
            name=f"Glucose ({code})",
            category=ExamType.BIOLOGY.value,
            unit="mmol/L",
            threshold_critical_low=2.5,
            threshold_low=3.9,
            threshold_high=10.0,
            threshold_critical_high=20.0,
        )
    )


def _make_exam_type_no_thresholds(code: str = "RAD") -> "ExamTypeModel":
    """Imaging exam type with no thresholds defined."""
    return ExamTypeService.create_exam_type(
        SaveExamTypeModelDTO(
            code=code,
            name=f"Radiology ({code})",
            category=ExamType.RADIOLOGY.value,
        )
    )


def _make_exam(patient, exam_type: ExamType = ExamType.BIOLOGY) -> "Exam":
    return ExamService.create_exam(
        SaveExamDTO(patient_id=str(patient.id), exam_date=date.today(), exam_type=exam_type)
    )


# ── ThresholdService unit tests ───────────────────────────────────────────────

class TestThresholdServiceCalculation(BaseTestCase):
    """Pure unit tests for ThresholdService.calculate_appreciation."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    def _make_model_obj(self, tcl=None, tl=None, th=None, tch=None):
        """Create a minimal ExamTypeModel-like object with threshold attributes."""
        class _FakeModel:
            threshold_critical_low = tcl
            threshold_low = tl
            threshold_high = th
            threshold_critical_high = tch
        return _FakeModel()

    def test_normal_in_middle_of_range(self):
        m = self._make_model_obj(tcl=2.5, tl=3.9, th=10.0, tch=20.0)
        self.assertEqual(ThresholdService.calculate_appreciation(m, 5.0), Appreciation.NORMAL)

    def test_low_below_low_threshold(self):
        m = self._make_model_obj(tcl=2.5, tl=3.9, th=10.0, tch=20.0)
        self.assertEqual(ThresholdService.calculate_appreciation(m, 3.0), Appreciation.LOW)

    def test_critical_low_below_critical_threshold(self):
        m = self._make_model_obj(tcl=2.5, tl=3.9, th=10.0, tch=20.0)
        self.assertEqual(ThresholdService.calculate_appreciation(m, 1.0), Appreciation.CRITICAL_LOW)

    def test_high_above_high_threshold(self):
        m = self._make_model_obj(tcl=2.5, tl=3.9, th=10.0, tch=20.0)
        self.assertEqual(ThresholdService.calculate_appreciation(m, 12.0), Appreciation.HIGH)

    def test_critical_high_above_critical_threshold(self):
        m = self._make_model_obj(tcl=2.5, tl=3.9, th=10.0, tch=20.0)
        self.assertEqual(ThresholdService.calculate_appreciation(m, 25.0), Appreciation.CRITICAL_HIGH)

    def test_boundary_exactly_at_low_threshold(self):
        """Value exactly at threshold_low is NORMAL (< not <=)."""
        m = self._make_model_obj(tl=3.9, th=10.0)
        self.assertEqual(ThresholdService.calculate_appreciation(m, 3.9), Appreciation.NORMAL)

    def test_boundary_exactly_at_high_threshold(self):
        """Value exactly at threshold_high is NORMAL (> not >=)."""
        m = self._make_model_obj(tl=3.9, th=10.0)
        self.assertEqual(ThresholdService.calculate_appreciation(m, 10.0), Appreciation.NORMAL)

    def test_only_high_threshold_defined(self):
        """Works correctly with only some thresholds set."""
        m = self._make_model_obj(th=10.0)
        self.assertEqual(ThresholdService.calculate_appreciation(m, 5.0), Appreciation.NORMAL)
        self.assertEqual(ThresholdService.calculate_appreciation(m, 15.0), Appreciation.HIGH)

    def test_has_thresholds_true(self):
        m = self._make_model_obj(th=10.0)
        self.assertTrue(ThresholdService.has_thresholds(m))

    def test_has_thresholds_false(self):
        m = self._make_model_obj()
        self.assertFalse(ThresholdService.has_thresholds(m))


# ── Auto-calculation in ExamResultService ─────────────────────────────────────

class TestExamResultServiceAppreciation(BaseTestCase):
    """Tests for appreciation auto-calculation when saving exam results."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    def test_auto_appreciation_normal(self):
        """Saving result with normal primary_value → NORMAL appreciation."""
        patient = _make_patient()
        exam_type_model = _make_exam_type_with_thresholds("AU_NRM")
        exam = _make_exam(patient, ExamType.BIOLOGY)

        result = ExamResultService.save_result(
            str(exam.id),
            SaveExamResultDTO(
                result_data={"glucose": "5.0"},
                primary_value=5.0,
                exam_type_model_id=str(exam_type_model.id),
            ),
        )

        self.assertEqual(result.appreciation, Appreciation.NORMAL)
        self.assertEqual(result.calculated_appreciation, Appreciation.NORMAL)
        self.assertFalse(result.appreciation_override)

    def test_auto_appreciation_high(self):
        """Saving result with high primary_value → HIGH appreciation."""
        patient = _make_patient()
        exam_type_model = _make_exam_type_with_thresholds("AU_HI")
        exam = _make_exam(patient, ExamType.BIOLOGY)

        result = ExamResultService.save_result(
            str(exam.id),
            SaveExamResultDTO(
                result_data={"glucose": "12.0"},
                primary_value=12.0,
                exam_type_model_id=str(exam_type_model.id),
            ),
        )

        self.assertEqual(result.appreciation, Appreciation.HIGH)
        self.assertEqual(result.calculated_appreciation, Appreciation.HIGH)

    def test_auto_appreciation_critical_low(self):
        patient = _make_patient()
        exam_type_model = _make_exam_type_with_thresholds("AU_CL")
        exam = _make_exam(patient, ExamType.BIOLOGY)

        result = ExamResultService.save_result(
            str(exam.id),
            SaveExamResultDTO(
                result_data={"glucose": "1.0"},
                primary_value=1.0,
                exam_type_model_id=str(exam_type_model.id),
            ),
        )

        self.assertEqual(result.appreciation, Appreciation.CRITICAL_LOW)

    def test_no_primary_value_no_appreciation(self):
        """Saving without primary_value leaves appreciation unchanged (None on new result)."""
        patient = _make_patient()
        exam = _make_exam(patient)

        result = ExamResultService.save_result(
            str(exam.id),
            SaveExamResultDTO(result_data={"notes": "text only"}),
        )

        self.assertIsNone(result.appreciation)
        self.assertIsNone(result.calculated_appreciation)
        self.assertFalse(result.appreciation_override)

    def test_no_thresholds_no_appreciation(self):
        """When ExamTypeModel has no thresholds, appreciation stays None even with a value."""
        patient = _make_patient()
        exam_type_model = _make_exam_type_no_thresholds("AU_NT")
        exam = _make_exam(patient, ExamType.RADIOLOGY)

        result = ExamResultService.save_result(
            str(exam.id),
            SaveExamResultDTO(
                result_data={"findings": "normal"},
                primary_value=99.0,
                exam_type_model_id=str(exam_type_model.id),
            ),
        )

        self.assertIsNone(result.appreciation)

    def test_auto_appreciation_by_category_match(self):
        """Without exam_type_model_id, service finds model by category."""
        patient = _make_patient()
        from gws_care.exam.exam_type_dto import SaveExamTypeModelDTO
        from gws_care.exam.exam_type_service import ExamTypeService
        etm = ExamTypeService.create_exam_type(
            SaveExamTypeModelDTO(
                code="CAT_CLN",
                name="Category Clinical",
                category=ExamType.CLINICAL.value,
                threshold_low=60.0,
                threshold_high=100.0,
            )
        )
        exam = _make_exam(patient, ExamType.CLINICAL)

        result = ExamResultService.save_result(
            str(exam.id),
            SaveExamResultDTO(
                result_data={"heart_rate": "120"},
                primary_value=120.0,
                # No exam_type_model_id — should be found by category
            ),
        )

        self.assertEqual(result.appreciation, Appreciation.HIGH)


# ── Phase 3.2 — Doctor appreciation override ─────────────────────────────────

class TestAppreciationOverride(BaseTestCase):
    """Tests for Médecin Clinic manual appreciation override."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    def _make_result_with_appreciation(self, appreciation: Appreciation):
        """Returns (exam, result) with a given auto-calculated appreciation."""
        import uuid
        patient = _make_patient()
        unique_suffix = uuid.uuid4().hex[:6].upper()
        exam_type_model = _make_exam_type_with_thresholds("OVR_" + unique_suffix)
        exam = _make_exam(patient, ExamType.BIOLOGY)
        # Map appreciation → a suitable primary value
        value_map = {
            Appreciation.CRITICAL_LOW: 1.0,
            Appreciation.LOW: 3.0,
            Appreciation.NORMAL: 5.0,
            Appreciation.HIGH: 12.0,
            Appreciation.CRITICAL_HIGH: 25.0,
        }
        result = ExamResultService.save_result(
            str(exam.id),
            SaveExamResultDTO(
                result_data={"glucose": str(value_map[appreciation])},
                primary_value=value_map[appreciation],
                exam_type_model_id=str(exam_type_model.id),
            ),
        )
        return exam, result

    def test_override_changes_appreciation(self):
        """Doctor can override the appreciation to NORMAL even when auto says HIGH."""
        exam, result = self._make_result_with_appreciation(Appreciation.HIGH)

        updated = ExamResultService.override_appreciation(
            str(exam.id),
            OverrideAppreciationDTO(appreciation=Appreciation.NORMAL),
        )

        self.assertEqual(updated.appreciation, Appreciation.NORMAL)
        self.assertTrue(updated.appreciation_override)

    def test_override_preserves_calculated_appreciation(self):
        """After override, calculated_appreciation still holds the original auto value."""
        exam, result = self._make_result_with_appreciation(Appreciation.HIGH)
        original_calc = result.calculated_appreciation

        ExamResultService.override_appreciation(
            str(exam.id),
            OverrideAppreciationDTO(appreciation=Appreciation.NORMAL),
        )

        # Re-fetch from DB
        from gws_care.exam.exam_result import ExamResult
        refreshed = ExamResult.get_by_id(result.id)
        self.assertEqual(refreshed.calculated_appreciation, original_calc)
        self.assertEqual(refreshed.calculated_appreciation, Appreciation.HIGH)

    def test_override_no_result_raises(self):
        """Overriding appreciation when no result exists raises NotFoundException."""
        patient = _make_patient()
        exam = _make_exam(patient)

        with self.assertRaises(NotFoundException):
            ExamResultService.override_appreciation(
                str(exam.id),
                OverrideAppreciationDTO(appreciation=Appreciation.NORMAL),
            )

    def test_re_saving_result_resets_override(self):
        """Saving new result data (with primary_value) resets override flag and recalculates."""
        exam, result = self._make_result_with_appreciation(Appreciation.HIGH)
        exam_type_model_id = str(
            ExamResultService._resolve_exam_type_model(exam, None).id
        )

        # Override to NORMAL
        ExamResultService.override_appreciation(
            str(exam.id), OverrideAppreciationDTO(appreciation=Appreciation.NORMAL)
        )

        # Save new result with a CRITICAL HIGH value — should reset override
        updated = ExamResultService.save_result(
            str(exam.id),
            SaveExamResultDTO(
                result_data={"glucose": "25.0"},
                primary_value=25.0,
                exam_type_model_id=exam_type_model_id,
            ),
        )

        self.assertEqual(updated.appreciation, Appreciation.CRITICAL_HIGH)
        self.assertFalse(updated.appreciation_override)
