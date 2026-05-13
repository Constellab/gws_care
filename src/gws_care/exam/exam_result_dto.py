"""ExamResult DTOs — typed result data per exam type."""

from gws_core import BaseModelDTO, ModelDTO

from gws_care.exam.appreciation import Appreciation


class ExamResultDTO(ModelDTO):
    """Full exam result record."""

    exam_id: str
    result_data: dict
    image_paths: list[str]
    appreciation: Appreciation | None = None
    calculated_appreciation: Appreciation | None = None
    appreciation_override: bool = False


class SaveExamResultDTO(BaseModelDTO):
    """DTO for saving/updating an exam result."""

    result_data: dict
    image_paths: list[str] = []
    # Optional: primary numeric value used to auto-calculate appreciation.
    # Callers should supply this when saving a result that has a single measurable value
    # (e.g. glycaemia = 5.8 mmol/L).  Leave None for image-based or multi-parameter exams.
    primary_value: float | None = None
    # Optional: explicitly specify which ExamTypeModel to use for threshold calculation.
    # If omitted, the service will attempt to match by exam category.
    exam_type_model_id: str | None = None


class OverrideAppreciationDTO(BaseModelDTO):
    """DTO for a Clinic Doctor manual appreciation override."""

    appreciation: Appreciation


# ── Per-type result data shapes (used as result_data dict) ────────────────────

class BiologyResultDTO(BaseModelDTO):
    """Biology exam result fields (blood + urine)."""

    # Blood parameters
    hemoglobin: str | None = None
    hematocrit: str | None = None
    rbc: str | None = None          # Red blood cells
    wbc: str | None = None          # White blood cells
    platelets: str | None = None
    glucose: str | None = None
    creatinine: str | None = None
    urea: str | None = None
    cholesterol_total: str | None = None
    cholesterol_hdl: str | None = None
    cholesterol_ldl: str | None = None
    triglycerides: str | None = None
    # Urine parameters
    urine_glucose: str | None = None
    urine_proteins: str | None = None
    urine_leukocytes: str | None = None
    urine_blood: str | None = None
    notes: str | None = None


class ClinicalResultDTO(BaseModelDTO):
    """Clinical exam result — vitals and physical constants."""

    weight_kg: str | None = None
    height_cm: str | None = None
    bmi: str | None = None
    blood_pressure_systolic: str | None = None
    blood_pressure_diastolic: str | None = None
    heart_rate: str | None = None
    temperature_c: str | None = None
    respiratory_rate: str | None = None
    oxygen_saturation: str | None = None
    visual_acuity_left: str | None = None
    visual_acuity_right: str | None = None
    notes: str | None = None


class ImageBasedResultDTO(BaseModelDTO):
    """Result for image/trace-based exams (Radiology, Ophthalmo, ORL, ECG, Spirometry)."""

    findings: str | None = None       # Text findings / description
    notes: str | None = None


class OtherResultDTO(BaseModelDTO):
    """Generic result for other exam types (hormones, drug test, etc.)."""

    parameters: list[dict] = []   # [{name, value, unit, reference_range, abnormal}]
    notes: str | None = None
