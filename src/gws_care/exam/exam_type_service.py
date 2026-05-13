"""CRUD service for ExamTypeModel."""

from gws_core import BadRequestException, NotFoundException

from gws_care.exam.exam_type import ExamType
from gws_care.exam.exam_type_dto import SaveExamTypeModelDTO
from gws_care.exam.exam_type_model import ExamTypeModel


class ExamTypeService:
    """Service for managing configurable exam types."""

    # ── Queries ───────────────────────────────────────────────────────────────

    @classmethod
    def get_exam_type(cls, exam_type_id: str) -> ExamTypeModel:
        record = ExamTypeModel.get_or_none(ExamTypeModel.id == exam_type_id)
        if record is None:
            raise NotFoundException(f"ExamType '{exam_type_id}' not found")
        return record

    @classmethod
    def get_by_code(cls, code: str) -> ExamTypeModel:
        record = ExamTypeModel.get_or_none(ExamTypeModel.code == code)
        if record is None:
            raise NotFoundException(f"ExamType with code '{code}' not found")
        return record

    @classmethod
    def list_exam_types(cls, active_only: bool = True) -> list[ExamTypeModel]:
        query = ExamTypeModel.select().order_by(ExamTypeModel.name)
        if active_only:
            query = query.where(ExamTypeModel.is_active == True)
        return list(query)

    # ── Mutations ─────────────────────────────────────────────────────────────

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
    def update_exam_type(cls, exam_type_id: str, dto: SaveExamTypeModelDTO) -> ExamTypeModel:
        record = cls.get_exam_type(exam_type_id)
        cls._validate_dto(dto)
        # Ensure code uniqueness if changed
        existing = ExamTypeModel.get_or_none(ExamTypeModel.code == dto.code)
        if existing is not None and str(existing.id) != exam_type_id:
            raise BadRequestException(f"An exam type with code '{dto.code}' already exists")
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
    def activate_exam_type(cls, exam_type_id: str) -> ExamTypeModel:
        record = cls.get_exam_type(exam_type_id)
        record.is_active = True
        record.save()
        return record

    # ── Seed ─────────────────────────────────────────────────────────────────

    @classmethod
    def seed_from_enum(cls) -> None:
        """Populate the table with one row per ExamType enum value if not present."""
        for exam_type in ExamType:
            if ExamTypeModel.get_or_none(ExamTypeModel.code == exam_type.value) is None:
                record = ExamTypeModel()
                record.code = exam_type.value
                record.name = exam_type.get_label()
                record.category = exam_type
                record.is_active = True
                record.save()

    # ── Internals ─────────────────────────────────────────────────────────────

    @classmethod
    def _validate_dto(cls, dto: SaveExamTypeModelDTO) -> None:
        if not dto.code or not dto.code.strip():
            raise BadRequestException("Exam type code is required")
        if not dto.name or not dto.name.strip():
            raise BadRequestException("Exam type name is required")
        # Validate category is a valid ExamType
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
