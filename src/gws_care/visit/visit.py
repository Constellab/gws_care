"""Visit (Visite Médicale) model."""

import secrets
import string
from datetime import datetime

from gws_core import EnumField
from peewee import CharField, DateTimeField, ForeignKeyField, TextField

from gws_care.account.account import Account
from gws_care.medical_program.medical_program import MedicalProgram
from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.patient.patient import Patient
from gws_care.visit.visit_status import VisitStatus

from .visit_dto import VisitDTO


def _generate_visit_number() -> str:
    chars = string.ascii_uppercase + string.digits
    suffix = "".join(secrets.choice(chars) for _ in range(8))
    return f"VIS-{suffix}"


class Visit(ModelWithUser):
    """One medical visit — all exams for a single patient in a single program.

    Progresses through a sequential validation chain:
    PENDING → TERRAIN_DONE → RESULTS_ENTERED → LAB_VALIDATED
           → DOCTOR_CLINIC_VALIDATED → DOCTOR_COMPANY_VALIDATED

    Validation steps (who validated and when) are tracked in
    VisitValidationWorkflow — one row per step per visit.
    """

    visit_number: str = CharField(max_length=50, unique=True, null=False, index=True)
    program: MedicalProgram = ForeignKeyField(MedicalProgram, null=True, backref="visits", on_delete="CASCADE")
    patient: Patient = ForeignKeyField(Patient, null=False, backref="visits", on_delete="CASCADE")
    billing_account: Account = ForeignKeyField(Account, null=True, backref="visits", on_delete="SET NULL")
    scheduled_at: datetime = DateTimeField(null=True)
    status: VisitStatus = EnumField(choices=VisitStatus, default=VisitStatus.PENDING, null=False)

    # Interpretation text — kept on Visit for fast access; authorship is in VisitValidationWorkflow
    doctor_clinic_interpretation: str = TextField(null=True)
    doctor_company_interpretation: str = TextField(null=True)
    doctor_company_message: str = TextField(null=True)

    def _before_insert(self) -> None:
        super()._before_insert()
        if not self.visit_number:
            self.visit_number = _generate_visit_number()

    def to_dto(self) -> VisitDTO:
        patient = self.patient
        account = self.billing_account if self.billing_account_id else None
        return VisitDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            visit_number=self.visit_number,
            program_id=str(self.program_id) if self.program_id else None,
            patient_id=str(self.patient_id),
            billing_account_id=str(self.billing_account_id) if self.billing_account_id else None,
            account_name=account.name if account else None,
            scheduled_at=self.scheduled_at,
            patient_name=patient.get_full_name() if patient else None,
            status=self.status,
            doctor_clinic_interpretation=self.doctor_clinic_interpretation,
            doctor_company_interpretation=self.doctor_company_interpretation,
            doctor_company_message=self.doctor_company_message,
        )

    class Meta:
        table_name = "gws_care_visit"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()

