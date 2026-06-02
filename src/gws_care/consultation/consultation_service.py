"""Service for creating and managing Consultation records."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from gws_care.consultation.consultation import Consultation
from gws_care.exam.exam import Exam
from gws_care.exam.exam_type import ExamStatus, ExamType
from gws_care.patient.patient import Patient


class ExamOrderDTO(BaseModel):
    """One exam type to order within the consultation."""

    exam_type_id: str  # ExamTypeRef.id
    selected_param_ids: list[str] = []  # if empty → all params of this type are prescribed


class CreateConsultationDTO(BaseModel):
    patient_id: str
    consultation_date: str   # ISO date string "YYYY-MM-DD"
    account_id: str | None = None
    reason_for_visit: str | None = None
    medical_history: str | None = None
    weight: float | None = None
    height: float | None = None
    bmi: float | None = None
    blood_pressure: str | None = None
    heart_rate: float | None = None
    temperature: float | None = None
    conclusion: str | None = None
    exam_orders: list[ExamOrderDTO] = []


class ConsultationService:

    @classmethod
    def create_consultation_with_exams(cls, dto: CreateConsultationDTO) -> Consultation:
        """Create one Consultation and one Exam per ordered exam type."""
        patient = Patient.get_by_id(dto.patient_id)

        consult = Consultation()
        consult.patient = patient
        consult.billing_account_id = dto.account_id
        consult.consultation_date = date.fromisoformat(dto.consultation_date)
        consult.reason_for_visit = dto.reason_for_visit
        consult.medical_history = dto.medical_history
        consult.weight = dto.weight
        consult.height = dto.height
        consult.bmi = dto.bmi
        consult.blood_pressure = dto.blood_pressure
        consult.heart_rate = dto.heart_rate
        consult.temperature = dto.temperature
        consult.conclusion = dto.conclusion
        consult.save()

        for order in dto.exam_orders:
            # Use only the selected parameters; fall back to all params if none explicitly chosen
            from gws_care.exam_type_ref.exam_parameter import ExamParameter
            if order.selected_param_ids:
                param_ids = [
                    str(p.id)
                    for p in ExamParameter.select(ExamParameter.id)
                    .where(
                        ExamParameter.exam_type_ref == order.exam_type_id,
                        ExamParameter.id.in_(order.selected_param_ids),
                    )
                    .order_by(ExamParameter.display_order)
                ]
            else:
                param_ids = [
                    str(p.id)
                    for p in ExamParameter.select(ExamParameter.id)
                    .where(ExamParameter.exam_type_ref == order.exam_type_id)
                    .order_by(ExamParameter.display_order)
                ]

            exam = Exam()
            exam.patient = patient
            exam.consultation_id = consult.id
            exam.exam_date = date.fromisoformat(dto.consultation_date)
            exam.exam_type = ExamType.OTHER      # legacy field — real type stored in exam_type_ref_id
            exam.exam_type_ref_id = order.exam_type_id
            exam.status = ExamStatus.DRAFT
            exam.billing_account_id = dto.account_id
            exam.requested_param_ids = param_ids if param_ids else None
            exam.save()

        return consult

    @classmethod
    def list_for_patient(cls, patient_id: str) -> list[Consultation]:
        return list(
            Consultation.select()
            .where(Consultation.patient == patient_id)
            .order_by(Consultation.consultation_date.desc())
        )

    @classmethod
    def count_all(cls, consultation_type: str | None = None) -> int:
        """Return total number of consultations (for pagination).

        Args:
            consultation_type: ``"patient"`` to count only patient consultations,
                ``"enterprise"`` to count only enterprise consultations, or
                ``None`` to count all (default).
        """
        q = Consultation.select()
        if consultation_type == "patient":
            q = q.where(Consultation.billing_account.is_null(True))
        elif consultation_type == "enterprise":
            q = q.where(Consultation.billing_account.is_null(False))
        return q.count()

    @classmethod
    def list_all(
        cls,
        limit: int = 50,
        offset: int = 0,
        consultation_type: str | None = None,
    ) -> list[Consultation]:
        """Return a paginated list of all consultations, newest first.

        Args:
            limit: Maximum number of rows to return.
            offset: Number of rows to skip.
            consultation_type: ``"patient"``, ``"enterprise"``, or ``None`` for all.
        """
        from gws_care.patient.patient import Patient
        q = (
            Consultation.select(Consultation, Patient)
            .join(Patient)
            .order_by(Consultation.consultation_date.desc())
        )
        if consultation_type == "patient":
            q = q.where(Consultation.billing_account.is_null(True))
        elif consultation_type == "enterprise":
            q = q.where(Consultation.billing_account.is_null(False))
        return list(q.limit(limit).offset(offset))

    @classmethod
    def get_or_none(cls, consultation_id: str) -> Consultation | None:
        return Consultation.get_or_none(Consultation.id == consultation_id)

    @classmethod
    def update_consultation(cls, consultation_id: str, dto: CreateConsultationDTO) -> Consultation:
        """Update the clinical context of an existing consultation."""
        consult = Consultation.get_by_id(consultation_id)
        consult.reason_for_visit = dto.reason_for_visit
        consult.medical_history = dto.medical_history
        consult.weight = dto.weight
        consult.height = dto.height
        consult.bmi = dto.bmi
        consult.blood_pressure = dto.blood_pressure
        consult.heart_rate = dto.heart_rate
        consult.temperature = dto.temperature
        consult.conclusion = dto.conclusion
        consult.save()
        return consult
