"""CampaignService — CRUD and workflow operations for Campaign and CampaignPatient."""

from datetime import date, datetime

from gws_care.account.account import Account
from gws_care.campaign.campaign import Campaign
from gws_care.campaign.campaign_patient import CampaignPatient, MedicalRecordStatus, PresenceStatus
from gws_care.campaign.campaign_status import CampaignStatus
from gws_care.user.user import User


class CampaignValidationError(Exception):
    """Raised when a workflow transition cannot proceed due to business rules."""


class CampaignService:
    """Service layer for Campaign management — CRUD + full lifecycle workflow."""

    # ── CRUD ──────────────────────────────────────────────────────────────

    @classmethod
    def create_campaign(
        cls,
        account_id: str,
        name: str,
        start_date: date | None = None,
        end_date: date | None = None,
        location: str | None = None,
        psc_doctor_id: str | None = None,
        enterprise_doctor_id: str | None = None,
        requires_medical_review: bool = False,
        notes: str | None = None,
    ) -> Campaign:
        account = Account.get_by_id_and_check(account_id)
        if not account.is_active:
            raise CampaignValidationError("Impossible de créer une campagne pour un compte archivé.")
        if start_date and end_date and end_date < start_date:
            raise CampaignValidationError("La date de fin doit être ≥ à la date de début.")
        campaign = Campaign()
        campaign.account = account
        campaign.name = name
        campaign.status = CampaignStatus.DRAFT
        campaign.start_date = start_date
        campaign.end_date = end_date
        campaign.location = location
        campaign.requires_medical_review = requires_medical_review
        campaign.notes = notes
        if psc_doctor_id:
            campaign.psc_doctor = User.get_by_id_and_check(psc_doctor_id)
        if enterprise_doctor_id:
            campaign.enterprise_doctor = User.get_by_id_and_check(enterprise_doctor_id)
        campaign.save()
        return campaign

    @classmethod
    def update_campaign(
        cls,
        campaign_id: str,
        name: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        location: str | None = None,
        psc_doctor_id: str | None = None,
        enterprise_doctor_id: str | None = None,
        requires_medical_review: bool | None = None,
        notes: str | None = None,
    ) -> Campaign:
        campaign = Campaign.get_by_id_and_check(campaign_id)
        if campaign.status not in (CampaignStatus.DRAFT, CampaignStatus.AWAITING_OP_VALIDATION):
            raise CampaignValidationError("La campagne ne peut être modifiée qu'en statut Brouillon ou En attente.")
        _start = start_date if start_date is not None else campaign.start_date
        _end = end_date if end_date is not None else campaign.end_date
        if _start and _end and _end < _start:
            raise CampaignValidationError("La date de fin doit être ≥ à la date de début.")
        if name is not None:
            campaign.name = name
        if start_date is not None:
            campaign.start_date = start_date
        if end_date is not None:
            campaign.end_date = end_date
        if location is not None:
            campaign.location = location
        if requires_medical_review is not None:
            campaign.requires_medical_review = requires_medical_review
        if notes is not None:
            campaign.notes = notes
        if psc_doctor_id is not None:
            campaign.psc_doctor_id = psc_doctor_id or None
        if enterprise_doctor_id is not None:
            campaign.enterprise_doctor_id = enterprise_doctor_id or None
        campaign.save()
        return campaign

    @classmethod
    def list_campaigns_for_account(cls, account_id: str) -> list[Campaign]:
        return list(
            Campaign.select()
            .where(Campaign.account == account_id)
            .order_by(Campaign.created_at.desc())
        )

    @classmethod
    def list_all_campaigns(cls, status: str | None = None) -> list[Campaign]:
        q = Campaign.select().order_by(Campaign.created_at.desc())
        if status:
            q = q.where(Campaign.status == status)
        return list(q)

    @classmethod
    def get_campaign(cls, campaign_id: str) -> Campaign:
        return Campaign.get_by_id_and_check(campaign_id)

    @classmethod
    def patient_count(cls, campaign_id: str) -> int:
        return CampaignPatient.select().where(CampaignPatient.campaign == campaign_id).count()

    # ── Patient enrollment ────────────────────────────────────────────────

    @classmethod
    def add_patient(cls, campaign_id: str, patient_id: str) -> CampaignPatient:
        """Enroll a patient in a campaign (US-050 rule: patient must be affiliated to the account)."""
        from gws_care.patient.patient import Patient
        from gws_care.patient_account.patient_account_service import PatientAccountService
        campaign = Campaign.get_by_id_and_check(campaign_id)
        account_id = str(campaign.account_id)

        # Deux mécanismes d'affiliation acceptés :
        # 1. PatientAccount M2M (affiliation formelle avec contrat)
        # 2. Patient.billing_account FK directe (affiliation simple)
        affiliated_m2m = PatientAccountService.is_patient_affiliated_to_account(patient_id, account_id)
        try:
            affiliated_fk = str(Patient.get_by_id_and_check(patient_id).billing_account_id) == account_id
        except Exception:
            affiliated_fk = False

        if not (affiliated_m2m or affiliated_fk):
            raise CampaignValidationError(
                "Le patient n'est pas rattaché au Compte de facturation de cette campagne."
            )
        if CampaignPatient.select().where(
            (CampaignPatient.campaign == campaign_id) & (CampaignPatient.patient == patient_id)
        ).exists():
            raise CampaignValidationError("Ce patient est déjà inscrit dans cette campagne.")
        cp = CampaignPatient()
        cp.campaign_id = campaign_id
        cp.patient_id = patient_id
        cp.presence_status = PresenceStatus.PENDING.value
        cp.medical_status = MedicalRecordStatus.PENDING.value
        cp.save()
        return cp

    @classmethod
    def remove_patient(cls, campaign_id: str, patient_id: str) -> None:
        CampaignPatient.delete().where(
            (CampaignPatient.campaign == campaign_id) & (CampaignPatient.patient == patient_id)
        ).execute()

    @classmethod
    def set_presence(cls, campaign_id: str, patient_id: str, status: str) -> CampaignPatient:
        cp = CampaignPatient.get(
            (CampaignPatient.campaign == campaign_id) & (CampaignPatient.patient == patient_id)
        )
        cp.presence_status = status
        cp.save()
        return cp

    # ── Workflow transitions ───────────────────────────────────────────────

    @classmethod
    def submit(cls, campaign_id: str) -> Campaign:
        """DRAFT → AWAITING_OP_VALIDATION. Opérateur submits campaign for admin review."""
        campaign = Campaign.get_by_id_and_check(campaign_id)
        if campaign.status != CampaignStatus.DRAFT:
            raise CampaignValidationError("Seul un brouillon peut être soumis.")
        if not campaign.name:
            raise CampaignValidationError("Le nom de la campagne est obligatoire.")
        if cls.patient_count(campaign_id) == 0:
            raise CampaignValidationError("La campagne doit contenir au moins un patient.")
        campaign.status = CampaignStatus.AWAITING_OP_VALIDATION
        campaign.save()
        return campaign

    @classmethod
    def validate_ops(cls, campaign_id: str) -> Campaign:
        """AWAITING_OP_VALIDATION → OPERATIONALLY_VALIDATED (Admin PSC, US-051)."""
        campaign = Campaign.get_by_id_and_check(campaign_id)
        if campaign.status != CampaignStatus.AWAITING_OP_VALIDATION:
            raise CampaignValidationError("La campagne n'est pas en attente de validation opérationnelle.")
        errors = []
        if not campaign.start_date:
            errors.append("Date de début manquante.")
        if not campaign.end_date:
            errors.append("Date de fin manquante.")
        if not campaign.location:
            errors.append("Lieu manquant.")
        if cls.patient_count(campaign_id) == 0:
            errors.append("Aucun patient inscrit.")
        if not campaign.psc_doctor_id:
            errors.append("Médecin PSC non défini.")
        if not campaign.enterprise_doctor_id:
            errors.append("Médecin entreprise non défini.")
        if errors:
            raise CampaignValidationError(" | ".join(errors))
        if campaign.requires_medical_review:
            campaign.status = CampaignStatus.AWAITING_MEDICAL_VALIDATION
        else:
            campaign.status = CampaignStatus.OPERATIONALLY_VALIDATED
        campaign.save()
        return campaign

    @classmethod
    def validate_medical(cls, campaign_id: str) -> Campaign:
        """AWAITING_MEDICAL_VALIDATION → MEDICALLY_VALIDATED (Médecin PSC, US-052)."""
        campaign = Campaign.get_by_id_and_check(campaign_id)
        if campaign.status != CampaignStatus.AWAITING_MEDICAL_VALIDATION:
            raise CampaignValidationError("La campagne n'est pas en attente de validation médicale.")
        campaign.status = CampaignStatus.MEDICALLY_VALIDATED
        campaign.save()
        return campaign

    @classmethod
    def refuse_medical(cls, campaign_id: str, reason: str) -> Campaign:
        """Medical refusal — goes back to DRAFT with a note."""
        if not reason or not reason.strip():
            raise CampaignValidationError("Un motif de refus est obligatoire.")
        campaign = Campaign.get_by_id_and_check(campaign_id)
        if campaign.status != CampaignStatus.AWAITING_MEDICAL_VALIDATION:
            raise CampaignValidationError("La campagne n'est pas en attente de validation médicale.")
        campaign.notes = f"[REFUS MÉDICAL] {reason}\n" + (campaign.notes or "")
        campaign.status = CampaignStatus.DRAFT
        campaign.save()
        return campaign

    @classmethod
    def ready_for_convocations(cls, campaign_id: str) -> Campaign:
        """OPERATIONALLY_VALIDATED or MEDICALLY_VALIDATED → READY_FOR_CONVOCATION."""
        campaign = Campaign.get_by_id_and_check(campaign_id)
        if campaign.status not in (
            CampaignStatus.OPERATIONALLY_VALIDATED,
            CampaignStatus.MEDICALLY_VALIDATED,
        ):
            raise CampaignValidationError("La campagne n'est pas dans un statut compatible.")
        campaign.status = CampaignStatus.READY_FOR_CONVOCATION
        campaign.save()
        return campaign

    @classmethod
    def send_convocations(cls, campaign_id: str) -> Campaign:
        """READY_FOR_CONVOCATION → CONVOCATIONS_SENT."""
        campaign = Campaign.get_by_id_and_check(campaign_id)
        if campaign.status != CampaignStatus.READY_FOR_CONVOCATION:
            raise CampaignValidationError("Les convocations ne peuvent être envoyées que depuis le statut 'Prête pour convocation'.")
        campaign.status = CampaignStatus.CONVOCATIONS_SENT
        campaign.save()
        return campaign

    @classmethod
    def start_terrain(cls, campaign_id: str) -> Campaign:
        """CONVOCATIONS_SENT → TERRAIN_EN_COURS."""
        campaign = Campaign.get_by_id_and_check(campaign_id)
        if campaign.status != CampaignStatus.CONVOCATIONS_SENT:
            raise CampaignValidationError("La phase terrain ne peut commencer que depuis 'Convocations envoyées'.")
        campaign.status = CampaignStatus.TERRAIN_EN_COURS
        campaign.save()
        return campaign

    @classmethod
    def close_terrain(cls, campaign_id: str) -> Campaign:
        """TERRAIN_EN_COURS → TERRAIN_CLOTURE (US-100).

        All enrolled patients must have a non-PENDING presence status.
        """
        campaign = Campaign.get_by_id_and_check(campaign_id)
        if campaign.status != CampaignStatus.TERRAIN_EN_COURS:
            raise CampaignValidationError("La clôture terrain n'est possible qu'en phase Terrain en cours.")
        pending = CampaignPatient.select().where(
            (CampaignPatient.campaign == campaign_id)
            & (CampaignPatient.presence_status == PresenceStatus.PENDING.value)
        ).count()
        if pending > 0:
            raise CampaignValidationError(
                f"{pending} patient(s) sans statut de présence. Veuillez les renseigner avant de clôturer."
            )
        campaign.status = CampaignStatus.TERRAIN_CLOTURE
        campaign.save()
        return campaign

    @classmethod
    def start_lab(cls, campaign_id: str) -> Campaign:
        """TERRAIN_CLOTURE → LABO_EN_COURS."""
        campaign = Campaign.get_by_id_and_check(campaign_id)
        if campaign.status != CampaignStatus.TERRAIN_CLOTURE:
            raise CampaignValidationError("Le labo ne peut commencer qu'après clôture terrain.")
        campaign.status = CampaignStatus.LABO_EN_COURS
        campaign.save()
        return campaign

    @classmethod
    def mark_lab_entered(cls, campaign_id: str, patient_id: str) -> CampaignPatient:
        """Transition patient medical status to LAB_ENTERED (results submitted to doctor)."""
        from gws_care.campaign.campaign_patient import MedicalRecordStatus
        cp = CampaignPatient.get(
            (CampaignPatient.campaign == campaign_id) & (CampaignPatient.patient == patient_id)
        )
        cp.medical_status = MedicalRecordStatus.LAB_ENTERED.value
        cp.save()
        return cp

    @classmethod
    def validate_lab_patient(cls, campaign_id: str, patient_id: str) -> CampaignPatient:
        """Mark a patient's lab results as validated (US-112)."""
        cp = CampaignPatient.get(
            (CampaignPatient.campaign == campaign_id) & (CampaignPatient.patient == patient_id)
        )
        if cp.presence_status == PresenceStatus.ABSENT.value:
            raise CampaignValidationError("Le patient est absent — pas de résultats à valider.")
        cp.medical_status = MedicalRecordStatus.LAB_VALIDATED.value
        cp.save()
        return cp

    @classmethod
    def validate_lab_campaign(cls, campaign_id: str) -> Campaign:
        """LABO_EN_COURS → LABO_VALIDE once all present patients are lab-validated (US-113)."""
        campaign = Campaign.get_by_id_and_check(campaign_id)
        if campaign.status != CampaignStatus.LABO_EN_COURS:
            raise CampaignValidationError("La validation labo campagne n'est possible qu'en phase Labo en cours.")
        present_not_validated = CampaignPatient.select().where(
            (CampaignPatient.campaign == campaign_id)
            & (CampaignPatient.presence_status == PresenceStatus.PRESENT.value)
            & (CampaignPatient.medical_status != MedicalRecordStatus.LAB_VALIDATED.value)
        ).count()
        if present_not_validated > 0:
            raise CampaignValidationError(
                f"{present_not_validated} patient(s) présent(s) dont les résultats ne sont pas encore validés au labo."
            )
        campaign.status = CampaignStatus.LABO_VALIDE
        campaign.save()
        return campaign

    @classmethod
    def add_psc_interpretation(cls, campaign_id: str, patient_id: str, notes: str) -> CampaignPatient:
        """Save PSC doctor interpretation for a patient (US-121)."""
        cp = CampaignPatient.get(
            (CampaignPatient.campaign == campaign_id) & (CampaignPatient.patient == patient_id)
        )
        cp.psc_notes = notes
        cp.medical_status = MedicalRecordStatus.PSC_INTERPRETED.value
        cp.save()
        return cp

    @classmethod
    def validate_psc_patient(cls, campaign_id: str, patient_id: str) -> CampaignPatient:
        """Lock PSC interpretation for a patient (US-122)."""
        cp = CampaignPatient.get(
            (CampaignPatient.campaign == campaign_id) & (CampaignPatient.patient == patient_id)
        )
        if cp.medical_status != MedicalRecordStatus.PSC_INTERPRETED.value:
            raise CampaignValidationError("Le dossier doit être interprété par le médecin PSC avant validation.")
        cp.medical_status = MedicalRecordStatus.PSC_VALIDATED.value
        cp.psc_validated_at = datetime.now()
        cp.save()
        return cp

    @classmethod
    def validate_psc_campaign(cls, campaign_id: str) -> Campaign:
        """LABO_VALIDE → VALIDE_MEDECIN_PSC once all present dossiers are PSC-validated (US-123)."""
        campaign = Campaign.get_by_id_and_check(campaign_id)
        if campaign.status != CampaignStatus.LABO_VALIDE:
            raise CampaignValidationError("La validation PSC campagne n'est possible qu'après 'Labo validé'.")
        not_validated = CampaignPatient.select().where(
            (CampaignPatient.campaign == campaign_id)
            & (CampaignPatient.presence_status == PresenceStatus.PRESENT.value)
            & (CampaignPatient.medical_status != MedicalRecordStatus.PSC_VALIDATED.value)
        ).count()
        if not_validated > 0:
            raise CampaignValidationError(
                f"{not_validated} dossier(s) non encore validé(s) par le médecin PSC."
            )
        campaign.status = CampaignStatus.VALIDE_MEDECIN_PSC
        campaign.save()
        return campaign

    @classmethod
    def add_enterprise_interpretation(
        cls, campaign_id: str, patient_id: str, notes: str, patient_message: str
    ) -> CampaignPatient:
        """Enterprise doctor adds their interpretation (US-131)."""
        if not patient_message or not patient_message.strip():
            raise CampaignValidationError("Le message destiné au patient est obligatoire pour la publication.")
        cp = CampaignPatient.get(
            (CampaignPatient.campaign == campaign_id) & (CampaignPatient.patient == patient_id)
        )
        cp.enterprise_notes = notes
        cp.patient_message = patient_message
        cp.medical_status = MedicalRecordStatus.ENTERPRISE_INTERPRETED.value
        cp.save()
        return cp

    @classmethod
    def validate_enterprise_patient(cls, campaign_id: str, patient_id: str) -> CampaignPatient:
        """Lock enterprise interpretation for a patient (US-131)."""
        cp = CampaignPatient.get(
            (CampaignPatient.campaign == campaign_id) & (CampaignPatient.patient == patient_id)
        )
        if cp.medical_status != MedicalRecordStatus.ENTERPRISE_INTERPRETED.value:
            raise CampaignValidationError("Le dossier doit être interprété par le médecin entreprise avant validation.")
        cp.medical_status = MedicalRecordStatus.ENTERPRISE_VALIDATED.value
        cp.enterprise_validated_at = datetime.now()
        cp.save()
        return cp

    @classmethod
    def publish_patient_results(cls, campaign_id: str, patient_id: str) -> CampaignPatient:
        """Publish results to patient (US-132)."""
        cp = CampaignPatient.get(
            (CampaignPatient.campaign == campaign_id) & (CampaignPatient.patient == patient_id)
        )
        if not cp.patient_message:
            raise CampaignValidationError("Un message patient est obligatoire avant publication.")
        cp.medical_status = MedicalRecordStatus.PUBLISHED.value
        cp.published_at = datetime.now()
        cp.save()
        return cp

    @classmethod
    def publish_campaign(cls, campaign_id: str) -> Campaign:
        """VALIDE_MEDECIN_PSC → PUBLIE_MEDECIN_ENTREPRISE."""
        campaign = Campaign.get_by_id_and_check(campaign_id)
        if campaign.status != CampaignStatus.VALIDE_MEDECIN_PSC:
            raise CampaignValidationError("La campagne doit être validée PSC avant publication.")
        campaign.status = CampaignStatus.PUBLIE_MEDECIN_ENTREPRISE
        campaign.save()
        return campaign

    @classmethod
    def publish_to_patients(cls, campaign_id: str) -> Campaign:
        """PUBLIE_MEDECIN_ENTREPRISE → PUBLIE_PATIENT."""
        campaign = Campaign.get_by_id_and_check(campaign_id)
        if campaign.status != CampaignStatus.PUBLIE_MEDECIN_ENTREPRISE:
            raise CampaignValidationError("La campagne doit être publiée médecin entreprise avant d'être publiée au patient.")
        campaign.status = CampaignStatus.PUBLIE_PATIENT
        campaign.save()
        return campaign

    @classmethod
    def archive(cls, campaign_id: str) -> Campaign:
        campaign = Campaign.get_by_id_and_check(campaign_id)
        campaign.status = CampaignStatus.ARCHIVED
        campaign.save()
        return campaign

    # Legacy compatibility
    @classmethod
    def advance_status(cls, campaign_id: str) -> Campaign:
        """Move campaign to the next logical status (simple linear advance)."""
        campaign = Campaign.get_by_id_and_check(campaign_id)
        _NEXT = {
            CampaignStatus.DRAFT: CampaignStatus.AWAITING_OP_VALIDATION,
            CampaignStatus.AWAITING_OP_VALIDATION: CampaignStatus.OPERATIONALLY_VALIDATED,
            CampaignStatus.OPERATIONALLY_VALIDATED: CampaignStatus.READY_FOR_CONVOCATION,
            CampaignStatus.READY_FOR_CONVOCATION: CampaignStatus.CONVOCATIONS_SENT,
            CampaignStatus.CONVOCATIONS_SENT: CampaignStatus.TERRAIN_EN_COURS,
        }
        next_status = _NEXT.get(campaign.status)
        if next_status:
            campaign.status = next_status
            campaign.save()
        return campaign
