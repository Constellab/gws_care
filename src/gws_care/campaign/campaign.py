"""Campaign model — a medical screening campaign organised by PSC for a company."""

from datetime import date

from gws_core import EnumField
from peewee import BooleanField, CharField, DateField, ForeignKeyField, TextField

from gws_care.account.account import Account
from gws_care.campaign.campaign_status import CampaignStatus
from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.user.user import User

from .campaign_dto import CampaignDTO


class Campaign(ModelWithUser):
    """One medical screening campaign organised by PSC for a billing account.

    Lifecycle follows CampaignStatus (15 states, from DRAFT to ARCHIVED).
    """

    account: Account = ForeignKeyField(Account, null=False, backref="campaigns", on_delete="CASCADE")
    name: str = CharField(max_length=255, null=False)
    status: CampaignStatus = EnumField(
        choices=CampaignStatus, default=CampaignStatus.DRAFT, null=False
    )
    start_date: date = DateField(null=True)
    end_date: date = DateField(null=True)
    location: str = CharField(max_length=500, null=True)
    # PSC supervising doctor
    psc_doctor: User = ForeignKeyField(User, null=True, backref="+", on_delete="SET NULL")
    # Company-side doctor
    enterprise_doctor: User = ForeignKeyField(User, null=True, backref="+", on_delete="SET NULL")
    # If True, requires medical review before convocations
    requires_medical_review: bool = BooleanField(default=False, null=False)
    notes: str = TextField(null=True)

    def to_dto(self, patient_count: int = 0) -> CampaignDTO:
        psc_doc = None
        if self.psc_doctor_id:
            try:
                psc_doc = f"{self.psc_doctor.first_name} {self.psc_doctor.last_name}"
            except Exception:
                psc_doc = None
        ent_doc = None
        if self.enterprise_doctor_id:
            try:
                ent_doc = f"{self.enterprise_doctor.first_name} {self.enterprise_doctor.last_name}"
            except Exception:
                ent_doc = None
        return CampaignDTO(
            id=str(self.id),
            name=self.name,
            account_id=str(self.account_id),
            account_name=self.account.name if self.account_id else "",
            status=self.status.value,
            status_label=self.status.get_label(),
            status_color=self.status.get_color(),
            start_date=self.start_date,
            end_date=self.end_date,
            location=self.location,
            psc_doctor_name=psc_doc,
            enterprise_doctor_name=ent_doc,
            requires_medical_review=self.requires_medical_review,
            patient_count=patient_count,
            notes=self.notes,
        )

    class Meta:
        table_name = "gws_care_campaign"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
