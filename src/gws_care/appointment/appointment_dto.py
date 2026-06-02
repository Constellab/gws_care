"""DTOs for Appointment."""

from datetime import datetime

from gws_core import BaseModelDTO, ModelDTO

from gws_care.appointment.appointment_status import AppointmentStatus
from gws_care.exam.exam_type import ExamType


class AppointmentDTO(ModelDTO):
    """Full appointment record returned to callers."""

    patient_id: str
    patient_name: str
    account_id: str | None = None
    account_name: str | None = None
    scheduled_at: datetime
    exam_type: ExamType
    exam_type_label: str
    status: AppointmentStatus
    notes: str | None = None


class AppointmentRowDTO(BaseModelDTO):
    """Lightweight row for list views."""

    id: str
    patient_id: str
    patient_name: str
    account_name: str | None = None
    scheduled_at: str          # ISO string — Reflex serialises datetime
    exam_type_label: str
    status: str


class SaveAppointmentDTO(BaseModelDTO):
    """DTO for creating or updating an appointment."""

    patient_id: str
    account_id: str | None = None
    scheduled_at: str          # ISO datetime string (YYYY-MM-DDTHH:MM)
    exam_type: str = "other"   # kept for backward-compat; use exam_type_ref_id for new records
    exam_type_ref_id: str | None = None   # ExamTypeRef.id — set by forms using the referential
    notes: str | None = None
    assigned_doctor_id: str | None = None
    duration_minutes: int = 20
    room: str | None = None


class UpdateAppointmentStatusDTO(BaseModelDTO):
    """DTO for status transitions."""

    status: AppointmentStatus
