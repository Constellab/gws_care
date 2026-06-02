"""PatientConsent — GDPR and medical consent tracking.

Records every consent given or revoked by a patient (or their legal guardian).
Required for RGPD compliance and medical ethics in French law.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from peewee import BooleanField, CharField, DateTimeField, ForeignKeyField, TextField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.patient.patient import Patient
from gws_care.user.user import User
from gws_core import Model


class ConsentType(str, Enum):
    DATA_PROCESSING = "DATA_PROCESSING"     # RGPD Art. 6 — processing health data
    MEDICAL_SHARING = "MEDICAL_SHARING"     # Share results between doctors
    PORTAL_ACCESS = "PORTAL_ACCESS"         # Patient can access their own portal
    RESEARCH = "RESEARCH"                   # Anonymous use in medical research
    TELECONSULTATION = "TELECONSULTATION"   # Video-based consultations

    def get_label(self) -> str:
        return {
            "DATA_PROCESSING": "Traitement des données de santé (RGPD)",
            "MEDICAL_SHARING": "Partage des résultats entre praticiens",
            "PORTAL_ACCESS": "Accès à l'espace patient en ligne",
            "RESEARCH": "Utilisation anonymisée à des fins de recherche",
            "TELECONSULTATION": "Consultation par vidéo",
        }[self.value]


class PatientConsent(Model):
    """One consent record for one patient and one consent type.

    is_given=True: consent is active.
    is_given=False: consent was revoked (row is kept for audit trail).
    """

    patient: Patient = ForeignKeyField(
        Patient, null=False, backref="consents", on_delete="CASCADE", index=True
    )
    consent_type: str = CharField(max_length=30, null=False)
    is_given: bool = BooleanField(null=False, default=True)
    given_at: datetime = DateTimeField(null=True)
    revoked_at: datetime = DateTimeField(null=True)
    # The user who recorded or witnessed the consent (doctor / secretary)
    recorded_by: User = ForeignKeyField(User, null=True, backref="+", on_delete="SET NULL")
    # Free text: "signed paper form ref. 2024-001", "verbal, witnessed", etc.
    notes: str | None = TextField(null=True)

    class Meta:
        table_name = "gws_care_patient_consent"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()


class PatientConsentService:
    """Record, revoke, or check patient consents."""

    @classmethod
    def record_consent(
        cls,
        patient_id: str,
        consent_type: ConsentType,
        recorded_by_id: str,
        notes: str | None = None,
    ) -> PatientConsent:
        """Give or re-activate a consent."""
        now = datetime.now()
        # Deactivate any previous active consent of this type
        (
            PatientConsent.update(is_given=False, revoked_at=now)
            .where(
                (PatientConsent.patient == patient_id)
                & (PatientConsent.consent_type == consent_type.value)
                & (PatientConsent.is_given == True)  # noqa: E712
            )
            .execute()
        )
        return PatientConsent.create(
            patient_id=patient_id,
            consent_type=consent_type.value,
            is_given=True,
            given_at=now,
            revoked_at=None,
            recorded_by_id=recorded_by_id,
            notes=notes,
        )

    @classmethod
    def revoke_consent(
        cls,
        patient_id: str,
        consent_type: ConsentType,
        recorded_by_id: str,
        notes: str | None = None,
    ) -> None:
        now = datetime.now()
        (
            PatientConsent.update(is_given=False, revoked_at=now, notes=notes)
            .where(
                (PatientConsent.patient == patient_id)
                & (PatientConsent.consent_type == consent_type.value)
                & (PatientConsent.is_given == True)  # noqa: E712
            )
            .execute()
        )

    @classmethod
    def has_active_consent(cls, patient_id: str, consent_type: ConsentType) -> bool:
        return (
            PatientConsent.select()
            .where(
                (PatientConsent.patient == patient_id)
                & (PatientConsent.consent_type == consent_type.value)
                & (PatientConsent.is_given == True)  # noqa: E712
            )
            .exists()
        )

    @classmethod
    def list_for_patient(cls, patient_id: str) -> list[PatientConsent]:
        return list(
            PatientConsent.select()
            .where(PatientConsent.patient == patient_id)
            .order_by(PatientConsent.given_at.desc())
        )
