"""Prescription — a medical prescription issued during a consultation.

Covers both drug prescriptions and exam/investigation orders.
"""

from __future__ import annotations

from datetime import date
from enum import Enum

from peewee import BooleanField, CharField, DateField, ForeignKeyField, IntegerField, TextField

from gws_care.consultation.consultation import Consultation
from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.patient.patient import Patient
from gws_care.user.user import User


class PrescriptionType(str, Enum):
    DRUG = "DRUG"                   # Médicament
    LAB_ORDER = "LAB_ORDER"         # Bilan biologique
    IMAGING = "IMAGING"             # Imagerie
    SPECIALIST = "SPECIALIST"       # Consultation spécialisée
    PHYSIOTHERAPY = "PHYSIOTHERAPY" # Kinésithérapie
    OTHER = "OTHER"

    def get_label(self) -> str:
        return {
            "DRUG": "Médicament",
            "LAB_ORDER": "Bilan biologique",
            "IMAGING": "Imagerie",
            "SPECIALIST": "Spécialiste",
            "PHYSIOTHERAPY": "Kinésithérapie",
            "OTHER": "Autre",
        }[self.value]


class Prescription(ModelWithUser):
    """A prescription document issued by a doctor during a consultation.

    Contains one or more PrescriptionLine items.
    """

    patient: Patient = ForeignKeyField(
        Patient, null=False, backref="prescriptions", on_delete="CASCADE", index=True
    )
    consultation: Consultation = ForeignKeyField(
        Consultation, null=True, backref="prescriptions", on_delete="SET NULL"
    )
    prescribing_doctor: User = ForeignKeyField(
        User, null=False, backref="prescriptions", on_delete="RESTRICT"
    )
    prescription_type: str = CharField(
        max_length=20, null=False, default=PrescriptionType.DRUG.value
    )
    issued_at: date = DateField(null=False)
    valid_until: date = DateField(null=True)
    is_renewable: bool = BooleanField(default=False, null=False)
    # Number of times already renewed
    renewal_count: int = IntegerField(default=0, null=False)
    # Free-text instructions printed at the bottom of the prescription
    general_instructions: str | None = TextField(null=True)

    def get_type_label(self) -> str:
        try:
            return PrescriptionType(self.prescription_type).get_label()
        except ValueError:
            return self.prescription_type

    class Meta:
        table_name = "gws_care_prescription"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()


class PrescriptionLine(ModelWithUser):
    """One item on a prescription (one drug, one imaging order, etc.)."""

    prescription: Prescription = ForeignKeyField(
        Prescription, null=False, backref="lines", on_delete="CASCADE", index=True
    )
    # For drugs: the drug name / INN
    item_name: str = CharField(max_length=300, null=False)
    # Dosage: "1 comprimé matin et soir"
    dosage: str = CharField(max_length=300, null=True)
    # Duration: "pendant 7 jours"
    duration: str = CharField(max_length=200, null=True)
    # Quantity: "1 boîte", "2 ampoules"
    quantity: str = CharField(max_length=100, null=True)
    # Specific instructions: "à prendre pendant les repas"
    instructions: str = TextField(null=True)
    display_order: int = IntegerField(default=0, null=False)

    class Meta:
        table_name = "gws_care_prescription_line"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()


class PrescriptionService:
    """Create and manage prescriptions."""

    @classmethod
    def create(
        cls,
        patient_id: str,
        prescribing_doctor_id: str,
        prescription_type: PrescriptionType,
        issued_at: date,
        consultation_id: str | None = None,
        valid_until: date | None = None,
        is_renewable: bool = False,
        general_instructions: str | None = None,
        lines: list[dict] | None = None,
    ) -> Prescription:
        """Create a prescription with its lines in a single call.

        Each line dict: {item_name, dosage?, duration?, quantity?, instructions?}
        """
        prescription = Prescription.create(
            patient_id=patient_id,
            consultation_id=consultation_id,
            prescribing_doctor_id=prescribing_doctor_id,
            prescription_type=prescription_type.value,
            issued_at=issued_at,
            valid_until=valid_until,
            is_renewable=is_renewable,
            general_instructions=general_instructions,
        )
        for i, line in enumerate(lines or []):
            PrescriptionLine.create(
                prescription=prescription,
                item_name=line["item_name"],
                dosage=line.get("dosage"),
                duration=line.get("duration"),
                quantity=line.get("quantity"),
                instructions=line.get("instructions"),
                display_order=i,
            )
        return prescription

    @classmethod
    def list_for_patient(cls, patient_id: str, limit: int = 50) -> list[Prescription]:
        return list(
            Prescription.select()
            .where(Prescription.patient == patient_id)
            .order_by(Prescription.issued_at.desc())
            .limit(limit)
        )

    @classmethod
    def list_for_consultation(cls, consultation_id: str) -> list[Prescription]:
        return list(
            Prescription.select()
            .where(Prescription.consultation == consultation_id)
            .order_by(Prescription.issued_at.desc())
        )
