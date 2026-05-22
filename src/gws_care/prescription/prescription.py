"""Prescription model, DTOs and service."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from gws_core import BaseModelDTO, ModelDTO
from peewee import BooleanField, DateField, ForeignKeyField, TextField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.patient.patient import Patient
from gws_care.user.user import User
from gws_care.visit.visit import Visit

# ── DTOs ──────────────────────────────────────────────────────────────────────

class DrugLineDTO(BaseModelDTO):
    """One drug line in a prescription."""

    name: str = ""
    dosage: str = ""
    frequency: str = ""
    duration: str = ""


class SavePrescriptionDTO(BaseModelDTO):
    patient_id: str
    prescription_date: str  # ISO date string "YYYY-MM-DD"
    drugs: list[DrugLineDTO] = []
    instructions: str = ""
    diagnosis: str = ""


class PrescriptionRowDTO(BaseModelDTO):
    """Lightweight DTO for the prescriptions list in the patient detail page."""

    id: str
    prescription_date: str
    drug_count: int
    diagnosis: str
    prescribed_by_name: str


class PrescriptionDetailDTO(BaseModelDTO):
    """Full DTO used when generating the PDF."""

    id: str
    prescription_date: str
    drugs: list[DrugLineDTO]
    instructions: str
    diagnosis: str
    prescribed_by_name: str
    patient_name: str
    patient_number: str
    patient_date_of_birth: str


# ── Model ──────────────────────────────────────────────────────────────────────

class Prescription(ModelWithUser):
    """Medical prescription issued for a patient."""

    patient: Patient = ForeignKeyField(
        Patient, null=False, backref="prescriptions", on_delete="CASCADE"
    )
    prescribed_by: User = ForeignKeyField(
        User, null=True, backref="+", on_delete="SET NULL"
    )
    prescription_date: date = DateField(null=False)
    # drugs stored as JSON text: list of {name, dosage, frequency, duration}
    drugs_json: str = TextField(null=False, default="[]")
    instructions: str = TextField(null=True)
    diagnosis: str = TextField(null=True)
    is_archived: bool = BooleanField(default=False, null=False)
    # Optional link to a classical visit (null for standalone prescriptions)
    visit: Visit = ForeignKeyField(Visit, null=True, backref="prescriptions", on_delete="SET NULL")

    @property
    def drugs(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.drugs_json) if self.drugs_json else []
        except Exception:
            return []

    @drugs.setter
    def drugs(self, value: list[dict[str, Any]]) -> None:
        self.drugs_json = json.dumps(value)

    def to_row_dto(self) -> PrescriptionRowDTO:
        prescribed_by_name = "—"
        if self.prescribed_by_id:
            try:
                u: User = User.get_by_id(str(self.prescribed_by_id))
                prescribed_by_name = f"{u.first_name} {u.last_name}".strip() or "—"
            except Exception:
                pass
        return PrescriptionRowDTO(
            id=str(self.id),
            prescription_date=self.prescription_date.isoformat(),
            drug_count=len(self.drugs),
            diagnosis=self.diagnosis or "",
            prescribed_by_name=prescribed_by_name,
        )

    def to_detail_dto(self) -> PrescriptionDetailDTO:
        prescribed_by_name = "—"
        if self.prescribed_by_id:
            try:
                u: User = User.get_by_id(str(self.prescribed_by_id))
                prescribed_by_name = f"Dr. {u.first_name} {u.last_name}".strip()
            except Exception:
                pass
        p: Patient = Patient.get_by_id(str(self.patient_id))
        return PrescriptionDetailDTO(
            id=str(self.id),
            prescription_date=self.prescription_date.isoformat(),
            drugs=[DrugLineDTO(**d) for d in self.drugs],
            instructions=self.instructions or "",
            diagnosis=self.diagnosis or "",
            prescribed_by_name=prescribed_by_name,
            patient_name=f"{p.first_name} {p.last_name}".strip(),
            patient_number=p.patient_number,
            patient_date_of_birth=p.date_of_birth.isoformat() if p.date_of_birth else "",
        )

    class Meta:
        table_name = "gws_care_prescription"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()


# ── Service ───────────────────────────────────────────────────────────────────

class PrescriptionService:
    """CRUD service for Prescription."""

    @classmethod
    def list_for_patient(cls, patient_id: str, include_archived: bool = False) -> list[Prescription]:
        q = Prescription.select().where(Prescription.patient == patient_id)
        if not include_archived:
            q = q.where((Prescription.is_archived == False) | (Prescription.is_archived.is_null(True)))
        return list(q.order_by(Prescription.prescription_date.desc()))

    @classmethod
    def get(cls, prescription_id: str) -> Prescription:
        from gws_core import NotFoundException
        p = Prescription.get_or_none(Prescription.id == prescription_id)
        if p is None:
            raise NotFoundException(f"Prescription '{prescription_id}' not found")
        return p

    @classmethod
    def create(cls, dto: SavePrescriptionDTO, prescribed_by: User) -> Prescription:
        from gws_core import BadRequestException
        patient = Patient.get_or_none(Patient.id == dto.patient_id)
        if patient is None:
            raise BadRequestException(f"Patient '{dto.patient_id}' not found")

        p = Prescription()
        p.patient = patient
        p.prescribed_by = prescribed_by
        p.prescription_date = date.fromisoformat(dto.prescription_date)
        p.drugs = [d.dict() for d in dto.drugs]
        p.instructions = dto.instructions or None
        p.diagnosis = dto.diagnosis or None
        p.save()
        return p

    @classmethod
    def archive(cls, prescription_id: str) -> None:
        p = cls.get(prescription_id)
        p.is_archived = True
        p.save()

    @classmethod
    def unarchive(cls, prescription_id: str) -> None:
        p = cls.get(prescription_id)
        p.is_archived = False
        p.save()

    @classmethod
    def delete(cls, prescription_id: str) -> None:
        p = cls.get(prescription_id)
        p.delete_instance()
