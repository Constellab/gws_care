"""CampaignVisit model."""

import secrets
import string
from datetime import datetime

from gws_core import EnumField
from peewee import CharField, DateTimeField, ForeignKeyField, TextField

from gws_care.account.account import Account
from gws_care.campaign.campaign import Campaign
from gws_care.campaign_visit.campaign_visit_dto import CampaignVisitDTO
from gws_care.campaign_visit.campaign_visit_status import CampaignVisitStatus
from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.patient.patient import Patient


def _generate_visit_number() -> str:
    chars = string.ascii_uppercase + string.digits
    suffix = "".join(secrets.choice(chars) for _ in range(8))
    return f"VIS-{suffix}"


class CampaignVisit(ModelWithUser):
    """One medical visit — all exams for a single patient in a single campaign.

    Progresses through a sequential validation chain:
    PENDING → VISIT_DONE → LAB_DONE
           → DOCTOR_CLINIC_VALIDATED → DOCTOR_COMPANY_VALIDATED

    Validation steps (who validated and when) are tracked in
    CampaignVisitValidationWorkflow — one row per step per visit.
    """

    visit_number: str = CharField(max_length=50, unique=True, null=False, index=True)
    program: Campaign = ForeignKeyField(Campaign, null=True, backref="visits", on_delete="CASCADE")
    patient: Patient = ForeignKeyField(Patient, null=False, backref="visits", on_delete="CASCADE")
    billing_account: Account = ForeignKeyField(Account, null=True, backref="visits", on_delete="SET NULL")
    scheduled_at: datetime = DateTimeField(null=True)
    status: CampaignVisitStatus = EnumField(choices=CampaignVisitStatus, default=CampaignVisitStatus.PENDING, null=False)

    # Interpretation text — kept on CampaignVisit for fast access; authorship is in CampaignVisitValidationWorkflow
    doctor_clinic_interpretation: str = TextField(null=True)
    doctor_company_interpretation: str = TextField(null=True)
    doctor_company_message: str = TextField(null=True)

    def _before_insert(self) -> None:
        super()._before_insert()
        if not self.visit_number:
            self.visit_number = _generate_visit_number()

    @property
    def campaign_id(self):
        """Alias for program_id (DB column kept for backward compatibility)."""
        return self.program_id

    def to_dto(self) -> CampaignVisitDTO:
        patient = self.patient
        account = self.billing_account if self.billing_account_id else None
        return CampaignVisitDTO(
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
