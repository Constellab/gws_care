"""Campaign model — a medical screening campaign organised by PSC for a company."""

from datetime import date

from gws_core import EnumField
from peewee import BooleanField, CharField, DateField, ForeignKeyField, TextField

from gws_care.account.account import Account
from gws_care.campaign.campaign_status import CampaignStatus
from gws_care.company.company import Company
from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.user.user import User

from .campaign_dto import CampaignDTO


class Campaign(ModelWithUser):
    """One medical screening campaign organised by PSC for a company.

    Lifecycle follows CampaignStatus (15 states, from DRAFT to ARCHIVED).
    """

    account: Account = ForeignKeyField(Account, null=True, backref="campaigns", on_delete="SET NULL")
    company: Company = ForeignKeyField(Company, null=True, backref="campaigns", on_delete="SET NULL")
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
            except Exception as exc:
                print(f"[campaign.to_dto] psc_doctor for {self.id}: {exc}")
                psc_doc = None
        ent_doc = None
        if self.enterprise_doctor_id:
            try:
                ent_doc = f"{self.enterprise_doctor.first_name} {self.enterprise_doctor.last_name}"
            except Exception as exc:
                print(f"[campaign.to_dto] enterprise_doctor for {self.id}: {exc}")
                ent_doc = None
        company_name = ""
        if self.company_id:
            try:
                company_name = self.company.name
            except Exception as exc:
                print(f"[campaign.to_dto] company for {self.id}: {exc}")
        elif self.account_id:
            try:
                company_name = self.account.name
            except Exception as exc:
                print(f"[campaign.to_dto] account for {self.id}: {exc}")
        return CampaignDTO(
            id=str(self.id),
            name=self.name,
            account_id=str(self.account_id) if self.account_id else "",
            account_name=company_name,
            company_id=str(self.company_id) if self.company_id else "",
            company_name=company_name,
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
