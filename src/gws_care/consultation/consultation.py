"""Consultation model — one medical visit, one clinical context, N exams ordered."""

from datetime import date
from enum import Enum

from peewee import CharField, DateField, FloatField, ForeignKeyField, TextField

from gws_care.account.account import Account
from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.patient.patient import Patient


class EncounterType(str, Enum):
    """How was this consultation initiated?"""
    CAMPAIGN_EXAM = "CAMPAIGN_EXAM"       # Part of a company screening campaign
    CLINIC_VISIT = "CLINIC_VISIT"         # Walk-in or booked private clinic visit
    PREVENTIVE = "PREVENTIVE"             # Scheduled preventive check-up (not linked to campaign)

    def get_label(self) -> str:
        return {
            "CAMPAIGN_EXAM": "Visite de médecine du travail (campagne)",
            "CLINIC_VISIT": "Consultation privée",
            "PREVENTIVE": "Visite préventive",
        }[self.value]


class Consultation(ModelWithUser):
    """One medical consultation visit.

    Holds the clinical context (reason, history, vitals, conclusion) once.
    Multiple Exam records link to this via their consultation_id FK.
    This avoids repeating the same clinical context for each ordered exam.
    """

    patient: Patient = ForeignKeyField(Patient, null=False, backref="consultations", on_delete="CASCADE")
    billing_account: Account = ForeignKeyField(Account, null=True, backref="consultations", on_delete="SET NULL")
    # How was this consultation initiated — determines workflow, billing, and access rights
    encounter_type: str = CharField(
        max_length=30, null=False, default=EncounterType.CLINIC_VISIT.value
    )
    consultation_date: date = DateField(null=False, index=True)
    reason_for_visit: str = TextField(null=True)
    medical_history: str = TextField(null=True)
    weight: float = FloatField(null=True)       # kg
    height: float = FloatField(null=True)       # cm
    bmi: float = FloatField(null=True)
    blood_pressure: str = CharField(max_length=50, null=True)
    heart_rate: float = FloatField(null=True)   # bpm
    temperature: float = FloatField(null=True)  # °C
    conclusion: str = TextField(null=True)

    def get_encounter_type_label(self) -> str:
        try:
            return EncounterType(self.encounter_type).get_label()
        except ValueError:
            return self.encounter_type

    class Meta:
        table_name = "gws_care_consultation"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
