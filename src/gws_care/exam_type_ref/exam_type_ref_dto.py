"""DTOs for ExamTypeRef and ExamParameter."""

from pydantic import BaseModel


class ExamParameterDTO(BaseModel):
    id: str
    exam_type_ref_id: str
    name: str
    value_type: str
    unit: str | None = None
    ref_low: float | None = None
    ref_high: float | None = None
    critical_low: float | None = None
    critical_high: float | None = None
    is_required: bool = False
    display_order: int = 0


class SaveExamParameterDTO(BaseModel):
    name: str
    value_type: str = "NUMERIC"
    unit: str | None = None
    ref_low: float | None = None
    ref_high: float | None = None
    critical_low: float | None = None
    critical_high: float | None = None
    is_required: bool = False
    display_order: int = 0


class ExamTypeRefDTO(BaseModel):
    id: str
    name: str
    category: str
    category_label: str
    description: str | None = None
    is_active: bool = True
    allows_attachment: bool = True
    requires_attachment: bool = False
    parameters: list[ExamParameterDTO] = []


class ExamTypeRefRowDTO(BaseModel):
    id: str
    name: str
    category: str
    category_label: str
    is_active: bool
    allows_attachment: bool
    requires_attachment: bool
    parameter_count: int = 0


class SaveExamTypeRefDTO(BaseModel):
    name: str
    category: str = "OTHER"
    description: str | None = None
    is_active: bool = True
    allows_attachment: bool = True
    requires_attachment: bool = False
