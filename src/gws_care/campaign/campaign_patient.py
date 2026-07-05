"""Junction table: Campaign ↔ Patient (many-to-many) + medical workflow status."""

from datetime import datetime
from enum import Enum

from gws_core import Model
from peewee import BooleanField, CharField, DateTimeField, ForeignKeyField, TextField

from gws_care.campaign.campaign import Campaign
from gws_care.core.care_db_manager import CareDbManager
from gws_care.patient.patient import Patient


class MedicalRecordStatus(str, Enum):
    """Per-patient medical workflow status within a campaign."""

    PENDING = "PENDING"                                      # Patient enrolled, no results yet
    LAB_ENTERED = "LAB_ENTERED"                              # Operator/lab has saved draft results
    LAB_VALIDATED = "LAB_VALIDATED"                          # Lab results fully validated
    PSC_INTERPRETED = "PSC_INTERPRETED"                      # PSC doctor has written interpretation (draft)
    PSC_VALIDATED = "PSC_VALIDATED"                          # PSC doctor has validated + sent to enterprise
    TRANSMITTED_TREATING_DOCTOR = "TRANSMITTED_TREATING_DOCTOR"  # Results sent to patient's treating doctor
    ENTERPRISE_VALIDATED = "ENTERPRISE_VALIDATED"            # Enterprise doctor has validated aptitude
    PUBLISHED = "PUBLISHED"                                  # Dossier published / closed

    def get_label(self) -> str:
        return {
            "PENDING": "En attente",
            "LAB_ENTERED": "Résultats saisis",
            "LAB_VALIDATED": "Résultats validés labo",
            "PSC_INTERPRETED": "Interprétation PSC en cours",
            "PSC_VALIDATED": "Validé PSC — transmis médecin travail",
            "TRANSMITTED_TREATING_DOCTOR": "Transmis au médecin traitant",
            "ENTERPRISE_VALIDATED": "Validé médecin travail",
            "PUBLISHED": "Dossier terminé",
        }.get(self.value, self.value)

    def get_color(self) -> str:
        return {
            "PENDING": "gray",
            "LAB_ENTERED": "orange",
            "LAB_VALIDATED": "amber",
            "PSC_INTERPRETED": "blue",
            "PSC_VALIDATED": "blue",
            "TRANSMITTED_TREATING_DOCTOR": "teal",
            "ENTERPRISE_VALIDATED": "green",
            "PUBLISHED": "green",
        }.get(self.value, "gray")


class CampaignPatient(Model):
    """Associates a Patient with a Campaign.

    All patients in a campaign must belong to the campaign's billing account.
    Extended with medical workflow tracking fields.
    """

    campaign: Campaign = ForeignKeyField(
        Campaign, null=False, backref="campaign_patients", on_delete="CASCADE", column_name="program_id"
    )
    patient: Patient = ForeignKeyField(
        Patient, null=False, backref="campaign_patients", on_delete="CASCADE"
    )

    # Medical workflow status (see MedicalRecordStatus)
    medical_status: str = CharField(max_length=30, default=MedicalRecordStatus.PENDING.value, null=False)

    # Operator/terrain notes (entered during the on-site phase)
    terrain_notes: str = TextField(null=True, default=None)

    # Doctor notes / interpretations
    psc_notes: str = TextField(null=True, default=None)
    enterprise_notes: str = TextField(null=True, default=None)
    patient_message: str = TextField(null=True, default=None)

    # Audit timestamps
    psc_validated_at: datetime = DateTimeField(null=True, default=None)
    enterprise_validated_at: datetime = DateTimeField(null=True, default=None)
    treating_doctor_transmitted_at: datetime = DateTimeField(null=True, default=None)
    published_at: datetime = DateTimeField(null=True, default=None)

    class Meta:
        table_name = "gws_care_program_patient"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
        indexes = (
            (("campaign", "patient"), True),  # unique: one row per (campaign, patient)
        )
