"""Service for managing exam results."""

from gws_care.exam.exam import Exam
from gws_care.exam.exam_result import ExamResult
from gws_care.exam.exam_result_dto import SaveExamResultDTO
from gws_care.exam.exam_service import ExamService
from gws_care.exam.exam_type import ExamStatus


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
        """
        exam = ExamService.get_exam(exam_id)
        result = cls.get_result_for_exam(exam_id)

        if result is None:
            result = ExamResult()
            result.exam = exam

        result.result_data = dto.result_data
        result.image_paths = dto.image_paths
        result.save()

        # Advance status to PENDING if still DRAFT
        if exam.status == ExamStatus.DRAFT:
            ExamService.set_pending(exam_id)

        return result

    @classmethod
    def delete_result(cls, exam_id: str) -> None:
        """Delete the result for an exam and reset status to DRAFT."""
        result = cls.get_result_for_exam(exam_id)
        if result:
            result.delete_instance()
            exam = ExamService.get_exam(exam_id)
            exam.status = ExamStatus.DRAFT
            exam.interpretation = None
            exam.interpreted_by = None
            exam.save()
