"""CRUD service for Campaign."""

from datetime import date, datetime

from gws_care.account.account import Account
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
from gws_care.workflow.campaign_validation_step import CampaignValidationStep
from gws_care.workflow.campaign_validation_workflow import CampaignValidationWorkflow
from gws_core import BadRequestException, NotFoundException


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
            query = query.where(Campaign.name**term)
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
            .where(CampaignPatient.campaign == campaign_id)
            .order_by(Patient.last_name, Patient.first_name)
        )

    @classmethod
    def get_exam_types(cls, campaign_id: str) -> list[ExamTypeModel]:
        cls.get_campaign(campaign_id)
        return list(
            ExamTypeModel.select()
            .join(CampaignExamType)
            .where(CampaignExamType.campaign == campaign_id)
            .order_by(ExamTypeModel.name)
        )

    @classmethod
    def to_row_dto(cls, campaign: Campaign) -> CampaignRowDTO:
        patient_count = (
            CampaignPatient.select().where(CampaignPatient.campaign == campaign.id).count()
        )
        exam_type_count = (
            CampaignExamType.select().where(CampaignExamType.campaign == campaign.id).count()
        )
        return CampaignRowDTO(
            id=str(campaign.id),
            campaign_number=campaign.campaign_number,
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
            campaign=campaign,
            step=CampaignValidationStep.VALIDATED,
            validated_by=user,
            validated_at=now,
        ).on_conflict_ignore().execute()
        return campaign

    @classmethod
    def start_campaign(cls, campaign_id: str) -> Campaign:
        """Mark a campaign as TERRAIN_EXAM (field operations started)."""
        campaign = cls.get_campaign(campaign_id)
        if campaign.status != CampaignStatus.VALIDATED:
            raise BadRequestException("Only VALIDATED campaigns can be started")
        campaign.status = CampaignStatus.TERRAIN_EXAM
        campaign.save()
        return campaign

    @classmethod
    def complete_terrain_phase(cls, campaign_id: str) -> Campaign:
        """Transition TERRAIN_EXAM → SAMPLE_ANALYSIS (terrain work done, start lab entry).

        Requires every visit to be either visit_done (or beyond) or cancelled.
        Any pending visit blocks the transition.
        """
        from gws_care.visit.campaign_visit_status import CampaignVisitStatus
        from gws_care.visit.visit import Visit

        campaign = cls.get_campaign(campaign_id)
        if campaign.status != CampaignStatus.TERRAIN_EXAM:
            raise BadRequestException(
                "Seules les campagnes en phase Terrain Exam peuvent passer en Analyse."
            )
        pending_count = (
            Visit.select()
            .where(
                Visit.campaign == campaign_id,
                Visit.campaign_visit_status == CampaignVisitStatus.PENDING,
            )
            .count()
        )
        if pending_count > 0:
            raise BadRequestException(
                f"{pending_count} visite(s) sont encore en attente. "
                "Toutes les visites doivent être terminées ou annulées avant de clôturer la phase terrain."
            )
        campaign.status = CampaignStatus.SAMPLE_ANALYSIS
        campaign.save()
        return campaign

    @classmethod
    def mark_lab_done(cls, campaign_id: str) -> Campaign:
        """Mark a campaign as LAB_DONE (Lab Validation)."""
        campaign = cls.get_campaign(campaign_id)
        if campaign.status not in (CampaignStatus.TERRAIN_EXAM, CampaignStatus.SAMPLE_ANALYSIS):
            raise BadRequestException(
                "Only TERRAIN_EXAM or SAMPLE_ANALYSIS campaigns can be marked as lab done"
            )
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
        if campaign.status not in (CampaignStatus.TERRAIN_EXAM, CampaignStatus.SAMPLE_ANALYSIS):
            raise BadRequestException(
                "Only TERRAIN_EXAM or SAMPLE_ANALYSIS campaigns can be lab-validated"
            )

        from gws_care.visit.campaign_visit_status import CampaignVisitStatus

        cls._assert_all_visits_at_least_status(campaign_id, CampaignVisitStatus.LAB_DONE)

        now = datetime.utcnow()
        campaign.status = CampaignStatus.LAB_DONE
        campaign.save()
        CampaignValidationWorkflow.insert(
            campaign=campaign,
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

        from gws_care.visit.campaign_visit_status import CampaignVisitStatus

        cls._assert_all_visits_at_least_status(
            campaign_id, CampaignVisitStatus.DOCTOR_CLINIC_VALIDATED
        )

        now = datetime.utcnow()
        campaign.status = CampaignStatus.DOCTOR_CLINIC_VALIDATED
        campaign.save()
        CampaignValidationWorkflow.insert(
            campaign=campaign,
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
            campaign=campaign,
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
            raise BadRequestException(
                "Only DOCTOR_CLINIC_VALIDATED campaigns can be company-doctor validated"
            )
        campaign.status = CampaignStatus.DOCTOR_COMPANY_VALIDATED
        campaign.save()
        return campaign

    @classmethod
    def archive_campaign(cls, campaign_id: str, reason: str | None = None) -> Campaign:
        campaign = cls.get_campaign(campaign_id)
        campaign.status = CampaignStatus.ARCHIVED
        if reason:
            campaign.archive_reason = reason
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
            raise BadRequestException(
                "Les patients ne peuvent être ajoutés qu'aux campagnes en statut Brouillon ou Validée."
            )

        if campaign.is_individual:
            raise BadRequestException(
                "Cette campagne est destinée à un seul patient et n'accepte pas de patients supplémentaires."
            )

        patient = Patient.get_or_none(Patient.id == patient_id)
        if patient is None:
            raise BadRequestException(f"Patient '{patient_id}' not found")

        # Skip account check when the campaign has no account (individual campaign)
        if campaign.account_id:
            from gws_care.patient.patient_account import PatientAccount

            # Accept the patient if they are linked via PatientAccount (billing account)
            # OR if their company_id matches the company behind the campaign's account.
            has_account_link = (
                PatientAccount.get_or_none(
                    (PatientAccount.patient_id == patient_id)
                    & (PatientAccount.account_id == str(campaign.account_id))
                )
                is not None
            )
            has_company_link = False
            if not has_account_link and campaign.account_id:
                acc = campaign.account
                if (
                    acc
                    and acc.company_id
                    and patient.company_id
                    and str(patient.company_id) == str(acc.company_id)
                ):
                    has_company_link = True
            if not has_account_link and not has_company_link:
                raise BadRequestException(
                    "Ce patient n'est pas rattaché au compte de facturation de cette campagne."
                )

        if (
            CampaignPatient.get_or_none(
                (CampaignPatient.campaign == campaign_id) & (CampaignPatient.patient == patient_id)
            )
            is not None
        ):
            raise BadRequestException("Ce patient est déjà dans cette campagne.")

        CampaignPatient.create(campaign=campaign, patient=patient)

        from gws_care.visit.campaign_visit_service import CampaignVisitService

        CampaignVisitService.create_visit(campaign_id, patient_id)

    @classmethod
    def remove_patient(cls, campaign_id: str, patient_id: str) -> None:
        campaign = cls.get_campaign(campaign_id)
        # Individual campaigns allow removal at any status (single-patient, error correction)
        if not campaign.is_individual and campaign.status not in (
            CampaignStatus.DRAFT,
            CampaignStatus.VALIDATED,
        ):
            raise BadRequestException(
                "Patients can only be removed from DRAFT or VALIDATED campaigns"
            )

        link = CampaignPatient.get_or_none(
            (CampaignPatient.campaign == campaign_id) & (CampaignPatient.patient == patient_id)
        )
        if link is None:
            raise BadRequestException("Patient is not in this campaign")
        link.delete_instance()

        from gws_care.visit.visit import Visit

        orphan_visit = Visit.get_or_none(
            (Visit.campaign == campaign_id) & (Visit.patient == patient_id)
        )
        if orphan_visit is not None:
            orphan_visit.delete_instance()

    # ── ExamTypeRef management (new referential-based system) ─────────────────

    @classmethod
    def get_exam_refs(cls, campaign_id: str):
        """Return the list of ExamTypeRef objects linked to the campaign."""
        from gws_care.campaign.campaign_exam import CampaignExam
        from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef

        return list(
            ExamTypeRef.select()
            .join(CampaignExam, on=(CampaignExam.exam_type_ref == ExamTypeRef.id))
            .where(CampaignExam.campaign == campaign_id)
            .order_by(ExamTypeRef.category, ExamTypeRef.name)
        )

    @classmethod
    def get_exam_refs_with_doctor(cls, campaign_id: str) -> list[tuple]:
        """Return list of (ExamTypeRef, CampaignExam) pairs for a campaign."""
        from gws_care.campaign.campaign_exam import CampaignExam
        from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef

        rows = list(
            CampaignExam.select(CampaignExam, ExamTypeRef)
            .join(ExamTypeRef)
            .where(CampaignExam.campaign == campaign_id)
            .order_by(CampaignExam.id)
        )
        return [(row.exam_type_ref, row) for row in rows]

    @classmethod
    def add_exam_ref(cls, campaign_id: str, exam_ref_id: str) -> None:
        """Link an ExamTypeRef to a campaign."""
        from gws_care.campaign.campaign_exam import CampaignExam
        from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef

        campaign = cls.get_campaign(campaign_id)
        if campaign.status not in (CampaignStatus.DRAFT, CampaignStatus.VALIDATED):
            raise BadRequestException(
                "Exam types can only be added to DRAFT or VALIDATED campaigns"
            )
        ref = ExamTypeRef.get_or_none(ExamTypeRef.id == exam_ref_id)
        if ref is None:
            raise BadRequestException(f"ExamTypeRef '{exam_ref_id}' not found")
        if not ref.is_active:
            raise BadRequestException(f"L'examen '{ref.name}' est inactif.")
        if (
            CampaignExam.get_or_none(
                (CampaignExam.campaign == campaign_id) & (CampaignExam.exam_type_ref == exam_ref_id)
            )
            is not None
        ):
            raise BadRequestException("Ce type d'examen est déjà dans cette campagne.")
        CampaignExam.create(campaign=campaign, exam_type_ref=ref)

    @classmethod
    def remove_exam_ref(cls, campaign_id: str, exam_ref_id: str) -> None:
        """Unlink an ExamTypeRef from a campaign."""
        from gws_care.campaign.campaign_exam import CampaignExam

        campaign = cls.get_campaign(campaign_id)
        if campaign.status not in (CampaignStatus.DRAFT, CampaignStatus.VALIDATED):
            raise BadRequestException(
                "Exam types can only be removed from DRAFT or VALIDATED campaigns"
            )
        link = CampaignExam.get_or_none(
            (CampaignExam.campaign == campaign_id) & (CampaignExam.exam_type_ref == exam_ref_id)
        )
        if link is None:
            raise BadRequestException("Ce type d'examen n'est pas dans cette campagne.")
        link.delete_instance()

    @classmethod
    def assign_doctor_to_exam_ref(
        cls, campaign_id: str, exam_ref_id: str, doctor_id: str | None
    ) -> None:
        """Assign (or unassign) a MedicalDoctor to an exam type within a campaign."""
        from gws_care.campaign.campaign_exam import CampaignExam
        from gws_care.doctor.medical_doctor import MedicalDoctor

        link = CampaignExam.get_or_none(
            (CampaignExam.campaign == campaign_id) & (CampaignExam.exam_type_ref == exam_ref_id)
        )
        if link is None:
            raise BadRequestException("Ce type d'examen n'est pas dans cette campagne.")
        if doctor_id:
            doc = MedicalDoctor.get_or_none(MedicalDoctor.id == doctor_id)
            if doc is None:
                raise BadRequestException("Médecin introuvable.")
            link.assigned_doctor_id = str(doc.id)
            link.assigned_doctor_name = doc.get_full_name()
        else:
            link.assigned_doctor_id = None
            link.assigned_doctor_name = None
        link.save()

    @classmethod
    def get_campaign_exam_doctors_map(cls, campaign_id: str) -> dict:
        """Return {exam_type_ref_id: [MedicalDoctor, ...]} for all exams in the campaign."""
        from gws_care.campaign.campaign_exam import CampaignExam
        from gws_care.campaign.campaign_exam_doctor import CampaignExamDoctor
        from gws_care.doctor.medical_doctor import MedicalDoctor

        rows = (
            CampaignExamDoctor.select(CampaignExamDoctor, MedicalDoctor, CampaignExam)
            .join(MedicalDoctor)
            .switch(CampaignExamDoctor)
            .join(CampaignExam)
            .where(CampaignExam.campaign == campaign_id)
        )
        result: dict = {}
        for row in rows:
            ref_id = str(row.campaign_exam.exam_type_ref_id)
            result.setdefault(ref_id, []).append(row.doctor)
        return result

    @classmethod
    def set_exam_location_mode(cls, campaign_id: str, exam_ref_id: str, mode: str | None) -> None:
        """Set (or clear) the location/mode for an exam type in a campaign."""
        from gws_care.campaign.campaign_exam import CampaignExam
        from gws_care.visit.appointment_mode import AppointmentMode

        link = CampaignExam.get_or_none(
            (CampaignExam.campaign == campaign_id) & (CampaignExam.exam_type_ref == exam_ref_id)
        )
        if link is None:
            raise BadRequestException("Ce type d'examen n'est pas dans cette campagne.")
        link.location_mode = AppointmentMode(mode) if mode else None
        link.save()

    @classmethod
    def assign_doctors_to_exam_ref(
        cls, campaign_id: str, exam_ref_id: str, doctor_ids: list
    ) -> None:
        """Assign multiple doctors to an exam type in a campaign.

        Replaces any previous assignment. Each doctor is also automatically
        added to the campaign's Médecins tab (CampaignDoctor).
        """
        from gws_care.campaign.campaign_exam import CampaignExam
        from gws_care.campaign.campaign_exam_doctor import CampaignExamDoctor
        from gws_care.doctor.medical_doctor import MedicalDoctor

        link = CampaignExam.get_or_none(
            (CampaignExam.campaign == campaign_id) & (CampaignExam.exam_type_ref == exam_ref_id)
        )
        if link is None:
            raise BadRequestException("Ce type d'examen n'est pas dans cette campagne.")

        CampaignExamDoctor.delete().where(CampaignExamDoctor.campaign_exam == link.id).execute()

        for doctor_id in doctor_ids:
            doc = MedicalDoctor.get_or_none(MedicalDoctor.id == doctor_id)
            if doc is None:
                continue
            CampaignExamDoctor.create(campaign_exam=link, doctor=doc)
            cls.add_doctor_to_campaign(campaign_id, str(doc.id))

    # ── Per-patient medical workflow ──────────────────────────────────────────

    @classmethod
    def _get_campaign_patient(cls, campaign_id: str, patient_id: str) -> CampaignPatient:
        from gws_care.campaign.campaign_patient import MedicalRecordStatus

        cp = CampaignPatient.get_or_none(
            (CampaignPatient.campaign == campaign_id) & (CampaignPatient.patient == patient_id)
        )
        if cp is None:
            raise BadRequestException(
                f"Patient '{patient_id}' not found in campaign '{campaign_id}'."
            )
        return cp

    @classmethod
    def mark_lab_entered(cls, campaign_id: str, patient_id: str) -> None:
        """Mark patient results as entered by operator/lab (draft saved)."""
        from gws_care.campaign.campaign_patient import MedicalRecordStatus

        cp = cls._get_campaign_patient(campaign_id, patient_id)
        if cp.medical_status == MedicalRecordStatus.PENDING.value:
            cp.medical_status = MedicalRecordStatus.LAB_ENTERED.value
            cp.save()

    @classmethod
    def save_psc_notes_draft(cls, campaign_id: str, patient_id: str, notes: str) -> None:
        """Save PSC doctor notes as draft (no status change)."""
        cp = cls._get_campaign_patient(campaign_id, patient_id)
        cp.psc_notes = notes
        cp.save()

    @classmethod
    def add_psc_interpretation(cls, campaign_id: str, patient_id: str, notes: str) -> None:
        """Save PSC interpretation and advance status to PSC_INTERPRETED."""
        from gws_care.campaign.campaign_patient import MedicalRecordStatus

        cp = cls._get_campaign_patient(campaign_id, patient_id)
        cp.psc_notes = notes
        cp.medical_status = MedicalRecordStatus.PSC_INTERPRETED.value
        cp.save()

    @classmethod
    def validate_psc_patient(cls, campaign_id: str, patient_id: str) -> None:
        """Mark PSC interpretation as validated and advance to PSC_VALIDATED."""
        from gws_care.campaign.campaign_patient import MedicalRecordStatus

        cp = cls._get_campaign_patient(campaign_id, patient_id)
        cp.medical_status = MedicalRecordStatus.PSC_VALIDATED.value
        cp.psc_validated_at = datetime.utcnow()
        cp.save()

    @classmethod
    def validate_psc_campaign(cls, campaign_id: str) -> None:
        """Mark all PSC_INTERPRETED patients in campaign as PSC_VALIDATED."""
        from gws_care.campaign.campaign_patient import MedicalRecordStatus

        CampaignPatient.update(
            medical_status=MedicalRecordStatus.PSC_VALIDATED.value,
            psc_validated_at=datetime.utcnow(),
        ).where(
            (CampaignPatient.campaign == campaign_id)
            & (CampaignPatient.medical_status == MedicalRecordStatus.PSC_INTERPRETED.value)
        ).execute()

    @classmethod
    def transmit_to_treating_doctor(cls, campaign_id: str, patient_id: str) -> None:
        """Record that results have been transmitted to the patient's treating doctor."""
        from gws_care.campaign.campaign_patient import MedicalRecordStatus

        cp = cls._get_campaign_patient(campaign_id, patient_id)
        cp.treating_doctor_transmitted_at = datetime.utcnow()
        if cp.medical_status in (
            MedicalRecordStatus.PSC_VALIDATED.value,
            MedicalRecordStatus.PSC_INTERPRETED.value,
            MedicalRecordStatus.LAB_VALIDATED.value,
            MedicalRecordStatus.LAB_ENTERED.value,
        ):
            cp.medical_status = MedicalRecordStatus.TRANSMITTED_TREATING_DOCTOR.value
        cp.save()

    @classmethod
    def add_enterprise_interpretation(
        cls, campaign_id: str, patient_id: str, notes: str, patient_message: str = ""
    ) -> None:
        """Save enterprise doctor interpretation."""
        cp = cls._get_campaign_patient(campaign_id, patient_id)
        cp.enterprise_notes = notes
        cp.patient_message = patient_message or notes
        cp.save()

    @classmethod
    def validate_enterprise_patient(cls, campaign_id: str, patient_id: str) -> None:
        """Mark enterprise validation as done and advance to ENTERPRISE_VALIDATED."""
        from gws_care.campaign.campaign_patient import MedicalRecordStatus

        cp = cls._get_campaign_patient(campaign_id, patient_id)
        cp.medical_status = MedicalRecordStatus.ENTERPRISE_VALIDATED.value
        cp.enterprise_validated_at = datetime.utcnow()
        cp.save()

    @classmethod
    def finish_patient_record(cls, campaign_id: str, patient_id: str) -> None:
        """Close the patient dossier (PUBLISHED)."""
        from gws_care.campaign.campaign_patient import MedicalRecordStatus

        cp = cls._get_campaign_patient(campaign_id, patient_id)
        cp.medical_status = MedicalRecordStatus.PUBLISHED.value
        cp.published_at = datetime.utcnow()
        cp.save()

    # ── ExamType management (legacy ExamTypeModel-based) ─────────────────────

    @classmethod
    def add_exam_type(cls, campaign_id: str, exam_type_id: str) -> None:
        campaign = cls.get_campaign(campaign_id)
        if campaign.status not in (CampaignStatus.DRAFT, CampaignStatus.VALIDATED):
            raise BadRequestException(
                "Exam types can only be added to DRAFT or VALIDATED campaigns"
            )

        exam_type = ExamTypeModel.get_or_none(ExamTypeModel.id == exam_type_id)
        if exam_type is None:
            raise BadRequestException(f"ExamType '{exam_type_id}' not found")
        if not exam_type.is_active:
            raise BadRequestException(
                f"ExamType '{exam_type.name}' is inactive and cannot be added"
            )

        if (
            CampaignExamType.get_or_none(
                (CampaignExamType.campaign == campaign_id)
                & (CampaignExamType.exam_type == exam_type_id)
            )
            is not None
        ):
            raise BadRequestException("Ce type d'examen est déjà dans cette campagne.")

        CampaignExamType.create(campaign=campaign, exam_type=exam_type)

        from gws_care.visit.campaign_visit_service import CampaignVisitService
        from gws_care.visit.visit import Visit

        for cp in CampaignPatient.select().where(CampaignPatient.campaign == campaign_id):
            if (
                Visit.get_or_none(
                    (Visit.campaign == campaign_id) & (Visit.patient == cp.patient_id)
                )
                is None
            ):
                CampaignVisitService.create_visit(campaign_id, str(cp.patient_id))

    @classmethod
    def remove_exam_type(cls, campaign_id: str, exam_type_id: str) -> None:
        campaign = cls.get_campaign(campaign_id)
        if campaign.status not in (CampaignStatus.DRAFT, CampaignStatus.VALIDATED):
            raise BadRequestException(
                "Exam types can only be removed from DRAFT or VALIDATED campaigns"
            )

        link = CampaignExamType.get_or_none(
            (CampaignExamType.campaign == campaign_id)
            & (CampaignExamType.exam_type == exam_type_id)
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
        from gws_care.visit.campaign_visit_status import CampaignVisitStatus
        from gws_care.visit.visit import Visit

        total = Visit.select().where(Visit.campaign == campaign_id).count()
        if total == 0:
            return False
        done = (
            Visit.select()
            .where(
                Visit.campaign == campaign_id,
                Visit.campaign_visit_status == CampaignVisitStatus(status_value),
            )
            .count()
        )
        return done == total

    @classmethod
    def _assert_all_visits_at_least_status(
        cls, campaign_id: str, min_status: "CampaignVisitStatus"
    ) -> None:
        """Raise BadRequestException if any non-cancelled visit has not yet reached min_status.

        Cancelled visits are explicitly excluded — a patient who did not attend
        should never block campaign progression.
        Visits that have advanced past min_status are considered compliant.
        """
        from gws_care.visit.campaign_visit_status import CampaignVisitStatus
        from gws_care.visit.visit import Visit

        status_order = [s for s in CampaignVisitStatus if s != CampaignVisitStatus.CANCELLED]
        min_index = status_order.index(min_status)
        # Statuses that are strictly before the required minimum (cancelled already excluded)
        statuses_not_ready = status_order[:min_index]

        active_total = (
            Visit.select()
            .where(
                Visit.campaign == campaign_id,
                Visit.campaign_visit_status != CampaignVisitStatus.CANCELLED,
            )
            .count()
        )
        if active_total == 0:
            raise BadRequestException(
                "La campagne n'a aucune visite active — impossible de valider."
            )

        if statuses_not_ready:
            not_ready_count = (
                Visit.select()
                .where(
                    Visit.campaign == campaign_id,
                    Visit.campaign_visit_status.in_(statuses_not_ready),
                )
                .count()
            )
        else:
            not_ready_count = 0

        if not_ready_count > 0:
            raise BadRequestException(
                f"{not_ready_count} visite(s) n'ont pas encore atteint le statut requis "
                f"'{min_status.value}'. Toutes les visites actives doivent être validées avant d'avancer la campagne."
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

    # ── Campaign doctor management ────────────────────────────────────────────

    @classmethod
    def list_campaign_doctors(cls, campaign_id: str):
        """Return MedicalDoctor records assigned to this campaign."""
        from gws_care.campaign.campaign_doctor import CampaignDoctor
        from gws_care.doctor.medical_doctor import MedicalDoctor

        links = (
            CampaignDoctor.select(CampaignDoctor, MedicalDoctor)
            .join(MedicalDoctor)
            .where(CampaignDoctor.campaign == campaign_id)
            .order_by(MedicalDoctor.last_name, MedicalDoctor.first_name)
        )
        return [link.doctor for link in links]

    @classmethod
    def add_doctor_to_campaign(cls, campaign_id: str, doctor_id: str) -> None:
        from gws_care.campaign.campaign_doctor import CampaignDoctor
        from gws_care.doctor.medical_doctor import MedicalDoctor

        doc = MedicalDoctor.get_or_none(MedicalDoctor.id == doctor_id)
        if doc is None:
            raise BadRequestException("Médecin introuvable.")
        existing = CampaignDoctor.get_or_none(
            (CampaignDoctor.campaign == campaign_id) & (CampaignDoctor.doctor == doctor_id)
        )
        if existing:
            return  # already linked — idempotent
        CampaignDoctor.create(campaign=campaign_id, doctor=doctor_id)

    @classmethod
    def remove_doctor_from_campaign(cls, campaign_id: str, doctor_id: str) -> None:
        from gws_care.campaign.campaign_doctor import CampaignDoctor

        CampaignDoctor.delete().where(
            (CampaignDoctor.campaign == campaign_id) & (CampaignDoctor.doctor == doctor_id)
        ).execute()
