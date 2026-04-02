"""Medical certificate model, DTO and service."""

from datetime import date

from gws_core import BaseModelDTO, ModelDTO
from peewee import BooleanField, DateField, ForeignKeyField, TextField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.exam.exam import Exam
from gws_care.patient.patient import Patient
from gws_care.user.user import User

# ── DTO ───────────────────────────────────────────────────────────────────────

class MedicalCertificateDTO(ModelDTO):
    patient_id: str
    exam_id: str | None
    issue_date: date
    conclusion: str
    is_fit_for_work: bool
    restrictions: str | None
    issued_by_id: str | None


class SaveMedicalCertificateDTO(BaseModelDTO):
    patient_id: str
    exam_id: str | None = None
    issue_date: date
    conclusion: str
    is_fit_for_work: bool = True
    restrictions: str | None = None


# ── Model ─────────────────────────────────────────────────────────────────────

class MedicalCertificate(ModelWithUser):
    """Medical certificate issued for a patient, optionally linked to an exam."""

    patient: Patient = ForeignKeyField(
        Patient, null=False, backref="certificates", on_delete="CASCADE"
    )
    exam: Exam = ForeignKeyField(Exam, null=True, backref="certificates", on_delete="SET NULL")
    issue_date: date = DateField(null=False)
    conclusion: str = TextField(null=False)
    is_fit_for_work: bool = BooleanField(default=True, null=False)
    restrictions: str = TextField(null=True)
    issued_by: User = ForeignKeyField(User, null=True, backref="+")

    def to_dto(self) -> MedicalCertificateDTO:
        return MedicalCertificateDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            patient_id=str(self.patient_id),
            exam_id=str(self.exam_id) if self.exam_id else None,
            issue_date=self.issue_date,
            conclusion=self.conclusion,
            is_fit_for_work=self.is_fit_for_work,
            restrictions=self.restrictions,
            issued_by_id=str(self.issued_by_id) if self.issued_by_id else None,
        )

    class Meta:
        table_name = "gws_care_medical_certificate"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()


# ── Service ───────────────────────────────────────────────────────────────────

class MedicalCertificateService:
    """Service for issuing and listing medical certificates."""

    @classmethod
    def list_for_patient(cls, patient_id: str) -> list[MedicalCertificate]:
        return list(
            MedicalCertificate.select()
            .where(MedicalCertificate.patient == patient_id)
            .order_by(MedicalCertificate.issue_date.desc())
        )

    @classmethod
    def create_certificate(
        cls, dto: SaveMedicalCertificateDTO, issued_by: User
    ) -> MedicalCertificate:
        cert = MedicalCertificate()
        cert.patient_id = dto.patient_id
        cert.exam_id = dto.exam_id
        cert.issue_date = dto.issue_date
        cert.conclusion = dto.conclusion
        cert.is_fit_for_work = dto.is_fit_for_work
        cert.restrictions = dto.restrictions
        cert.issued_by = issued_by
        cert.save()
        return cert
