"""CRUD + validation service for Visit (Visite Médicale)."""

from datetime import datetime

from gws_core import BadRequestException, NotFoundException

from gws_care.medical_program.medical_program import MedicalProgram
from gws_care.medical_program.medical_program_patient import ProgramPatient
from gws_care.patient.patient import Patient
from gws_care.role.care_action import CareAction
from gws_care.role.permission_service import PermissionService
from gws_care.user.user import User
from gws_care.visit.visit import Visit
from gws_care.visit.visit_dto import (
    SaveStandaloneVisitDTO,
    ValidateDoctorClinicDTO,
    ValidateDoctorCompanyDTO,
    VisitRowDTO,
)
from gws_care.visit.visit_status import VisitStatus
from gws_care.workflow.visit_validation_step import VisitValidationStep
from gws_care.workflow.visit_validation_workflow import VisitValidationWorkflow


class VisitService:
    """Service for managing visits within a program."""

    # ── Queries ───────────────────────────────────────────────────────────────

    @classmethod
    def get_visit(cls, visit_id: str) -> Visit:
        visit = Visit.get_or_none(Visit.id == visit_id)
        if visit is None:
            raise NotFoundException(f"Visit '{visit_id}' not found")
        return visit

    @classmethod
    def list_for_campaign(cls, program_id: str) -> list[Visit]:
        """Return all visits for a program, ordered by patient name."""
        return list(
            Visit.select()
            .join(Patient)
            .where(Visit.program == program_id)
            .order_by(Patient.last_name, Patient.first_name)
        )

    @classmethod
    def list_for_patient(cls, patient_id: str) -> list[Visit]:
        """Return all visits for a patient, most recent first."""
        from peewee import JOIN
        return list(
            Visit.select()
            .join(MedicalProgram, JOIN.LEFT_OUTER)
            .where(Visit.patient == patient_id)
            .order_by(MedicalProgram.start_date.desc())
        )

    @classmethod
    def to_row_dto(cls, visit: Visit) -> VisitRowDTO:
        patient = visit.patient
        account = visit.billing_account if visit.billing_account_id else None
        return VisitRowDTO(
            id=str(visit.id),
            visit_number=visit.visit_number,
            patient_id=str(patient.id) if patient else None,
            patient_name=patient.get_full_name() if patient else None,
            patient_number=patient.patient_number if patient else None,
            billing_account_id=str(visit.billing_account_id) if visit.billing_account_id else None,
            account_name=account.name if account else None,
            scheduled_at=visit.scheduled_at.isoformat() if visit.scheduled_at else None,
            status=visit.status.value,
            status_label=visit.status.get_label(),
        )

    # ── Creation ──────────────────────────────────────────────────────────────

    @classmethod
    def create_visit(cls, program_id: str, patient_id: str) -> Visit:
        """Create a new visit for a patient in a program.

        Called automatically when a patient is added to a program.
        Raises if the visit already exists.
        """
        existing = Visit.get_or_none(
            (Visit.program == program_id) & (Visit.patient == patient_id)
        )
        if existing is not None:
            raise BadRequestException("A visit already exists for this patient in this program")

        program = MedicalProgram.get_or_none(MedicalProgram.id == program_id)
        if program is None:
            raise NotFoundException(f"MedicalProgram '{program_id}' not found")

        patient = Patient.get_or_none(Patient.id == patient_id)
        if patient is None:
            raise NotFoundException(f"Patient '{patient_id}' not found")

        # Ensure the patient-program link exists
        if ProgramPatient.get_or_none(
            (ProgramPatient.program == program_id) & (ProgramPatient.patient == patient_id)
        ) is None:
            raise BadRequestException("Patient is not enrolled in this program")

        visit = Visit()
        visit.program = program
        visit.patient = patient
        visit.status = VisitStatus.PENDING
        visit.save()
        return visit
    # ── Standalone scheduled visits (no program) ─────────────────────────────

    @classmethod
    def list_scheduled(
        cls,
        status: VisitStatus | None = None,
        search: str = "",
        account_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[Visit]:
        """Return visits that have a scheduled_at date, ordered soonest first."""
        query = Visit.select().join(Patient)
        query = query.where(Visit.scheduled_at.is_null(False))
        if status:
            query = query.where(Visit.status == status)
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
                Visit.scheduled_at >= datetime.fromisoformat(date_from)
            )
        if date_to:
            query = query.where(
                Visit.scheduled_at <= datetime.fromisoformat(date_to + "T23:59:59")
            )
        return list(query.order_by(Visit.scheduled_at.asc()))

    @classmethod
    def list_scheduled_for_patient(cls, patient_id: str) -> list[Visit]:
        """Return scheduled visits for a specific patient, newest first."""
        return list(
            Visit.select()
            .where((Visit.patient == patient_id) & Visit.scheduled_at.is_null(False))
            .order_by(Visit.scheduled_at.desc())
        )

    @classmethod
    def list_all(
        cls,
        status: VisitStatus | None = None,
        search: str = "",
        account_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[Visit]:
        """Return all visits (including program visits without scheduled_at).

        Date filters apply only to visits that have a scheduled_at value; visits
        without a scheduled date are always included regardless of date range.
        """
        query = Visit.select().join(Patient)
        if status:
            query = query.where(Visit.status == status)
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
        return list(query.order_by(Visit.created_at.desc()))

    @classmethod
    def create_standalone_visit(cls, dto: SaveStandaloneVisitDTO) -> Visit:
        """Create a visit linked to an auto-created individual program."""
        visit, _program = cls.create_visit_with_default_program(
            patient_id=dto.patient_id,
            scheduled_at_str=dto.scheduled_at,
            billing_account_id=dto.billing_account_id,
        )
        return visit

    @classmethod
    def create_visit_with_default_program(
        cls,
        patient_id: str,
        scheduled_at_str: str,
        billing_account_id: str | None = None,
    ) -> tuple["Visit", "MedicalProgram"]:
        """Create an individual program and a visit for the patient within it.

        The program starts in DRAFT status so exam types can be configured
        before it is moved to IN_PROGRESS.  Returns ``(visit, program)``.
        """
        from gws_care.medical_program.medical_program import MedicalProgram
        from gws_care.medical_program.medical_program_patient import ProgramPatient
        from gws_care.medical_program.program_status import ProgramStatus

        patient = Patient.get_or_none(Patient.id == patient_id)
        if patient is None:
            raise NotFoundException(f"Patient '{patient_id}' not found")

        try:
            scheduled_at = datetime.fromisoformat(scheduled_at_str)
        except ValueError:
            raise BadRequestException(f"Invalid scheduled_at format: '{scheduled_at_str}'")

        visit_date = scheduled_at.date()

        # Create the auto-generated individual program
        program = MedicalProgram()
        program.name = f"Program — {patient.get_full_name()} ({visit_date.isoformat()})"
        program.account_id = billing_account_id or None
        program.start_date = visit_date
        program.end_date = visit_date
        program.status = ProgramStatus.DRAFT
        program.is_individual = True
        program.save()

        # Enroll the patient in the program
        ProgramPatient.create(program=program, patient=patient)

        # Create the visit
        visit = Visit()
        visit.program = program
        visit.patient = patient
        visit.billing_account_id = billing_account_id or None
        visit.scheduled_at = scheduled_at
        visit.status = VisitStatus.PENDING
        visit.save()

        return visit, program

    @classmethod
    def update_standalone_visit(cls, visit_id: str, dto: SaveStandaloneVisitDTO) -> Visit:
        """Update a standalone scheduled visit."""
        visit = cls.get_visit(visit_id)
        if visit.status in (VisitStatus.CANCELLED, VisitStatus.LAB_VALIDATED,
                             VisitStatus.DOCTOR_CLINIC_VALIDATED, VisitStatus.DOCTOR_COMPANY_VALIDATED):
            raise BadRequestException("Cannot edit a visit in its current state.")

        try:
            scheduled_at = datetime.fromisoformat(dto.scheduled_at)
        except ValueError:
            raise BadRequestException(f"Invalid scheduled_at format: '{dto.scheduled_at}'")

        visit.billing_account_id = dto.billing_account_id or None
        visit.scheduled_at = scheduled_at
        visit.save()
        return visit

    @classmethod
    def cancel_visit(cls, visit_id: str) -> Visit:
        """Cancel a visit (standalone scheduling use case)."""
        visit = cls.get_visit(visit_id)
        if visit.status in (VisitStatus.LAB_VALIDATED, VisitStatus.DOCTOR_CLINIC_VALIDATED,
                             VisitStatus.DOCTOR_COMPANY_VALIDATED):
            raise BadRequestException("Cannot cancel a validated visit.")
        visit.status = VisitStatus.CANCELLED
        visit.save()
        return visit

    @classmethod
    def force_set_status(cls, visit_id: str, status: str) -> Visit:
        """Force-set a visit to any status (used by the workflow lifeline to allow going back)."""
        visit = cls.get_visit(visit_id)
        try:
            visit.status = VisitStatus(status)
        except ValueError:
            raise BadRequestException(f"Invalid visit status: '{status}'")
        visit.save()
        return visit

    @classmethod
    def start_visit(cls, visit_id: str) -> Visit:
        """Mark visit as on-site done (patient seen, samples collected)."""
        visit = cls.get_visit(visit_id)
        if visit.status != VisitStatus.PENDING:
            raise BadRequestException("Only PENDING visits can be started.")
        visit.status = VisitStatus.TERRAIN_DONE
        visit.save()
        return visit

    @classmethod
    def complete_visit(cls, visit_id: str) -> Visit:
        """Mark visit as results entered."""
        visit = cls.get_visit(visit_id)
        if visit.status != VisitStatus.TERRAIN_DONE:
            raise BadRequestException("Only TERRAIN_DONE visits can be completed.")
        visit.status = VisitStatus.RESULTS_ENTERED
        visit.save()
        return visit
    # ── Lifecycle transitions ─────────────────────────────────────────────────

    @classmethod
    def mark_terrain_done(cls, visit_id: str) -> Visit:
        """Mark visit on-site phase as done (blood/sample collection complete)."""
        visit = cls.get_visit(visit_id)
        if visit.status != VisitStatus.PENDING:
            raise BadRequestException("Only PENDING visits can be marked as on-site done")
        now = datetime.utcnow()
        visit.status = VisitStatus.TERRAIN_DONE
        visit.save()
        VisitValidationWorkflow.insert(
            visit=visit,
            step=VisitValidationStep.TERRAIN_DONE,
            validated_by=None,
            validated_at=now,
        ).on_conflict_ignore().execute()
        return visit

    @classmethod
    def mark_results_entered(cls, visit_id: str) -> Visit:
        """Mark that all exam results have been entered."""
        visit = cls.get_visit(visit_id)
        if visit.status != VisitStatus.TERRAIN_DONE:
            raise BadRequestException("Only TERRAIN_DONE visits can have results entered")
        now = datetime.utcnow()
        visit.status = VisitStatus.RESULTS_ENTERED
        visit.save()
        VisitValidationWorkflow.insert(
            visit=visit,
            step=VisitValidationStep.RESULTS_ENTERED,
            validated_by=None,
            validated_at=now,
        ).on_conflict_ignore().execute()
        return visit

    @classmethod
    def validate_lab(cls, visit_id: str, user: User) -> Visit:
        """Lab validation: lock results (Lab Validation)."""
        PermissionService.require(user, CareAction.VISIT_VALIDATE_LAB)
        visit = cls.get_visit(visit_id)
        if visit.status != VisitStatus.RESULTS_ENTERED:
            raise BadRequestException("Only RESULTS_ENTERED visits can be lab-validated")
        now = datetime.utcnow()
        visit.status = VisitStatus.LAB_VALIDATED
        visit.save()
        VisitValidationWorkflow.insert(
            visit=visit,
            step=VisitValidationStep.LAB_VALIDATED,
            validated_by=user,
            validated_at=now,
        ).on_conflict_ignore().execute()
        return visit

    @classmethod
    def validate_doctor_clinic(cls, visit_id: str, user: User, dto: ValidateDoctorClinicDTO) -> Visit:
        """Clinic doctor validation: add interpretation (Validation Clinic Doctor / Employé)."""
        PermissionService.require(user, CareAction.VISIT_VALIDATE_CLINIC)
        visit = cls.get_visit(visit_id)
        if visit.status != VisitStatus.LAB_VALIDATED:
            raise BadRequestException("Only LAB_VALIDATED visits can be clinic-doctor validated")
        now = datetime.utcnow()
        visit.status = VisitStatus.DOCTOR_CLINIC_VALIDATED
        visit.doctor_clinic_interpretation = dto.interpretation
        visit.save()
        VisitValidationWorkflow.insert(
            visit=visit,
            step=VisitValidationStep.DOCTOR_CLINIC_VALIDATED,
            validated_by=user,
            validated_at=now,
        ).on_conflict_ignore().execute()
        return visit

    @classmethod
    def validate_doctor_company(cls, visit_id: str, user: User, dto: ValidateDoctorCompanyDTO) -> Visit:
        """Company doctor validation: add interpretation + patient message.

        Phase 2.3 additions:
        - Notify the patient that their results are available.
        - Auto-advance the program to DOCTOR_COMPANY_VALIDATED if every visit
          in the program has now reached that status.
        """
        PermissionService.require(user, CareAction.VISIT_VALIDATE_COMPANY)
        visit = cls.get_visit(visit_id)
        if visit.status != VisitStatus.DOCTOR_CLINIC_VALIDATED:
            raise BadRequestException(
                "Only DOCTOR_CLINIC_VALIDATED visits can be company-doctor validated"
            )
        now = datetime.utcnow()
        visit.status = VisitStatus.DOCTOR_COMPANY_VALIDATED
        visit.doctor_company_interpretation = dto.interpretation
        visit.doctor_company_message = dto.message
        visit.save()
        VisitValidationWorkflow.insert(
            visit=visit,
            step=VisitValidationStep.DOCTOR_COMPANY_VALIDATED,
            validated_by=user,
            validated_at=now,
        ).on_conflict_ignore().execute()

        # Notify the patient that their medical results are available
        try:
            from gws_care.notification.notification_service import NotificationService
            patient = visit.patient
            NotificationService.notify_results_available_to_patient(visit, patient, sent_by=user)
        except Exception as exc:
            print(f"[VisitService] notify_results_available_to_patient failed: {exc}")

        # Auto-advance program when all visits are company-doctor validated
        try:
            from gws_care.medical_program.medical_program_service import MedicalProgramService
            MedicalProgramService.check_and_advance_to_company_validated(str(visit.program_id))
        except Exception as exc:
            print(f"[VisitService] check_and_advance_to_company_validated failed: {exc}")

        return visit
