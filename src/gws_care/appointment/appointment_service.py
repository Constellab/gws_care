"""CRUD service for Appointment."""

from datetime import datetime

from gws_core import BadRequestException, NotFoundException

from gws_care.appointment.appointment import Appointment
from gws_care.appointment.appointment_dto import (
    AppointmentRowDTO,
    SaveAppointmentDTO,
)
from gws_care.appointment.appointment_status import AppointmentStatus
from gws_care.exam.exam_type import ExamType
from gws_care.patient.patient import Patient


class AppointmentService:
    """Service for managing patient appointments."""

    # ── Queries ───────────────────────────────────────────────────────────────

    @classmethod
    def get_appointment(cls, appointment_id: str) -> Appointment:
        appt = Appointment.get_or_none(Appointment.id == appointment_id)
        if appt is None:
            raise NotFoundException(f"Appointment '{appointment_id}' not found")
        return appt

    @classmethod
    def list_all(
        cls,
        status: AppointmentStatus | None = None,
        search: str = "",
        account_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[Appointment]:
        """Return appointments ordered by scheduled_at (soonest first).

        Optionally filter by status, patient name / number search term,
        account, and/or scheduled date range.
        """
        query = Appointment.select().join(Patient)
        if status:
            query = query.where(Appointment.status == status)
        if search:
            term = f"%{search}%"
            query = query.where(
                Patient.last_name ** term
                | Patient.first_name ** term
                | Patient.patient_number ** term
            )
        if account_id:
            query = query.where(Appointment.billing_account == account_id)
        if date_from:
            from datetime import datetime
            query = query.where(
                Appointment.scheduled_at >= datetime.fromisoformat(date_from)
            )
        if date_to:
            from datetime import datetime
            query = query.where(
                Appointment.scheduled_at <= datetime.fromisoformat(date_to + "T23:59:59")
            )
        return list(query.order_by(Appointment.scheduled_at.asc()))

    @classmethod
    def list_for_patient(cls, patient_id: str) -> list[Appointment]:
        """Return all appointments for a specific patient, newest first."""
        return list(
            Appointment.select()
            .where(Appointment.patient == patient_id)
            .order_by(Appointment.scheduled_at.desc())
        )

    @classmethod
    def to_row_dto(cls, appt: Appointment) -> AppointmentRowDTO:
        patient = appt.patient
        account = appt.billing_account if appt.billing_account_id else None
        return AppointmentRowDTO(
            id=str(appt.id),
            patient_id=str(patient.id),
            patient_name=f"{patient.first_name} {patient.last_name}",
            account_name=account.name if account else None,
            scheduled_at=appt.scheduled_at.isoformat(),
            exam_type_label=appt.exam_type.get_label(),
            status=appt.status.value,
        )

    # ── Commands ──────────────────────────────────────────────────────────────

    @classmethod
    def create_appointment(cls, dto: SaveAppointmentDTO) -> Appointment:
        patient = Patient.get_or_none(Patient.id == dto.patient_id)
        if patient is None:
            raise BadRequestException(f"Patient '{dto.patient_id}' not found")

        try:
            exam_type = ExamType(dto.exam_type)
        except ValueError:
            raise BadRequestException(f"Invalid exam type '{dto.exam_type}'")

        try:
            scheduled_at = datetime.fromisoformat(dto.scheduled_at)
        except ValueError:
            raise BadRequestException(f"Invalid scheduled_at format: '{dto.scheduled_at}'")

        appt = Appointment()
        appt.patient = patient
        appt.billing_account_id = dto.account_id or None
        appt.scheduled_at = scheduled_at
        appt.exam_type = exam_type
        appt.status = AppointmentStatus.SCHEDULED
        appt.notes = dto.notes
        appt.save()
        return appt

    @classmethod
    def update_appointment(cls, appointment_id: str, dto: SaveAppointmentDTO) -> Appointment:
        appt = cls.get_appointment(appointment_id)
        if appt.status == AppointmentStatus.DONE:
            raise BadRequestException("Cannot edit a completed appointment.")
        if appt.status == AppointmentStatus.CANCELLED:
            raise BadRequestException("Cannot edit a cancelled appointment.")

        try:
            exam_type = ExamType(dto.exam_type)
        except ValueError:
            raise BadRequestException(f"Invalid exam type '{dto.exam_type}'")

        try:
            scheduled_at = datetime.fromisoformat(dto.scheduled_at)
        except ValueError:
            raise BadRequestException(f"Invalid scheduled_at format: '{dto.scheduled_at}'")

        appt.billing_account_id = dto.account_id or None
        appt.scheduled_at = scheduled_at
        appt.exam_type = exam_type
        appt.notes = dto.notes
        appt.save()
        return appt

    @classmethod
    def set_status(cls, appointment_id: str, status: AppointmentStatus) -> Appointment:
        """Transition an appointment to the given status."""
        appt = cls.get_appointment(appointment_id)
        appt.status = status
        appt.save()
        return appt

    @classmethod
    def cancel_appointment(cls, appointment_id: str) -> Appointment:
        return cls.set_status(appointment_id, AppointmentStatus.CANCELLED)

    @classmethod
    def start_appointment(cls, appointment_id: str) -> Appointment:
        return cls.set_status(appointment_id, AppointmentStatus.IN_PROGRESS)

    @classmethod
    def complete_appointment(cls, appointment_id: str) -> Appointment:
        return cls.set_status(appointment_id, AppointmentStatus.DONE)
