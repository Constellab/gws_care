"""CampaignPatient — M2M between Campaign and Patient.

Stores per-patient attendance/presence tracking and medical workflow state within a campaign.
"""

from datetime import datetime
from enum import Enum

from peewee import CharField, DateTimeField, ForeignKeyField, TextField

from gws_care.campaign.campaign import Campaign
from gws_care.core.care_db_manager import CareDbManager
from gws_core import Model
from gws_care.patient.patient import Patient


class PresenceStatus(str, Enum):
    PENDING = "PENDING"
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"

    def get_label(self) -> str:
        return {"PENDING": "En attente", "PRESENT": "Présent", "ABSENT": "Absent"}[self.value]

    def get_color(self) -> str:
        return {"PENDING": "gray", "PRESENT": "green", "ABSENT": "red"}[self.value]


class MedicalRecordStatus(str, Enum):
    """Per-patient medical workflow status within a campaign."""

    PENDING = "PENDING"
    LAB_ENTERED = "LAB_ENTERED"
    LAB_VALIDATED = "LAB_VALIDATED"
    PSC_INTERPRETED = "PSC_INTERPRETED"
    PSC_VALIDATED = "PSC_VALIDATED"
    ENTERPRISE_INTERPRETED = "ENTERPRISE_INTERPRETED"
    ENTERPRISE_VALIDATED = "ENTERPRISE_VALIDATED"
    PUBLISHED = "PUBLISHED"

    def get_label(self) -> str:
        _labels = {
            "PENDING": "En attente",
            "LAB_ENTERED": "Résultats saisis",
            "LAB_VALIDATED": "Labo validé",
            "PSC_INTERPRETED": "Interprété PSC",
            "PSC_VALIDATED": "Validé PSC",
            "ENTERPRISE_INTERPRETED": "Interprété entreprise",
            "ENTERPRISE_VALIDATED": "Validé entreprise",
            "PUBLISHED": "Publié patient",
        }
        return _labels.get(self.value, self.value)

    def get_color(self) -> str:
        _colors = {
            "PENDING": "gray",
            "LAB_ENTERED": "yellow",
            "LAB_VALIDATED": "lime",
            "PSC_INTERPRETED": "teal",
            "PSC_VALIDATED": "cyan",
            "ENTERPRISE_INTERPRETED": "indigo",
            "ENTERPRISE_VALIDATED": "violet",
            "PUBLISHED": "green",
        }
        return _colors.get(self.value, "gray")


class CampaignPatient(Model):
    """Link table: one Patient enrolled in one Campaign.

    `presence_status` tracks whether the patient showed up during the terrain phase.
    `medical_status` tracks the per-patient medical workflow (lab → PSC → enterprise → published).
    """

    campaign: Campaign = ForeignKeyField(Campaign, null=False, backref="campaign_patients", on_delete="CASCADE")
    patient: Patient = ForeignKeyField(Patient, null=False, backref="campaign_enrollments", on_delete="CASCADE")
    presence_status: str = CharField(max_length=20, default=PresenceStatus.PENDING.value, null=False)
    appointment_id: str = CharField(max_length=36, null=True)
    # Medical workflow columns (added in migration 0.10.0)
    medical_status: str = CharField(max_length=30, default=MedicalRecordStatus.PENDING.value, null=False)
    psc_notes: str = TextField(null=True)
    enterprise_notes: str = TextField(null=True)
    patient_message: str = TextField(null=True)
    psc_validated_at: datetime = DateTimeField(null=True)
    enterprise_validated_at: datetime = DateTimeField(null=True)
    published_at: datetime = DateTimeField(null=True)

    class Meta:
        table_name = "gws_care_campaign_patient"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
        indexes = (
            (("campaign", "patient"), True),  # unique: one row per campaign+patient
        )
