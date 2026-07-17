"""Service for the legacy ExamTypeModel table.

New exam types are created exclusively via ExamTypeRef (the "Référentiel
examens" tab) — ExamTypeModel's user-facing CRUD/seed surface was removed.
`get_exam_type`/`get_exam_type_model_for_exam` remain so historical exams
created under the old system (and their PDFs) can still resolve their exam
type; `create_exam_type`/`deactivate_exam_type` remain only as fixture
factories used by test_campaign_service.py / test_threshold_service.py.
"""

from gws_core import BadRequestException, NotFoundException

from gws_care.exam.exam_type import ExamType
from gws_care.exam.exam_type_dto import SaveExamTypeModelDTO
from gws_care.exam.exam_type_model import ExamTypeModel


class ExamTypeService:
    @classmethod
    def get_exam_type(cls, exam_type_id: str) -> ExamTypeModel:
        record = ExamTypeModel.get_or_none(ExamTypeModel.id == exam_type_id)
        if record is None:
            raise NotFoundException(f"ExamType '{exam_type_id}' not found")
        return record

    @classmethod
    def get_exam_type_model_for_exam(cls, exam) -> "ExamTypeModel | None":
        """Return the ExamTypeModel whose category matches the exam's exam_type enum value."""
        if exam is None or not exam.exam_type:
            return None
        return ExamTypeModel.get_or_none(ExamTypeModel.category == exam.exam_type)

    @classmethod
    def create_exam_type(cls, dto: SaveExamTypeModelDTO) -> ExamTypeModel:
        cls._validate_dto(dto)
        if ExamTypeModel.get_or_none(ExamTypeModel.code == dto.code) is not None:
            raise BadRequestException(f"An exam type with code '{dto.code}' already exists")
        record = ExamTypeModel()
        cls._apply_dto(record, dto)
        record.save()
        return record

    @classmethod
    def deactivate_exam_type(cls, exam_type_id: str) -> ExamTypeModel:
        record = cls.get_exam_type(exam_type_id)
        record.is_active = False
        record.save()
        return record

    @classmethod
    def _validate_dto(cls, dto: SaveExamTypeModelDTO) -> None:
        if not dto.code or not dto.code.strip():
            raise BadRequestException("Exam type code is required")
        if not dto.name or not dto.name.strip():
            raise BadRequestException("Exam type name is required")
        try:
            ExamType(dto.category)
        except ValueError:
            raise BadRequestException(f"Invalid exam category: '{dto.category}'")

    @classmethod
    def _apply_dto(cls, record: ExamTypeModel, dto: SaveExamTypeModelDTO) -> None:
        record.code = dto.code.strip()
        record.name = dto.name.strip()
        record.category = ExamType(dto.category)
        record.description = dto.description
        record.unit = dto.unit
        record.threshold_low = dto.threshold_low
        record.threshold_high = dto.threshold_high
        record.threshold_critical_low = dto.threshold_critical_low
        record.threshold_critical_high = dto.threshold_critical_high
        record.is_active = dto.is_active
