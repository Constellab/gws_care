"""DTOs for ExamTypeModel."""

from gws_core import BaseModelDTO, ModelDTO

from gws_care.exam.exam_type import ExamType


class ExamTypeModelDTO(ModelDTO):
    """Full exam type record returned to callers."""

    code: str
    name: str
    category: ExamType
    description: str | None = None
    unit: str | None = None
    threshold_low: float | None = None
    threshold_high: float | None = None
    threshold_critical_low: float | None = None
    threshold_critical_high: float | None = None
    is_active: bool


class SaveExamTypeModelDTO(BaseModelDTO):
    """DTO for creating or updating an exam type."""

    code: str
    name: str
    category: str  # ExamType enum value
    description: str | None = None
    unit: str | None = None
    threshold_low: float | None = None
    threshold_high: float | None = None
    threshold_critical_low: float | None = None
    threshold_critical_high: float | None = None
    is_active: bool = True
