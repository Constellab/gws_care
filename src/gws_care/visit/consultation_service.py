"""Service for managing consultation visits."""

from datetime import datetime

from gws_core import BadRequestException, NotFoundException

from gws_care.patient.patient import Patient
from gws_care.visit.appointment_mode import AppointmentMode
from gws_care.visit.consultation_visit_status import ConsultationVisitStatus
from gws_care.visit.visit import Visit
from gws_care.visit.visit_dto import BookAppointmentDTO
from gws_care.visit.visit_type import VisitType


class ConsultationService:
    """Service for consultation visits (visit_type=CONSULTATION)."""

    # ── Queries ───────────────────────────────────────────────────────────────

    @classmethod
    def get_consultation(cls, visit_id: str) -> Visit:
        visit = Visit.get_or_none(
            (Visit.id == visit_id) & (Visit.visit_type == VisitType.CONSULTATION)
        )
        if visit is None:
            raise NotFoundException(f"Consultation '{visit_id}' not found")
        return visit

    @classmethod
    def list_for_patient(cls, patient_id: str) -> list[Visit]:
        """Return all consultation visits for a patient, most recent first."""
        return list(
            Visit.select()
            .where(
                (Visit.patient == patient_id) & (Visit.visit_type == VisitType.CONSULTATION)
            )
            .order_by(Visit.scheduled_at.desc())
        )

    @classmethod
    def list_all(
        cls,
        status: ConsultationVisitStatus | None = None,
        search: str = "",
        account_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Visit]:
        """Return all consultation visits with optional filters."""
        query = Visit.select().join(Patient)
        query = query.where(Visit.visit_type == VisitType.CONSULTATION)
        if status:
            query = query.where(Visit.consultation_visit_status == status)
        if search:
            term = f"%{search}%"
            query = query.where(
                Patient.last_name ** term
                | Patient.first_name ** term
                | Patient.patient_number ** term
            )
        if account_id:
            query = query.where(Visit.billing_account == account_id)
        if date_from:
            query = query.where(
                Visit.scheduled_at.is_null()
                | (Visit.scheduled_at >= datetime.fromisoformat(date_from))
            )
        if date_to:
            query = query.where(
                Visit.scheduled_at.is_null()
                | (Visit.scheduled_at <= datetime.fromisoformat(date_to + "T23:59:59"))
            )
        query = query.order_by(Visit.scheduled_at.desc(), Visit.created_at.desc())
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return list(query)

    # ── Creation ──────────────────────────────────────────────────────────────

    @classmethod
    def create_consultation(
        cls,
        patient_id: str,
        scheduled_at_str: str | None = None,
        billing_account_id: str | None = None,
    ) -> Visit:
        """Create a new consultation visit."""
        patient = Patient.get_or_none(Patient.id == patient_id)
        if patient is None:
            raise NotFoundException(f"Patient '{patient_id}' not found")

        visit = Visit()
        visit.visit_type = VisitType.CONSULTATION
        visit.patient = patient
        visit.billing_account_id = billing_account_id or None
        visit.consultation_visit_status = ConsultationVisitStatus.SCHEDULED
        if scheduled_at_str:
            try:
                visit.scheduled_at = datetime.fromisoformat(scheduled_at_str)
            except ValueError:
                raise BadRequestException(f"Invalid scheduled_at format: '{scheduled_at_str}'")
        visit.save()
        return visit

    @classmethod
    def create_from_patient_booking(cls, dto: BookAppointmentDTO, patient_id: str) -> Visit:
        """Create a consultation visit from a patient self-booking request."""
        patient = Patient.get_or_none(Patient.id == patient_id)
        if patient is None:
            raise NotFoundException(f"Patient '{patient_id}' not found")

        try:
            scheduled_at = datetime.fromisoformat(dto.scheduled_at)
        except (ValueError, TypeError):
            raise BadRequestException(f"Invalid scheduled_at format: '{dto.scheduled_at}'")

        try:
            mode = AppointmentMode(dto.appointment_mode) if dto.appointment_mode else AppointmentMode.ONSITE
        except ValueError:
            mode = AppointmentMode.ONSITE

        doctor_id = None
        if dto.doctor_id:
            from gws_care.doctor.medical_doctor import MedicalDoctor
            doctor = MedicalDoctor.get_or_none(MedicalDoctor.id == dto.doctor_id)
            if doctor is None:
                raise BadRequestException(f"Doctor '{dto.doctor_id}' not found")
            doctor_id = doctor.id

        visit = Visit()
        visit.visit_type = VisitType.CONSULTATION
        visit.patient = patient
        visit.consultation_visit_status = ConsultationVisitStatus.SCHEDULED
        visit.scheduled_at = scheduled_at
        visit.doctor_id = doctor_id
        visit.appointment_mode = mode
        visit.patient_notes = dto.patient_notes or None
        visit.save()
        return visit

    # ── Lifecycle transitions ─────────────────────────────────────────────────

    @classmethod
    def mark_in_progress(cls, visit_id: str) -> Visit:
        """Mark a consultation as in-progress (patient being seen)."""
        visit = cls.get_consultation(visit_id)
        if visit.consultation_visit_status != ConsultationVisitStatus.SCHEDULED:
            raise BadRequestException("Only SCHEDULED consultations can be started.")
        visit.consultation_visit_status = ConsultationVisitStatus.IN_PROGRESS
        visit.save()
        return visit

    @classmethod
    def mark_done(cls, visit_id: str, closed_by_user_id: str | None = None) -> Visit:
        """Mark a consultation as done."""
        visit = cls.get_consultation(visit_id)
        if visit.consultation_visit_status not in (
            ConsultationVisitStatus.SCHEDULED,
            ConsultationVisitStatus.IN_PROGRESS,
        ):
            raise BadRequestException("Cannot close a consultation in its current state.")
        visit.consultation_visit_status = ConsultationVisitStatus.DONE
        if closed_by_user_id:
            visit.closed_by_id = closed_by_user_id
            visit.closed_at = datetime.utcnow()
        visit.save()
        return visit

    @classmethod
    def cancel(cls, visit_id: str) -> Visit:
        """Cancel a consultation."""
        visit = cls.get_consultation(visit_id)
        if visit.consultation_visit_status == ConsultationVisitStatus.DONE:
            raise BadRequestException("Cannot cancel a completed consultation.")
        visit.consultation_visit_status = ConsultationVisitStatus.CANCELLED
        visit.save()
        return visit
