"""CRUD service for MedicalProgram."""

from datetime import date, datetime

from gws_core import BadRequestException, NotFoundException

from gws_care.account.account import Account
from gws_care.appointment.appointment import Appointment
from gws_care.exam.exam_type_model import ExamTypeModel
from gws_care.medical_program.medical_program import MedicalProgram
from gws_care.medical_program.medical_program_dto import ProgramRowDTO, SaveProgramDTO
from gws_care.medical_program.medical_program_exam_type import ProgramExamType
from gws_care.medical_program.medical_program_patient import ProgramPatient
from gws_care.medical_program.program_status import ProgramStatus
from gws_care.patient.patient import Patient
from gws_care.role.care_action import CareAction
from gws_care.role.permission_service import PermissionService
from gws_care.user.user import User
from gws_care.visit.visit import Visit
from gws_care.workflow.program_validation_step import ProgramValidationStep
from gws_care.workflow.program_validation_workflow import ProgramValidationWorkflow


class MedicalProgramService:
    """Service for managing programs."""

    # ── Queries ───────────────────────────────────────────────────────────────

    @classmethod
    def get_program(cls, program_id: str) -> MedicalProgram:
        program = MedicalProgram.get_or_none(MedicalProgram.id == program_id)
        if program is None:
            raise NotFoundException(f"MedicalProgram '{program_id}' not found")
        return program

    @classmethod
    def list_programs(
        cls,
        account_id: str | None = None,
        status: ProgramStatus | None = None,
        search: str = "",
        limit: int | None = None,
        offset: int = 0,
    ) -> list[MedicalProgram]:
        query = MedicalProgram.select().order_by(MedicalProgram.start_date.desc())
        if account_id:
            query = query.where(MedicalProgram.account == account_id)
        if status:
            query = query.where(MedicalProgram.status == status)
        if search:
            term = f"%{search}%"
            query = query.where(MedicalProgram.name ** term)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return list(query)

    @classmethod
    def get_patients(cls, program_id: str) -> list[Patient]:
        cls.get_program(program_id)
        return list(
            Patient.select()
            .join(ProgramPatient)
            .where(ProgramPatient.program == program_id)
            .order_by(Patient.last_name, Patient.first_name)
        )

    @classmethod
    def get_exam_types(cls, program_id: str) -> list[ExamTypeModel]:
        cls.get_program(program_id)
        return list(
            ExamTypeModel.select()
            .join(ProgramExamType)
            .where(ProgramExamType.program == program_id)
            .order_by(ExamTypeModel.name)
        )

    @classmethod
    def to_row_dto(cls, program: MedicalProgram) -> ProgramRowDTO:
        patient_count = ProgramPatient.select().where(ProgramPatient.program == program.id).count()
        exam_type_count = ProgramExamType.select().where(ProgramExamType.program == program.id).count()
        return ProgramRowDTO(
            id=str(program.id),
            program_number=program.program_number,
            name=program.name,
            account_name=program.account.name if program.account_id else None,
            start_date=str(program.start_date),
            end_date=str(program.end_date),
            status=program.status.value,
            status_label=program.status.get_label(),
            patient_count=patient_count,
            exam_type_count=exam_type_count,
        )

    # ── Mutations ─────────────────────────────────────────────────────────────

    @classmethod
    def create_program(cls, dto: SaveProgramDTO) -> MedicalProgram:
        cls._validate_dto(dto)
        account = Account.get_or_none(Account.id == dto.account_id) if dto.account_id else None
        if dto.account_id and account is None:
            raise BadRequestException(f"Account '{dto.account_id}' not found")

        program = MedicalProgram()
        program.account = account
        cls._apply_dto(program, dto)
        program.save()
        return program

    @classmethod
    def update_program(cls, program_id: str, dto: SaveProgramDTO) -> MedicalProgram:
        program = cls.get_program(program_id)
        if program.status not in (ProgramStatus.DRAFT, ProgramStatus.VALIDATED):
            raise BadRequestException("Only programs in DRAFT or VALIDATED status can be modified")
        cls._validate_dto(dto)

        new_start = date.fromisoformat(dto.start_date)
        new_end = date.fromisoformat(dto.end_date)
        old_start = program.start_date

        account = Account.get_or_none(Account.id == dto.account_id)
        if account is None:
            raise BadRequestException(f"Account '{dto.account_id}' not found")
        program.account = account
        cls._apply_dto(program, dto)
        program.save()

        # If dates changed, check appointment coherence (raises if incompatible)
        if new_start != old_start or new_end != program.end_date:
            cls._check_appointment_dates(program, new_start, new_end)

        return program

    @classmethod
    def validate_program(cls, program_id: str, user: User) -> MedicalProgram:
        """Validate a DRAFT program (Clinic Doctor or Admin)."""
        program = cls.get_program(program_id)
        if program.status != ProgramStatus.DRAFT:
            raise BadRequestException("Only DRAFT programs can be validated")
        now = datetime.utcnow()
        program.status = ProgramStatus.VALIDATED
        program.save()
        ProgramValidationWorkflow.insert(
            program=program,
            step=ProgramValidationStep.VALIDATED,
            validated_by=user,
            validated_at=now,
        ).on_conflict_ignore().execute()
        return program

    @classmethod
    def start_campaign(cls, program_id: str) -> MedicalProgram:
        """Mark a program as IN_PROGRESS."""
        program = cls.get_program(program_id)
        if program.status != ProgramStatus.VALIDATED:
            raise BadRequestException("Only VALIDATED programs can be started")
        program.status = ProgramStatus.IN_PROGRESS
        program.save()
        return program

    @classmethod
    def mark_lab_done(cls, program_id: str) -> MedicalProgram:
        """Mark a program as LAB_DONE (Lab Validation)."""
        program = cls.get_program(program_id)
        if program.status != ProgramStatus.IN_PROGRESS:
            raise BadRequestException("Only IN_PROGRESS programs can be marked as lab done")
        program.status = ProgramStatus.LAB_DONE
        program.save()
        return program

    @classmethod
    def validate_lab_campaign(cls, program_id: str, user: User) -> MedicalProgram:
        """Phase 2.1 — Lab Validation (HQ Operator).

        Verifies every visit in the program has reached LAB_VALIDATED status,
        then advances the program to LAB_DONE and notifies all Clinic Doctor
        (DOCTOR role) users via bell + email.
        """
        PermissionService.require(user, CareAction.CAMPAIGN_VALIDATE_LAB)
        program = cls.get_program(program_id)
        if program.status != ProgramStatus.IN_PROGRESS:
            raise BadRequestException("Only IN_PROGRESS programs can be lab-validated")

        from gws_care.visit.visit_status import VisitStatus
        cls._assert_all_visits_at_least_status(program_id, VisitStatus.LAB_VALIDATED)

        now = datetime.utcnow()
        program.status = ProgramStatus.LAB_DONE
        program.save()
        ProgramValidationWorkflow.insert(
            program=program,
            step=ProgramValidationStep.LAB_DONE,
            validated_by=user,
            validated_at=now,
        ).on_conflict_ignore().execute()

        try:
            from gws_care.notification.notification_service import NotificationService
            NotificationService.notify_lab_done_to_doctors(program, sent_by=user)
        except Exception as exc:
            print(f"[MedicalProgramService] notify_lab_done_to_doctors failed: {exc}")

        return program

    @classmethod
    def validate_doctor_clinic(cls, program_id: str) -> MedicalProgram:
        """Mark program as DOCTOR_CLINIC_VALIDATED."""
        program = cls.get_program(program_id)
        if program.status != ProgramStatus.LAB_DONE:
            raise BadRequestException("Only LAB_DONE programs can be clinic-doctor validated")
        program.status = ProgramStatus.DOCTOR_CLINIC_VALIDATED
        program.save()
        return program

    @classmethod
    def validate_doctor_clinic_campaign(cls, program_id: str, user: User) -> MedicalProgram:
        """Phase 2.2 — Validation Clinic Doctor.

        Verifies every visit in the program has reached DOCTOR_CLINIC_VALIDATED
        status, then advances the program to DOCTOR_CLINIC_VALIDATED and notifies
        all ACCOUNT_ADMIN users linked to the program's account via bell + email.
        """
        PermissionService.require(user, CareAction.CAMPAIGN_VALIDATE_CLINIC)
        program = cls.get_program(program_id)
        if program.status != ProgramStatus.LAB_DONE:
            raise BadRequestException("Only LAB_DONE programs can be clinic-doctor validated")

        from gws_care.visit.visit_status import VisitStatus
        cls._assert_all_visits_at_least_status(program_id, VisitStatus.DOCTOR_CLINIC_VALIDATED)

        now = datetime.utcnow()
        program.status = ProgramStatus.DOCTOR_CLINIC_VALIDATED
        program.save()
        ProgramValidationWorkflow.insert(
            program=program,
            step=ProgramValidationStep.DOCTOR_CLINIC_VALIDATED,
            validated_by=user,
            validated_at=now,
        ).on_conflict_ignore().execute()

        try:
            from gws_care.notification.notification_service import NotificationService
            NotificationService.notify_clinic_validated_to_account_admins(program, sent_by=user)
        except Exception as exc:
            print(f"[MedicalProgramService] notify_clinic_validated_to_account_admins failed: {exc}")

        return program

    @classmethod
    def check_and_advance_to_company_validated(cls, program_id: str) -> MedicalProgram | None:
        """Phase 2.3 — Auto-advance program to DOCTOR_COMPANY_VALIDATED.

        Called after each visit reaches DOCTOR_COMPANY_VALIDATED. When every
        visit in the program has that status, the program is automatically
        advanced. Returns the updated program, or None if not all visits are done.
        """
        program = cls.get_program(program_id)
        if program.status != ProgramStatus.DOCTOR_CLINIC_VALIDATED:
            return None

        all_done = cls._all_visits_have_status(program_id, "doctor_company_validated")
        if not all_done:
            return None

        now = datetime.utcnow()
        program.status = ProgramStatus.DOCTOR_COMPANY_VALIDATED
        program.save()
        ProgramValidationWorkflow.insert(
            program=program,
            step=ProgramValidationStep.DOCTOR_COMPANY_VALIDATED,
            validated_by=None,
            validated_at=now,
        ).on_conflict_ignore().execute()
        return program

    @classmethod
    def validate_doctor_company(cls, program_id: str) -> MedicalProgram:
        """Mark program as DOCTOR_COMPANY_VALIDATED."""
        program = cls.get_program(program_id)
        if program.status != ProgramStatus.DOCTOR_CLINIC_VALIDATED:
            raise BadRequestException("Only DOCTOR_CLINIC_VALIDATED programs can be company-doctor validated")
        program.status = ProgramStatus.DOCTOR_COMPANY_VALIDATED
        program.save()
        return program

    @classmethod
    def archive_program(cls, program_id: str) -> MedicalProgram:
        program = cls.get_program(program_id)
        program.status = ProgramStatus.ARCHIVED
        program.save()
        return program

    @classmethod
    def force_set_status(cls, program_id: str, status: str) -> MedicalProgram:
        """Force-set a program to any status (used by the workflow lifeline to allow going back)."""
        program = cls.get_program(program_id)
        try:
            program.status = ProgramStatus(status)
        except ValueError:
            raise BadRequestException(f"Invalid program status: '{status}'")
        program.save()
        return program

    # ── Patient management ────────────────────────────────────────────────────

    @classmethod
    def add_patient(cls, program_id: str, patient_id: str) -> None:
        """Add a patient to a program.

        The patient must belong to the program's billing account, unless the
        program has no account (individual / auto-created program).
        """
        program = cls.get_program(program_id)
        if program.status not in (ProgramStatus.DRAFT, ProgramStatus.VALIDATED):
            raise BadRequestException("Patients can only be added to DRAFT or VALIDATED programs")

        if program.is_individual:
            raise BadRequestException("This program is for a single patient and cannot accept additional patients")

        patient = Patient.get_or_none(Patient.id == patient_id)
        if patient is None:
            raise BadRequestException(f"Patient '{patient_id}' not found")

        # Skip account check when the program has no account (individual program)
        if program.account_id:
            from gws_care.patient.patient_account import PatientAccount
            has_link = PatientAccount.get_or_none(
                (PatientAccount.patient_id == patient_id)
                & (PatientAccount.account_id == str(program.account_id))
            ) is not None
            if not has_link:
                raise BadRequestException(
                    "Patient does not belong to the program's billing account"
                )

        if ProgramPatient.get_or_none(
            (ProgramPatient.program == program_id) & (ProgramPatient.patient == patient_id)
        ) is not None:
            raise BadRequestException("Patient is already in this program")

        ProgramPatient.create(program=program, patient=patient)

    @classmethod
    def remove_patient(cls, program_id: str, patient_id: str) -> None:
        program = cls.get_program(program_id)
        # Individual programs allow removal at any status (single-patient, error correction)
        if not program.is_individual and program.status not in (ProgramStatus.DRAFT, ProgramStatus.VALIDATED):
            raise BadRequestException("Patients can only be removed from DRAFT or VALIDATED programs")

        link = ProgramPatient.get_or_none(
            (ProgramPatient.program == program_id) & (ProgramPatient.patient == patient_id)
        )
        if link is None:
            raise BadRequestException("Patient is not in this program")
        link.delete_instance()

    # ── ExamType management ───────────────────────────────────────────────────

    @classmethod
    def add_exam_type(cls, program_id: str, exam_type_id: str) -> None:
        program = cls.get_program(program_id)
        if program.status not in (ProgramStatus.DRAFT, ProgramStatus.VALIDATED):
            raise BadRequestException("Exam types can only be added to DRAFT or VALIDATED programs")

        exam_type = ExamTypeModel.get_or_none(ExamTypeModel.id == exam_type_id)
        if exam_type is None:
            raise BadRequestException(f"ExamType '{exam_type_id}' not found")
        if not exam_type.is_active:
            raise BadRequestException(f"ExamType '{exam_type.name}' is inactive and cannot be added")

        if ProgramExamType.get_or_none(
            (ProgramExamType.program == program_id) & (ProgramExamType.exam_type == exam_type_id)
        ) is not None:
            raise BadRequestException("ExamType is already in this program")

        ProgramExamType.create(program=program, exam_type=exam_type)

    @classmethod
    def remove_exam_type(cls, program_id: str, exam_type_id: str) -> None:
        program = cls.get_program(program_id)
        if program.status not in (ProgramStatus.DRAFT, ProgramStatus.VALIDATED):
            raise BadRequestException("Exam types can only be removed from DRAFT or VALIDATED programs")

        link = ProgramExamType.get_or_none(
            (ProgramExamType.program == program_id) & (ProgramExamType.exam_type == exam_type_id)
        )
        if link is None:
            raise BadRequestException("ExamType is not in this program")
        link.delete_instance()

    # ── Internals ─────────────────────────────────────────────────────────────

    @classmethod
    def _all_visits_have_status(cls, program_id: str, status_value: str) -> bool:
        """Return True only if EVERY visit in the program has exactly the given status value.

        Returns False if there are no visits (empty program).
        """
        from gws_care.visit.visit_status import VisitStatus
        total = Visit.select().where(Visit.program == program_id).count()
        if total == 0:
            return False
        done = Visit.select().where(
            Visit.program == program_id,
            Visit.status == VisitStatus(status_value),
        ).count()
        return done == total

    @classmethod
    def _assert_all_visits_at_least_status(cls, program_id: str, min_status: "VisitStatus") -> None:
        """Raise BadRequestException if any visit has not yet reached min_status.

        Visits that have advanced PAST min_status (e.g. already DOCTOR_CLINIC_VALIDATED
        when checking for LAB_VALIDATED) are considered compliant.
        """
        from gws_care.visit.visit_status import VisitStatus
        status_order = list(VisitStatus)
        min_index = status_order.index(min_status)
        # Statuses that are strictly before the required minimum
        statuses_not_ready = status_order[:min_index]

        total = Visit.select().where(Visit.program == program_id).count()
        if total == 0:
            raise BadRequestException("The program has no visits — cannot validate.")

        if statuses_not_ready:
            not_ready_count = Visit.select().where(
                Visit.program == program_id,
                Visit.status.in_(statuses_not_ready),
            ).count()
        else:
            not_ready_count = 0

        if not_ready_count > 0:
            raise BadRequestException(
                f"{not_ready_count} visit(s) have not yet reached the required status "
                f"'{min_status.value}'. All visits must be validated before advancing the program."
            )

    @classmethod
    def _validate_dto(cls, dto: SaveProgramDTO) -> None:
        if not dto.name or not dto.name.strip():
            raise BadRequestException("MedicalProgram name is required")
        if not dto.account_id:
            raise BadRequestException("Account ID is required")
        try:
            start = date.fromisoformat(dto.start_date)
            end = date.fromisoformat(dto.end_date)
        except (ValueError, TypeError):
            raise BadRequestException("Invalid date format — use YYYY-MM-DD")
        if end < start:
            raise BadRequestException("End date must be on or after start date")

    @classmethod
    def _apply_dto(cls, program: MedicalProgram, dto: SaveProgramDTO) -> None:
        program.name = dto.name.strip()
        program.start_date = date.fromisoformat(dto.start_date)
        program.end_date = date.fromisoformat(dto.end_date)
        program.notes = dto.notes

    @classmethod
    def _check_appointment_dates(cls, program: MedicalProgram, new_start: date, new_end: date) -> None:
        """Raise if any linked appointments fall outside the program date window."""
        incompatible = (
            Appointment.select()
            .where(Appointment.visit.is_null(False))
            .join(Visit, on=(Visit.id == Appointment.visit))
            .where(Visit.program == program.id)
            .where(
                (Appointment.scheduled_at < datetime.combine(new_start, datetime.min.time())) |
                (Appointment.scheduled_at > datetime.combine(new_end, datetime.max.time()))
            )
        )
        count = incompatible.count()
        if count > 0:
            raise BadRequestException(
                f"{count} appointment(s) fall outside the new program date range "
                f"({new_start} — {new_end}). Please adjust or remove them first."
            )
