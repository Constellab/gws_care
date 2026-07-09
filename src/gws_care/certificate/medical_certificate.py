"""Medical certificate model, DTO and service."""

from datetime import date

from gws_core import BaseModelDTO, ModelDTO
from peewee import BooleanField, CharField, DateField, ForeignKeyField, TextField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.exam.exam import Exam
from gws_care.patient.patient import Patient
from gws_care.user.user import User
from gws_care.visit.visit import Visit

# ── Certificate types ─────────────────────────────────────────────────────────

CERTIFICATE_TYPES = {
    "APTITUDE": "Certificat d'aptitude",
    "WORK_STOPPAGE": "Arrêt de travail",
    "PRE_EMPLOYMENT": "Visite d'embauche",
    "PERIODIC": "Visite périodique",
    "WORK_ACCIDENT": "Accident du travail / Maladie professionnelle",
    "SIR": "Suivi Individuel Renforcé (SIR)",
    "VACCINATION": "Vaccinal",
}


# ── DTOs ──────────────────────────────────────────────────────────────────────

class MedicalCertificateDTO(ModelDTO):
    patient_id: str
    exam_id: str | None
    issue_date: date
    conclusion: str
    is_fit_for_work: bool
    restrictions: str | None
    issued_by_id: str | None
    # Extended fields (migration 3.0.0)
    certificate_type: str = "APTITUDE"
    start_date: str | None = None
    end_date: str | None = None
    return_date: str | None = None
    exposure_type: str | None = None
    vaccine_name: str | None = None
    vaccine_lot: str | None = None
    next_booster: str | None = None
    accident_date: str | None = None
    body_part: str | None = None
    visit_subtype: str | None = None


class SaveMedicalCertificateDTO(BaseModelDTO):
    patient_id: str
    exam_id: str | None = None
    issue_date: date
    conclusion: str
    fitness_decision: str = "FIT"  # "FIT" | "UNFIT" | "PERMANENTLY_UNFIT"
    restrictions: str | None = None
    # Extended fields (migration 3.0.0)
    certificate_type: str = "APTITUDE"
    start_date: str | None = None
    end_date: str | None = None
    return_date: str | None = None
    exposure_type: str | None = None
    vaccine_name: str | None = None
    vaccine_lot: str | None = None
    next_booster: str | None = None
    accident_date: str | None = None
    body_part: str | None = None
    visit_subtype: str | None = None


# ── Model ─────────────────────────────────────────────────────────────────────

