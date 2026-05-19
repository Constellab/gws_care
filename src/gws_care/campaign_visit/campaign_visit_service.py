"""CRUD + validation service for CampaignVisit."""

from datetime import datetime

from gws_core import BadRequestException, NotFoundException

from gws_care.campaign.campaign import Campaign
from gws_care.campaign.campaign_patient import CampaignPatient
from gws_care.campaign_visit.campaign_visit import CampaignVisit
from gws_care.campaign_visit.campaign_visit_dto import (
    CampaignVisitRowDTO,
    SaveStandaloneVisitDTO,
    ValidateDoctorClinicDTO,
    ValidateDoctorCompanyDTO,
)
from gws_care.campaign_visit.campaign_visit_status import CampaignVisitStatus
from gws_care.patient.patient import Patient
from gws_care.role.care_action import CareAction
from gws_care.role.permission_service import PermissionService
from gws_care.user.user import User
from gws_care.workflow.visit_validation_step import CampaignVisitValidationStep
from gws_care.workflow.visit_validation_workflow import CampaignVisitValidationWorkflow


class CampaignVisitService:
    """Service for managing campaign visits."""

    # ── Queries ───────────────────────────────────────────────────────────────

    @classmethod
    def get_visit(cls, visit_id: str) -> CampaignVisit:
        visit = CampaignVisit.get_or_none(CampaignVisit.id == visit_id)
        if visit is None:
            raise NotFoundException(f"CampaignVisit '{visit_id}' not found")
        return visit

    @classmethod
    def list_for_campaign(cls, campaign_id: str) -> list[CampaignVisit]:
        """Return all visits for a campaign, ordered by patient name."""
        return list(
            CampaignVisit.select()
            .join(Patient)
            .where(CampaignVisit.program == campaign_id)
            .order_by(Patient.last_name, Patient.first_name)
        )

    @classmethod
    def list_for_patient(cls, patient_id: str) -> list[CampaignVisit]:
        """Return all visits for a patient, most recent first."""
        from peewee import JOIN
        return list(
            CampaignVisit.select()
            .join(Campaign, JOIN.LEFT_OUTER)
            .where(CampaignVisit.patient == patient_id)
            .order_by(Campaign.start_date.desc())
        )

    @classmethod
    def to_row_dto(cls, visit: CampaignVisit) -> CampaignVisitRowDTO:
        patient = visit.patient
        account = visit.billing_account if visit.billing_account_id else None
        return CampaignVisitRowDTO(
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
    def create_visit(cls, campaign_id: str, patient_id: str) -> CampaignVisit:
        """Create a new visit for a patient in a campaign.

        Called automatically when a patient is added to a campaign.
        Raises if the visit already exists.
        """
        existing = CampaignVisit.get_or_none(
            (CampaignVisit.program == campaign_id) & (CampaignVisit.patient == patient_id)
        )
        if existing is not None:
            raise BadRequestException("A visit already exists for this patient in this campaign")

        campaign = Campaign.get_or_none(Campaign.id == campaign_id)
        if campaign is None:
            raise NotFoundException(f"Campaign '{campaign_id}' not found")

        patient = Patient.get_or_none(Patient.id == patient_id)
        if patient is None:
            raise NotFoundException(f"Patient '{patient_id}' not found")

        # Ensure the patient-campaign link exists
        if CampaignPatient.get_or_none(
            (CampaignPatient.program == campaign_id) & (CampaignPatient.patient == patient_id)
        ) is None:
            raise BadRequestException("Patient is not enrolled in this campaign")

        visit = CampaignVisit()
        visit.program = campaign
        visit.patient = patient
        visit.status = CampaignVisitStatus.PENDING
        visit.save()
        return visit

    # ── Standalone scheduled visits (no campaign) ─────────────────────────────

    @classmethod
    def list_scheduled(
        cls,
        status: CampaignVisitStatus | None = None,
        search: str = "",
        account_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[CampaignVisit]:
        """Return visits that have a scheduled_at date, ordered soonest first."""
        query = CampaignVisit.select().join(Patient)
        query = query.where(CampaignVisit.scheduled_at.is_null(False))
        if status:
            query = query.where(CampaignVisit.status == status)
        if search:
            term = f"%{search}%"
            query = query.where(
                Patient.last_name ** term
                | Patient.first_name ** term
                | Patient.patient_number ** term
            )
        if account_id:
            query = query.where(CampaignVisit.billing_account == account_id)
        if date_from:
            query = query.where(
                CampaignVisit.scheduled_at >= datetime.fromisoformat(date_from)
            )
        if date_to:
            query = query.where(
                CampaignVisit.scheduled_at <= datetime.fromisoformat(date_to + "T23:59:59")
            )
        return list(query.order_by(CampaignVisit.scheduled_at.asc()))

    @classmethod
    def list_scheduled_for_patient(cls, patient_id: str) -> list[CampaignVisit]:
        """Return scheduled visits for a specific patient, newest first."""
        return list(
            CampaignVisit.select()
            .where((CampaignVisit.patient == patient_id) & CampaignVisit.scheduled_at.is_null(False))
            .order_by(CampaignVisit.scheduled_at.desc())
        )

    @classmethod
    def list_all(
        cls,
        status: CampaignVisitStatus | None = None,
        search: str = "",
        account_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[CampaignVisit]:
        """Return all visits (including campaign visits without scheduled_at).

        Date filters apply only to visits that have a scheduled_at value; visits
        without a scheduled date are always included regardless of date range.
        """
        query = CampaignVisit.select().join(Patient)
        if status:
            query = query.where(CampaignVisit.status == status)
        if search:
            term = f"%{search}%"
            query = query.where(
                Patient.last_name ** term
                | Patient.first_name ** term
                | Patient.patient_number ** term
            )
        if account_id:
            query = query.where(CampaignVisit.billing_account == account_id)
        if date_from:
            query = query.where(
                CampaignVisit.scheduled_at.is_null()
                | (CampaignVisit.scheduled_at >= datetime.fromisoformat(date_from))
            )
        if date_to:
            query = query.where(
                CampaignVisit.scheduled_at.is_null()
                | (CampaignVisit.scheduled_at <= datetime.fromisoformat(date_to + "T23:59:59"))
            )
        query = query.order_by(CampaignVisit.created_at.desc())
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return list(query)

    @classmethod
    def create_standalone_visit(cls, dto: SaveStandaloneVisitDTO) -> CampaignVisit:
        """Create a visit linked to an auto-created individual campaign."""
        visit, _campaign = cls.create_visit_with_default_campaign(
            patient_id=dto.patient_id,
            scheduled_at_str=dto.scheduled_at,
            billing_account_id=dto.billing_account_id,
        )
        return visit

    @classmethod
    def create_visit_with_default_campaign(
        cls,
        patient_id: str,
        scheduled_at_str: str,
        billing_account_id: str | None = None,
    ) -> tuple["CampaignVisit", "Campaign"]:
        """Create an individual campaign and a visit for the patient within it.

        The campaign starts in DRAFT status so exam types can be configured
        before it is moved to IN_PROGRESS.  Returns ``(visit, campaign)``.
        """
        from gws_care.campaign.campaign_status import CampaignStatus

        patient = Patient.get_or_none(Patient.id == patient_id)
        if patient is None:
            raise NotFoundException(f"Patient '{patient_id}' not found")

        try:
            scheduled_at = datetime.fromisoformat(scheduled_at_str)
        except ValueError:
            raise BadRequestException(f"Invalid scheduled_at format: '{scheduled_at_str}'")

        visit_date = scheduled_at.date()

        # Create the auto-generated individual campaign
        campaign = Campaign()
        campaign.name = f"Campaign — {patient.get_full_name()} ({visit_date.isoformat()})"
        campaign.account_id = billing_account_id or None
        campaign.start_date = visit_date
        campaign.end_date = visit_date
        campaign.status = CampaignStatus.DRAFT
        campaign.is_individual = True
        campaign.save()

        # Enroll the patient in the campaign
        CampaignPatient.create(program=campaign, patient=patient)

        # Create the visit
        visit = CampaignVisit()
        visit.program = campaign
        visit.patient = patient
        visit.billing_account_id = billing_account_id or None
        visit.scheduled_at = scheduled_at
        visit.status = CampaignVisitStatus.PENDING
        visit.save()

        return visit, campaign

    @classmethod
    def update_standalone_visit(cls, visit_id: str, dto: SaveStandaloneVisitDTO) -> CampaignVisit:
        """Update a standalone scheduled visit."""
        visit = cls.get_visit(visit_id)
        if visit.status in (CampaignVisitStatus.CANCELLED, CampaignVisitStatus.LAB_DONE,
                             CampaignVisitStatus.DOCTOR_CLINIC_VALIDATED, CampaignVisitStatus.DOCTOR_COMPANY_VALIDATED):
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
    def cancel_visit(cls, visit_id: str) -> CampaignVisit:
        """Cancel a visit (standalone scheduling use case)."""
        visit = cls.get_visit(visit_id)
        if visit.status in (CampaignVisitStatus.LAB_DONE, CampaignVisitStatus.DOCTOR_CLINIC_VALIDATED,
                             CampaignVisitStatus.DOCTOR_COMPANY_VALIDATED):
            raise BadRequestException("Cannot cancel a validated visit.")
        visit.status = CampaignVisitStatus.CANCELLED
        visit.save()
        return visit

    @classmethod
    def force_set_status(cls, visit_id: str, status: str) -> CampaignVisit:
        """Force-set a visit to any status (used by the workflow lifeline to allow going back)."""
        visit = cls.get_visit(visit_id)
        try:
            visit.status = CampaignVisitStatus(status)
        except ValueError:
            raise BadRequestException(f"Invalid visit status: '{status}'")
        visit.save()
        return visit

    @classmethod
    def start_visit(cls, visit_id: str) -> CampaignVisit:
        """Mark visit as visit done (patient seen, samples collected)."""
        visit = cls.get_visit(visit_id)
        if visit.status != CampaignVisitStatus.PENDING:
            raise BadRequestException("Only PENDING visits can be started.")
        visit.status = CampaignVisitStatus.VISIT_DONE
        visit.save()
        return visit

    # ── Lifecycle transitions ─────────────────────────────────────────────────

    @classmethod
    def mark_terrain_done(cls, visit_id: str) -> CampaignVisit:
        """Mark visit as done (patient seen, samples collected)."""
        visit = cls.get_visit(visit_id)
        if visit.status != CampaignVisitStatus.PENDING:
            raise BadRequestException("Only PENDING visits can be marked as visit done")
        now = datetime.utcnow()
        visit.status = CampaignVisitStatus.VISIT_DONE
        visit.save()
        CampaignVisitValidationWorkflow.insert(
            visit=visit,
            step=CampaignVisitValidationStep.VISIT_DONE,
            validated_by=None,
            validated_at=now,
        ).on_conflict_ignore().execute()
        return visit

    @classmethod
    def validate_lab(cls, visit_id: str, user: User) -> CampaignVisit:
        """Lab validation: lock results."""
        PermissionService.require(user, CareAction.VISIT_VALIDATE_LAB)
        visit = cls.get_visit(visit_id)
        if visit.status != CampaignVisitStatus.VISIT_DONE:
            raise BadRequestException("Only VISIT_DONE visits can be lab-validated")
        now = datetime.utcnow()
        visit.status = CampaignVisitStatus.LAB_DONE
        visit.save()
        CampaignVisitValidationWorkflow.insert(
            visit=visit,
            step=CampaignVisitValidationStep.LAB_DONE,
            validated_by=user,
            validated_at=now,
        ).on_conflict_ignore().execute()
        visit.lab_validated_by_id = str(user.id) if user else None
        visit.lab_validated_at = now
        return visit

    @classmethod
    def validate_doctor_clinic(cls, visit_id: str, user: User, dto: ValidateDoctorClinicDTO) -> CampaignVisit:
        """Clinic doctor validation: add interpretation (Validation Clinic Doctor / Employé)."""
        PermissionService.require(user, CareAction.VISIT_VALIDATE_CLINIC)
        visit = cls.get_visit(visit_id)
        if visit.status != CampaignVisitStatus.LAB_DONE:
            raise BadRequestException("Only LAB_DONE visits can be clinic-doctor validated")
        now = datetime.utcnow()
        visit.status = CampaignVisitStatus.DOCTOR_CLINIC_VALIDATED
        visit.doctor_clinic_interpretation = dto.interpretation
        visit.save()
        CampaignVisitValidationWorkflow.insert(
            visit=visit,
            step=CampaignVisitValidationStep.DOCTOR_CLINIC_VALIDATED,
            validated_by=user,
            validated_at=now,
        ).on_conflict_ignore().execute()
        visit.doctor_clinic_validated_by_id = str(user.id) if user else None
        visit.doctor_clinic_validated_at = now
        return visit

    @classmethod
    def validate_doctor_company(cls, visit_id: str, user: User, dto: ValidateDoctorCompanyDTO) -> CampaignVisit:
        """Company doctor validation: add interpretation + patient message.

        Phase 2.3 additions:
        - Notify the patient that their results are available.
        - Auto-advance the campaign to DOCTOR_COMPANY_VALIDATED if every visit
          in the campaign has now reached that status.
        """
        PermissionService.require(user, CareAction.VISIT_VALIDATE_COMPANY)
        visit = cls.get_visit(visit_id)
        if visit.status != CampaignVisitStatus.DOCTOR_CLINIC_VALIDATED:
            raise BadRequestException(
                "Only DOCTOR_CLINIC_VALIDATED visits can be company-doctor validated"
            )
        now = datetime.utcnow()
        visit.status = CampaignVisitStatus.DOCTOR_COMPANY_VALIDATED
        visit.doctor_company_interpretation = dto.interpretation
        visit.doctor_company_message = dto.message
        visit.save()
        CampaignVisitValidationWorkflow.insert(
            visit=visit,
            step=CampaignVisitValidationStep.DOCTOR_COMPANY_VALIDATED,
            validated_by=user,
            validated_at=now,
        ).on_conflict_ignore().execute()
        visit.doctor_company_validated_at = now

        # Notify the patient that their medical results are available
        try:
            from gws_care.notification.notification_service import NotificationService
            patient = visit.patient
            NotificationService.notify_results_available_to_patient(visit, patient, sent_by=user)
        except Exception as exc:
            print(f"[CampaignVisitService] notify_results_available_to_patient failed: {exc}")

        # Auto-advance campaign when all visits are company-doctor validated
        try:
            from gws_care.campaign.campaign_service import CampaignService
            CampaignService.check_and_advance_to_company_validated(str(visit.program_id))
        except Exception as exc:
            print(f"[CampaignVisitService] check_and_advance_to_company_validated failed: {exc}")

        return visit
