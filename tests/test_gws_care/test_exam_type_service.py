"""Unit tests for ExamTypeService."""

from gws_care.exam.exam_type import ExamType
from gws_care.exam.exam_type_dto import SaveExamTypeModelDTO
from gws_care.exam.exam_type_model import ExamTypeModel
from gws_care.exam.exam_type_service import ExamTypeService
from gws_care.user.care_user_sync_service import CareUserSyncService
from gws_core import BadRequestException, BaseTestCase, NotFoundException


def _save_dto(**kwargs) -> SaveExamTypeModelDTO:
    defaults = {
        "code": "TST",
        "name": "Test Exam",
        "category": ExamType.CLINICAL.value,
    }
    defaults.update(kwargs)
    return SaveExamTypeModelDTO(**defaults)


class TestExamTypeService(BaseTestCase):
    """Tests for ExamTypeService: CRUD, seed, and validation."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    # ── create ───────────────────────────────────────────────────────────────

    def test_create_exam_type_happy_path(self):
        """ExamTypeModel is created with correct fields."""
        et = ExamTypeService.create_exam_type(_save_dto())
        self.assertIsNotNone(et.id)
        self.assertEqual(et.code, "TST")
        self.assertEqual(et.name, "Test Exam")
        self.assertEqual(et.category, ExamType.CLINICAL)
        self.assertTrue(et.is_active)

    def test_create_exam_type_duplicate_code_raises(self):
        """Creating two exam types with the same code raises BadRequestException."""
        ExamTypeService.create_exam_type(_save_dto(code="DUP"))
        with self.assertRaises(BadRequestException):
            ExamTypeService.create_exam_type(_save_dto(code="DUP"))

    def test_create_exam_type_missing_code_raises(self):
        with self.assertRaises(BadRequestException):
            ExamTypeService.create_exam_type(_save_dto(code=""))

    def test_create_exam_type_missing_name_raises(self):
        with self.assertRaises(BadRequestException):
            ExamTypeService.create_exam_type(_save_dto(code="NN", name=""))

    def test_create_exam_type_invalid_category_raises(self):
        with self.assertRaises(BadRequestException):
            ExamTypeService.create_exam_type(_save_dto(code="IC", category="INVALID_CATEGORY"))

    def test_create_exam_type_with_thresholds(self):
        """Thresholds are persisted."""
        et = ExamTypeService.create_exam_type(
            _save_dto(
                code="THR",
                threshold_low=3.5,
                threshold_high=10.0,
                threshold_critical_low=1.0,
                threshold_critical_high=15.0,
                unit="mmol/L",
            )
        )
        self.assertAlmostEqual(et.threshold_low, 3.5)
        self.assertAlmostEqual(et.threshold_high, 10.0)
        self.assertEqual(et.unit, "mmol/L")

    # ── read ─────────────────────────────────────────────────────────────────

    def test_get_exam_type_not_found_raises(self):
        with self.assertRaises(NotFoundException):
            ExamTypeService.get_exam_type("00000000-0000-0000-0000-000000000000")

    def test_get_by_code(self):
        ExamTypeService.create_exam_type(_save_dto(code="GBC"))
        et = ExamTypeService.get_by_code("GBC")
        self.assertEqual(et.code, "GBC")

    def test_list_exam_types_active_only(self):
        """list_exam_types(active_only=True) excludes inactive records."""
        ExamTypeService.create_exam_type(_save_dto(code="ACT"))
        inactive = ExamTypeService.create_exam_type(_save_dto(code="INA"))
        ExamTypeService.deactivate_exam_type(str(inactive.id))

        active_list = ExamTypeService.list_exam_types(active_only=True)
        codes = [e.code for e in active_list]
        self.assertIn("ACT", codes)
        self.assertNotIn("INA", codes)

    def test_list_exam_types_all(self):
        """list_exam_types(active_only=False) includes inactive records."""
        ExamTypeService.create_exam_type(_save_dto(code="ALL1"))
        inactive = ExamTypeService.create_exam_type(_save_dto(code="ALL2"))
        ExamTypeService.deactivate_exam_type(str(inactive.id))

        all_list = ExamTypeService.list_exam_types(active_only=False)
        codes = [e.code for e in all_list]
        self.assertIn("ALL1", codes)
        self.assertIn("ALL2", codes)

    # ── update ───────────────────────────────────────────────────────────────

    def test_update_exam_type(self):
        et = ExamTypeService.create_exam_type(_save_dto(code="UPD"))
        updated = ExamTypeService.update_exam_type(
            str(et.id),
            _save_dto(code="UPD", name="Updated Name", category=ExamType.BIOLOGY.value),
        )
        self.assertEqual(updated.name, "Updated Name")
        self.assertEqual(updated.category, ExamType.BIOLOGY)

    # ── activate / deactivate ─────────────────────────────────────────────────

    def test_deactivate_and_activate_exam_type(self):
        et = ExamTypeService.create_exam_type(_save_dto(code="ACT2"))
        deactivated = ExamTypeService.deactivate_exam_type(str(et.id))
        self.assertFalse(deactivated.is_active)
        reactivated = ExamTypeService.activate_exam_type(str(et.id))
        self.assertTrue(reactivated.is_active)

    # ── seed_from_enum ────────────────────────────────────────────────────────

    def test_seed_from_enum_creates_all_enum_values(self):
        """seed_from_enum populates one row per ExamType without duplicates."""
        ExamTypeService.seed_from_enum()
        codes_in_db = {e.code for e in ExamTypeService.list_exam_types(active_only=False)}
        for exam_type in ExamType:
            self.assertIn(exam_type.value, codes_in_db)

    def test_seed_from_enum_is_idempotent(self):
        """Calling seed_from_enum twice does not duplicate records."""
        ExamTypeService.seed_from_enum()
        ExamTypeService.seed_from_enum()
        enum_codes = [e.value for e in ExamType]
        seeded_count = ExamTypeModel.select().where(ExamTypeModel.code.in_(enum_codes)).count()
        self.assertEqual(seeded_count, len(list(ExamType)))