class MedicalCertificate(ModelWithUser):
    """Medical certificate issued for a patient, optionally linked to an exam."""

    patient: Patient = ForeignKeyField(
        Patient, null=False, backref="certificates", on_delete="CASCADE"
    )
    exam: Exam = ForeignKeyField(Exam, null=True, backref="certificates", on_delete="SET NULL")
    # Optional link to a classical visit (null for standalone certificates and exam-visit certificates)
    visit: Visit = ForeignKeyField(Visit, null=True, backref="visit_certificates", on_delete="SET NULL")
    issue_date: date = DateField(null=False)
    conclusion: str = TextField(null=False)
    is_fit_for_work: bool = BooleanField(default=True, null=False)
    fitness_decision: str = CharField(max_length=20, null=True)  # "FIT" | "UNFIT" | "PERMANENTLY_UNFIT"
    restrictions: str = TextField(null=True)
    issued_by: User = ForeignKeyField(User, null=True, backref="+")
    is_archived: bool = BooleanField(default=False, null=False)
    # Extended fields (migration 3.0.0)
    certificate_type: str = CharField(max_length=30, null=False, default="APTITUDE")
    start_date: date = DateField(null=True)
    end_date: date = DateField(null=True)
    return_date: date = DateField(null=True)
    exposure_type: str = CharField(max_length=120, null=True)
    vaccine_name: str = CharField(max_length=120, null=True)
    vaccine_lot: str = CharField(max_length=80, null=True)
    next_booster: date = DateField(null=True)
    accident_date: date = DateField(null=True)
    body_part: str = CharField(max_length=120, null=True)
    visit_subtype: str = CharField(max_length=80, null=True)

    @property
    def certificate_type_label(self) -> str:
        return CERTIFICATE_TYPES.get(self.certificate_type or "APTITUDE", self.certificate_type)

    @property
    def effective_fitness(self) -> str:
        """Three-way fitness decision, backward-compatible with old bool field."""
        if self.fitness_decision:
            return self.fitness_decision
        return "FIT" if self.is_fit_for_work else "UNFIT"

    def to_dto(self) -> "MedicalCertificateDTO":
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
            certificate_type=self.certificate_type or "APTITUDE",
            start_date=self.start_date.isoformat() if self.start_date else None,
            end_date=self.end_date.isoformat() if self.end_date else None,
            return_date=self.return_date.isoformat() if self.return_date else None,
            exposure_type=self.exposure_type,
            vaccine_name=self.vaccine_name,
            vaccine_lot=self.vaccine_lot,
            next_booster=self.next_booster.isoformat() if self.next_booster else None,
            accident_date=self.accident_date.isoformat() if self.accident_date else None,
            body_part=self.body_part,
            visit_subtype=self.visit_subtype,
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
    def list_for_patient(cls, patient_id: str, include_archived: bool = False) -> list["MedicalCertificate"]:
        q = MedicalCertificate.select().where(MedicalCertificate.patient == patient_id)
        if not include_archived:
            q = q.where((MedicalCertificate.is_archived == False) | (MedicalCertificate.is_archived.is_null(True)))
        return list(q.order_by(MedicalCertificate.issue_date.desc()))

    @classmethod
    def get(cls, certificate_id: str) -> "MedicalCertificate":
        from gws_core import NotFoundException
        c = MedicalCertificate.get_or_none(MedicalCertificate.id == certificate_id)
        if c is None:
            raise NotFoundException(f"Certificate '{certificate_id}' not found")
        return c

    @classmethod
    def create_certificate(
        cls, dto: "SaveMedicalCertificateDTO", issued_by: "User"
    ) -> "MedicalCertificate":
        def _parse_date(s):
            if not s:
                return None
            try:
                return date.fromisoformat(s)
            except Exception:
                return None

        cert = MedicalCertificate()
        cert.patient_id = dto.patient_id
        cert.exam_id = dto.exam_id
        cert.issue_date = dto.issue_date
        cert.conclusion = dto.conclusion
        cert.fitness_decision = dto.fitness_decision
        cert.is_fit_for_work = dto.fitness_decision == "FIT"
        cert.restrictions = dto.restrictions
        cert.issued_by = issued_by
        cert.certificate_type = dto.certificate_type or "APTITUDE"
        cert.start_date = _parse_date(dto.start_date)
        cert.end_date = _parse_date(dto.end_date)
        cert.return_date = _parse_date(dto.return_date)
        cert.exposure_type = dto.exposure_type
        cert.vaccine_name = dto.vaccine_name
        cert.vaccine_lot = dto.vaccine_lot
        cert.next_booster = _parse_date(dto.next_booster)
        cert.accident_date = _parse_date(dto.accident_date)
        cert.body_part = dto.body_part
        cert.visit_subtype = dto.visit_subtype
        cert.save()

        # Phase 5 — notify the patient that their certificate is available
        try:
            from gws_care.notification.notification_service import NotificationService
            from gws_care.patient.patient import Patient as _Patient
            patient = _Patient.get_by_id(dto.patient_id)
            NotificationService.notify_certificate_available(cert, patient, sent_by=issued_by)
        except Exception:
            pass  # Notification failure must never block the workflow

        return cert

    @classmethod
    def archive(cls, certificate_id: str) -> None:
        c = cls.get(certificate_id)
        c.is_archived = True
        c.save()

    @classmethod
    def unarchive(cls, certificate_id: str) -> None:
        c = cls.get(certificate_id)
        c.is_archived = False
        c.save()

    @classmethod
    def delete(cls, certificate_id: str) -> None:
        c = cls.get(certificate_id)
        c.delete_instance()
