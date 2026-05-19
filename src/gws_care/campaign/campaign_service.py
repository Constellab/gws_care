"""CRUD service for Campaign."""

from datetime import date, datetime

from gws_core import BadRequestException, NotFoundException

from gws_care.account.account import Account
from gws_care.appointment.appointment import Appointment
from gws_care.campaign.campaign import Campaign
from gws_care.campaign.campaign_dto import CampaignRowDTO, SaveCampaignDTO
from gws_care.campaign.campaign_exam_type import CampaignExamType
from gws_care.campaign.campaign_patient import CampaignPatient
from gws_care.campaign.campaign_status import CampaignStatus
from gws_care.exam.exam_type_model import ExamTypeModel
from gws_care.patient.patient import Patient
from gws_care.role.care_action import CareAction
from gws_care.role.permission_service import PermissionService
from gws_care.user.user import User
from gws_care.workflow.program_validation_step import CampaignValidationStep
from gws_care.workflow.program_validation_workflow import CampaignValidationWorkflow


class CampaignService:
    """Service for managing campaigns."""

    # ── Queries ───────────────────────────────────────────────────────────────

    @classmethod
    def get_campaign(cls, campaign_id: str) -> Campaign:
        campaign = Campaign.get_or_none(Campaign.id == campaign_id)
        if campaign is None:
            raise NotFoundException(f"Campaign '{campaign_id}' not found")
        return campaign

    @classmethod
    def list_campaigns(
        cls,
        account_id: str | None = None,
        status: CampaignStatus | None = None,
        search: str = "",
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Campaign]:
        query = Campaign.select().order_by(Campaign.start_date.desc())
        if account_id:
            query = query.where(Campaign.account == account_id)
        if status:
            query = query.where(Campaign.status == status)
        if search:
            term = f"%{search}%"
            query = query.where(Campaign.name ** term)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return list(query)

    @classmethod
    def get_patients(cls, campaign_id: str) -> list[Patient]:
        cls.get_campaign(campaign_id)
        return list(
            Patient.select()
            .join(CampaignPatient)
            .where(CampaignPatient.program == campaign_id)
            .order_by(Patient.last_name, Patient.first_name)
        )

    @classmethod
    def get_exam_types(cls, campaign_id: str) -> list[ExamTypeModel]:
        cls.get_campaign(campaign_id)
        return list(
            ExamTypeModel.select()
            .join(CampaignExamType)
            .where(CampaignExamType.program == campaign_id)
            .order_by(ExamTypeModel.name)
        )

    @classmethod
    def to_row_dto(cls, campaign: Campaign) -> CampaignRowDTO:
        patient_count = CampaignPatient.select().where(CampaignPatient.program == campaign.id).count()
        exam_type_count = CampaignExamType.select().where(CampaignExamType.program == campaign.id).count()
        return CampaignRowDTO(
            id=str(campaign.id),
            program_number=campaign.program_number,
            name=campaign.name,
            account_name=campaign.account.name if campaign.account_id else None,
            start_date=str(campaign.start_date),
            end_date=str(campaign.end_date),
            status=campaign.status.value,
            status_label=campaign.status.get_label(),
            patient_count=patient_count,
            exam_type_count=exam_type_count,
        )

    # ── Mutations ─────────────────────────────────────────────────────────────

    @classmethod
    def create_campaign(cls, dto: SaveCampaignDTO) -> Campaign:
        cls._validate_dto(dto)
        account = Account.get_or_none(Account.id == dto.account_id) if dto.account_id else None
        if dto.account_id and account is None:
            raise BadRequestException(f"Account '{dto.account_id}' not found")

        campaign = Campaign()
        campaign.account = account
        cls._apply_dto(campaign, dto)
        campaign.save()
        return campaign

    @classmethod
    def update_campaign(cls, campaign_id: str, dto: SaveCampaignDTO) -> Campaign:
        campaign = cls.get_campaign(campaign_id)
        if campaign.status not in (CampaignStatus.DRAFT, CampaignStatus.VALIDATED):
            raise BadRequestException("Only campaigns in DRAFT or VALIDATED status can be modified")
        cls._validate_dto(dto)

        new_start = date.fromisoformat(dto.start_date)
        new_end = date.fromisoformat(dto.end_date)
        old_start = campaign.start_date

        account = Account.get_or_none(Account.id == dto.account_id)
        if account is None:
            raise BadRequestException(f"Account '{dto.account_id}' not found")
        campaign.account = account
        cls._apply_dto(campaign, dto)
        campaign.save()

        # If dates changed, check appointment coherence (raises if incompatible)
        if new_start != old_start or new_end != campaign.end_date:
            cls._check_appointment_dates(campaign, new_start, new_end)

        return campaign

    @classmethod
    def validate_campaign(cls, campaign_id: str, user: User) -> Campaign:
        """Validate a DRAFT campaign (Clinic Doctor or Admin)."""
        campaign = cls.get_campaign(campaign_id)
        if campaign.status != CampaignStatus.DRAFT:
            raise BadRequestException("Only DRAFT campaigns can be validated")
        now = datetime.utcnow()
        campaign.status = CampaignStatus.VALIDATED
        campaign.save()
        CampaignValidationWorkflow.insert(
            program=campaign,
            step=CampaignValidationStep.VALIDATED,
            validated_by=user,
            validated_at=now,
        ).on_conflict_ignore().execute()
        return campaign

    @classmethod
    def start_campaign(cls, campaign_id: str) -> Campaign:
        """Mark a campaign as IN_PROGRESS."""
        campaign = cls.get_campaign(campaign_id)
        if campaign.status != CampaignStatus.VALIDATED:
            raise BadRequestException("Only VALIDATED campaigns can be started")
        campaign.status = CampaignStatus.IN_PROGRESS
        campaign.save()
        return campaign

    @classmethod
    def mark_lab_done(cls, campaign_id: str) -> Campaign:
        """Mark a campaign as LAB_DONE (Lab Validation)."""
        campaign = cls.get_campaign(campaign_id)
        if campaign.status != CampaignStatus.IN_PROGRESS:
            raise BadRequestException("Only IN_PROGRESS campaigns can be marked as lab done")
        campaign.status = CampaignStatus.LAB_DONE
        campaign.save()
        return campaign

    @classmethod
    def validate_lab_campaign(cls, campaign_id: str, user: User) -> Campaign:
        """Phase 2.1 — Lab Validation (HQ Operator).

        Verifies every visit in the campaign has reached LAB_DONE status,
        then advances the campaign to LAB_DONE and notifies all Clinic Doctor
        (DOCTOR role) users via bell + email.
        """
        PermissionService.require(user, CareAction.CAMPAIGN_VALIDATE_LAB)
        campaign = cls.get_campaign(campaign_id)
        if campaign.status != CampaignStatus.IN_PROGRESS:
            raise BadRequestException("Only IN_PROGRESS campaigns can be lab-validated")

        from gws_care.campaign_visit.campaign_visit_status import CampaignVisitStatus
        cls._assert_all_visits_at_least_status(campaign_id, CampaignVisitStatus.LAB_DONE)

        now = datetime.utcnow()
        campaign.status = CampaignStatus.LAB_DONE
        campaign.save()
        CampaignValidationWorkflow.insert(
            program=campaign,
            step=CampaignValidationStep.LAB_DONE,
            validated_by=user,
            validated_at=now,
        ).on_conflict_ignore().execute()

        try:
            from gws_care.notification.notification_service import NotificationService
            NotificationService.notify_lab_done_to_doctors(campaign, sent_by=user)
        except Exception as exc:
            print(f"[CampaignService] notify_lab_done_to_doctors failed: {exc}")

        return campaign

    @classmethod
    def validate_doctor_clinic(cls, campaign_id: str) -> Campaign:
        """Mark campaign as DOCTOR_CLINIC_VALIDATED."""
        campaign = cls.get_campaign(campaign_id)
        if campaign.status != CampaignStatus.LAB_DONE:
            raise BadRequestException("Only LAB_DONE campaigns can be clinic-doctor validated")
        campaign.status = CampaignStatus.DOCTOR_CLINIC_VALIDATED
        campaign.save()
        return campaign

    @classmethod
    def validate_doctor_clinic_campaign(cls, campaign_id: str, user: User) -> Campaign:
        """Phase 2.2 — Validation Clinic Doctor.

        Verifies every visit in the campaign has reached DOCTOR_CLINIC_VALIDATED
        status, then advances the campaign to DOCTOR_CLINIC_VALIDATED and notifies
        all ACCOUNT_ADMIN users linked to the campaign's account via bell + email.
        """
        PermissionService.require(user, CareAction.CAMPAIGN_VALIDATE_CLINIC)
        campaign = cls.get_campaign(campaign_id)
        if campaign.status != CampaignStatus.LAB_DONE:
            raise BadRequestException("Only LAB_DONE campaigns can be clinic-doctor validated")

        from gws_care.campaign_visit.campaign_visit_status import CampaignVisitStatus
        cls._assert_all_visits_at_least_status(campaign_id, CampaignVisitStatus.DOCTOR_CLINIC_VALIDATED)

        now = datetime.utcnow()
        campaign.status = CampaignStatus.DOCTOR_CLINIC_VALIDATED
        campaign.save()
        CampaignValidationWorkflow.insert(
            program=campaign,
            step=CampaignValidationStep.DOCTOR_CLINIC_VALIDATED,
            validated_by=user,
            validated_at=now,
        ).on_conflict_ignore().execute()

        try:
            from gws_care.notification.notification_service import NotificationService
            NotificationService.notify_clinic_validated_to_account_admins(campaign, sent_by=user)
        except Exception as exc:
            print(f"[CampaignService] notify_clinic_validated_to_account_admins failed: {exc}")

        return campaign

    @classmethod
    def check_and_advance_to_company_validated(cls, campaign_id: str) -> Campaign | None:
        """Phase 2.3 — Auto-advance campaign to DOCTOR_COMPANY_VALIDATED.

        Called after each visit reaches DOCTOR_COMPANY_VALIDATED. When every
        visit in the campaign has that status, the campaign is automatically
        advanced. Returns the updated campaign, or None if not all visits are done.
        """
        campaign = cls.get_campaign(campaign_id)
        if campaign.status != CampaignStatus.DOCTOR_CLINIC_VALIDATED:
            return None

        all_done = cls._all_visits_have_status(campaign_id, "doctor_company_validated")
        if not all_done:
            return None

        now = datetime.utcnow()
        campaign.status = CampaignStatus.DOCTOR_COMPANY_VALIDATED
        campaign.save()
        CampaignValidationWorkflow.insert(
            program=campaign,
            step=CampaignValidationStep.DOCTOR_COMPANY_VALIDATED,
            validated_by=None,
            validated_at=now,
        ).on_conflict_ignore().execute()
        return campaign

    @classmethod
    def validate_doctor_company(cls, campaign_id: str) -> Campaign:
        """Mark campaign as DOCTOR_COMPANY_VALIDATED."""
        campaign = cls.get_campaign(campaign_id)
        if campaign.status != CampaignStatus.DOCTOR_CLINIC_VALIDATED:
            raise BadRequestException("Only DOCTOR_CLINIC_VALIDATED campaigns can be company-doctor validated")
        campaign.status = CampaignStatus.DOCTOR_COMPANY_VALIDATED
        campaign.save()
        return campaign

    @classmethod
    def archive_campaign(cls, campaign_id: str) -> Campaign:
        campaign = cls.get_campaign(campaign_id)
        campaign.status = CampaignStatus.ARCHIVED
        campaign.save()
        return campaign

    @classmethod
    def close_campaign(cls, campaign_id: str) -> Campaign:
        campaign = cls.get_campaign(campaign_id)
        campaign.status = CampaignStatus.CLOSED
        campaign.save()
        return campaign

    @classmethod
    def force_set_status(cls, campaign_id: str, status: str) -> Campaign:
        """Force-set a campaign to any status (used by the workflow lifeline to allow going back)."""
        campaign = cls.get_campaign(campaign_id)
        try:
            campaign.status = CampaignStatus(status)
        except ValueError:
            raise BadRequestException(f"Invalid campaign status: '{status}'")
        campaign.save()
        return campaign

    # ── Patient management ────────────────────────────────────────────────────

    @classmethod
    def add_patient(cls, campaign_id: str, patient_id: str) -> None:
        """Add a patient to a campaign.

        The patient must belong to the campaign's billing account, unless the
        campaign has no account (individual / auto-created campaign).
        """
        campaign = cls.get_campaign(campaign_id)
        if campaign.status not in (CampaignStatus.DRAFT, CampaignStatus.VALIDATED):
            raise BadRequestException("Patients can only be added to DRAFT or VALIDATED campaigns")

        if campaign.is_individual:
            raise BadRequestException("This campaign is for a single patient and cannot accept additional patients")

        patient = Patient.get_or_none(Patient.id == patient_id)
        if patient is None:
            raise BadRequestException(f"Patient '{patient_id}' not found")

        # Skip account check when the campaign has no account (individual campaign)
        if campaign.account_id:
            from gws_care.patient.patient_account import PatientAccount
            has_link = PatientAccount.get_or_none(
                (PatientAccount.patient_id == patient_id)
                & (PatientAccount.account_id == str(campaign.account_id))
            ) is not None
            if not has_link:
                raise BadRequestException(
                    "Patient does not belong to the campaign's billing account"
                )

        if CampaignPatient.get_or_none(
            (CampaignPatient.program == campaign_id) & (CampaignPatient.patient == patient_id)
        ) is not None:
            raise BadRequestException("Patient is already in this campaign")

        CampaignPatient.create(program=campaign, patient=patient)

    @classmethod
    def remove_patient(cls, campaign_id: str, patient_id: str) -> None:
        campaign = cls.get_campaign(campaign_id)
        # Individual campaigns allow removal at any status (single-patient, error correction)
        if not campaign.is_individual and campaign.status not in (CampaignStatus.DRAFT, CampaignStatus.VALIDATED):
            raise BadRequestException("Patients can only be removed from DRAFT or VALIDATED campaigns")

        link = CampaignPatient.get_or_none(
            (CampaignPatient.program == campaign_id) & (CampaignPatient.patient == patient_id)
        )
        if link is None:
            raise BadRequestException("Patient is not in this campaign")
        link.delete_instance()

    # ── ExamType management ───────────────────────────────────────────────────

    @classmethod
    def add_exam_type(cls, campaign_id: str, exam_type_id: str) -> None:
        campaign = cls.get_campaign(campaign_id)
        if campaign.status not in (CampaignStatus.DRAFT, CampaignStatus.VALIDATED):
            raise BadRequestException("Exam types can only be added to DRAFT or VALIDATED campaigns")

        exam_type = ExamTypeModel.get_or_none(ExamTypeModel.id == exam_type_id)
        if exam_type is None:
            raise BadRequestException(f"ExamType '{exam_type_id}' not found")
        if not exam_type.is_active:
            raise BadRequestException(f"ExamType '{exam_type.name}' is inactive and cannot be added")

        if CampaignExamType.get_or_none(
            (CampaignExamType.program == campaign_id) & (CampaignExamType.exam_type == exam_type_id)
        ) is not None:
            raise BadRequestException("ExamType is already in this campaign")

        CampaignExamType.create(program=campaign, exam_type=exam_type)

    @classmethod
    def remove_exam_type(cls, campaign_id: str, exam_type_id: str) -> None:
        campaign = cls.get_campaign(campaign_id)
        if campaign.status not in (CampaignStatus.DRAFT, CampaignStatus.VALIDATED):
            raise BadRequestException("Exam types can only be removed from DRAFT or VALIDATED campaigns")

        link = CampaignExamType.get_or_none(
            (CampaignExamType.program == campaign_id) & (CampaignExamType.exam_type == exam_type_id)
        )
        if link is None:
            raise BadRequestException("ExamType is not in this campaign")
        link.delete_instance()

    # ── Internals ─────────────────────────────────────────────────────────────

    @classmethod
    def _all_visits_have_status(cls, campaign_id: str, status_value: str) -> bool:
        """Return True only if EVERY visit in the campaign has exactly the given status value.

        Returns False if there are no visits (empty campaign).
        """
        from gws_care.campaign_visit.campaign_visit import CampaignVisit
        from gws_care.campaign_visit.campaign_visit_status import CampaignVisitStatus
        total = CampaignVisit.select().where(CampaignVisit.program == campaign_id).count()
        if total == 0:
            return False
        done = CampaignVisit.select().where(
            CampaignVisit.program == campaign_id,
            CampaignVisit.status == CampaignVisitStatus(status_value),
        ).count()
        return done == total

    @classmethod
    def _assert_all_visits_at_least_status(cls, campaign_id: str, min_status: "CampaignVisitStatus") -> None:
        """Raise BadRequestException if any visit has not yet reached min_status.

        Visits that have advanced PAST min_status (e.g. already DOCTOR_CLINIC_VALIDATED
        when checking for LAB_DONE) are considered compliant.
        """
        from gws_care.campaign_visit.campaign_visit import CampaignVisit
        from gws_care.campaign_visit.campaign_visit_status import CampaignVisitStatus
        status_order = list(CampaignVisitStatus)
        min_index = status_order.index(min_status)
        # Statuses that are strictly before the required minimum
        statuses_not_ready = status_order[:min_index]

        total = CampaignVisit.select().where(CampaignVisit.program == campaign_id).count()
        if total == 0:
            raise BadRequestException("The campaign has no visits — cannot validate.")

        if statuses_not_ready:
            not_ready_count = CampaignVisit.select().where(
                CampaignVisit.program == campaign_id,
                CampaignVisit.status.in_(statuses_not_ready),
            ).count()
        else:
            not_ready_count = 0

        if not_ready_count > 0:
            raise BadRequestException(
                f"{not_ready_count} visit(s) have not yet reached the required status "
                f"'{min_status.value}'. All visits must be validated before advancing the campaign."
            )

    @classmethod
    def _validate_dto(cls, dto: SaveCampaignDTO) -> None:
        if not dto.name or not dto.name.strip():
            raise BadRequestException("Campaign name is required")
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
    def _apply_dto(cls, campaign: Campaign, dto: SaveCampaignDTO) -> None:
        campaign.name = dto.name.strip()
        campaign.start_date = date.fromisoformat(dto.start_date)
        campaign.end_date = date.fromisoformat(dto.end_date)
        campaign.notes = dto.notes

    @classmethod
    def _check_appointment_dates(cls, campaign: Campaign, new_start: date, new_end: date) -> None:
        """Raise if any linked appointments fall outside the campaign date window."""
        from gws_care.campaign_visit.campaign_visit import CampaignVisit
        incompatible = (
            Appointment.select()
            .where(Appointment.visit.is_null(False))
            .join(CampaignVisit, on=(CampaignVisit.id == Appointment.visit))
            .where(CampaignVisit.program == campaign.id)
            .where(
                (Appointment.scheduled_at < datetime.combine(new_start, datetime.min.time())) |
                (Appointment.scheduled_at > datetime.combine(new_end, datetime.max.time()))
            )
        )
        count = incompatible.count()
        if count > 0:
            raise BadRequestException(
                f"{count} appointment(s) fall outside the new campaign date range "
                f"({new_start} — {new_end}). Please adjust or remove them first."
            )
