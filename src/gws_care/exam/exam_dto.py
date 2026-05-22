"""Exam DTOs."""

from datetime import date

from gws_core import BaseModelDTO, ModelDTO

from gws_care.exam.exam_type import ExamStatus, ExamType


class LabResultRowDTO(BaseModelDTO):
    """One row in the laboratory results table."""

    id: str = ""
    parameter: str = ""
    unit: str = ""
    value: str = ""
    reference_range: str = ""
    status: str = "normal"  # normal | high | low | critical


class ExamDTO(ModelDTO):
    """Full exam DTO."""

    patient_id: str
    account_id: str | None
    exam_date: date
    exam_type: ExamType
    status: ExamStatus
    reason_for_visit: str | None = None
    medical_history: str | None = None
    weight: float | None = None
    height: float | None = None
    bmi: float | None = None
    blood_pressure: str | None = None
    heart_rate: float | None = None
    temperature: float | None = None
    conclusion: str | None = None
    lab_results: list[dict] = []
    interpretation: str | None = None
    interpreted_by_id: str | None = None


class ExamRowDTO(BaseModelDTO):
    """Lightweight exam row for lists."""

    id: str
    exam_date: str
    exam_type: str
    exam_type_label: str
    status: str


class SaveExamDTO(BaseModelDTO):
    """DTO for creating / updating an exam session."""

    patient_id: str
    visit_id: str | None = None
    account_id: str | None = None
    exam_date: date
    exam_type: ExamType
    reason_for_visit: str | None = None
    medical_history: str | None = None
    weight: float | None = None
    height: float | None = None
    bmi: float | None = None
    blood_pressure: str | None = None
    heart_rate: float | None = None
    temperature: float | None = None
    conclusion: str | None = None


class UpdateExamSectionsDTO(BaseModelDTO):
    """DTO for updating the medical sections of an exam."""

    reason_for_visit: str | None = None
    medical_history: str | None = None
    weight: float | None = None
    height: float | None = None
    bmi: float | None = None
    blood_pressure: str | None = None
    heart_rate: float | None = None
    temperature: float | None = None
    conclusion: str | None = None
    lab_results: list[dict] | None = None


class InterpretExamDTO(BaseModelDTO):
    """DTO for doctor to submit an interpretation."""

    interpretation: str
