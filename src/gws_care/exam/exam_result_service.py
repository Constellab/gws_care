"""Service for managing exam results."""

from gws_core import BadRequestException, NotFoundException

from gws_care.exam.appreciation import Appreciation
from gws_care.exam.exam import Exam
from gws_care.exam.exam_result import ExamResult
from gws_care.exam.exam_result_dto import OverrideAppreciationDTO, SaveExamResultDTO
from gws_care.exam.exam_service import ExamService
from gws_care.exam.exam_type import ExamStatus
from gws_care.exam.threshold_service import ThresholdService
from gws_care.role.care_action import CareAction
from gws_care.role.permission_service import PermissionService
from gws_care.user.user import User


class ExamResultService:
    """Service to create / update exam results and advance exam status."""

    @classmethod
    def get_result_for_exam(cls, exam_id: str) -> ExamResult | None:
        """Return the ExamResult for an exam, or None if not yet entered."""
        return ExamResult.get_or_none(ExamResult.exam == exam_id)

    @classmethod
    def save_result(cls, exam_id: str, dto: SaveExamResultDTO) -> ExamResult:
        """Create or update the result for an exam.

        Automatically advances exam status from DRAFT → PENDING.

        Phase 3 — If `dto.primary_value` is supplied:
        - Load the ExamTypeModel (via `dto.exam_type_model_id` if given, else by category match)
        - Auto-calculate appreciation using ThresholdService
        - Store both `appreciation` and `calculated_appreciation`
        - `appreciation_override` is reset to False (new result data supersedes any prior override)
        """
        exam = ExamService.get_exam(exam_id)

        result = cls.get_result_for_exam(exam_id)
        if result is None:
            result = ExamResult()
            result.exam = exam

        result.result_data = dto.result_data
        result.image_paths = dto.image_paths

        # Auto-calculate appreciation when a primary numeric value is provided
        if dto.primary_value is not None:
            exam_type_model = cls._resolve_exam_type_model(exam, dto.exam_type_model_id)
            if exam_type_model and ThresholdService.has_thresholds(exam_type_model):
                calc = ThresholdService.calculate_appreciation(exam_type_model, dto.primary_value)
                result.appreciation = calc
                result.calculated_appreciation = calc
            else:
                result.appreciation = None
                result.calculated_appreciation = None
            result.appreciation_override = False

        result.save()

        # Advance to IN_PROGRESS_INTERPRETATION when results are saved via campaign/visit flow
        if exam.status in (ExamStatus.TODO, ExamStatus.IN_PROGRESS_RESULTS):
            ExamService.set_in_progress_interpretation(exam_id)

        return result

    @classmethod
    def override_appreciation(
        cls,
        exam_id: str,
        dto: OverrideAppreciationDTO,
        user: "User | None" = None,
    ) -> ExamResult:
        """Phase 3.2 — Clinic Doctor manually overrides the appreciation.

        - Sets `appreciation` to the new value
        - Sets `appreciation_override = True`
        - Preserves `calculated_appreciation` (original auto-calculated value)

        Raises if no result exists yet for the exam, or if the visit is already
        past DOCTOR_CLINIC_VALIDATED (locked).
        """
        if user is not None:
            PermissionService.require(user, CareAction.EXAM_APPRECIATION_OVERRIDE)
        exam = ExamService.get_exam(exam_id)

        result = cls.get_result_for_exam(exam_id)
        if result is None:
            raise NotFoundException(f"No result found for exam '{exam_id}'. Save a result first.")

        result.appreciation = dto.appreciation
        result.appreciation_override = True
        # calculated_appreciation is intentionally NOT changed — it preserves the auto value
        result.save()
        return result

    @classmethod
    def delete_result(cls, exam_id: str) -> None:
        """Delete the result for an exam and reset status to DRAFT."""
        result = cls.get_result_for_exam(exam_id)
        if result:
            result.delete_instance()
            exam = ExamService.get_exam(exam_id)
            exam.status = ExamStatus.TODO
            exam.interpretation = None
            exam.interpreted_by = None
            exam.save()

    # ── Internal helpers ──────────────────────────────────────────────────────

    @classmethod
    def _resolve_exam_type_model(cls, exam: Exam, exam_type_model_id: str | None):
        """Return the appropriate ExamTypeModel for threshold calculation.

        If `exam_type_model_id` is provided, load that model directly.
        Otherwise fall back to the best-match by exam category.
        Returns None if nothing found.
        """
        if exam_type_model_id:
            from gws_care.exam.exam_type_model import ExamTypeModel
            return ExamTypeModel.get_or_none(ExamTypeModel.id == exam_type_model_id)
        return ThresholdService.find_exam_type_model_for_exam(exam)
