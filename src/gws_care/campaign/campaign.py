"""Campaign model."""

import secrets
import string

from gws_core import EnumField
from peewee import BooleanField, CharField, DateField, ForeignKeyField, TextField

from gws_care.account.account import Account
from gws_care.campaign.campaign_dto import CampaignDTO
from gws_care.campaign.campaign_status import CampaignStatus
from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser


def _generate_campaign_number() -> str:
    """Generate a unique campaign number like PRG-XXXXXXXX."""
    chars = string.ascii_uppercase + string.digits
    suffix = "".join(secrets.choice(chars) for _ in range(8))
    return f"PRG-{suffix}"


class Campaign(ModelWithUser):
    """An organised medical campaign planned for a billing account.

    A campaign groups multiple visits (one per patient) of the same set
    of exam types, performed during a defined date range.
    """

    campaign_number: str = CharField(max_length=50, unique=True, null=False, index=True, column_name='program_number')
    name: str = CharField(max_length=255, null=False)
    account: Account = ForeignKeyField(Account, null=True, backref="programs", on_delete="SET NULL")
    start_date = DateField(null=False)
    end_date = DateField(null=False)
    status: CampaignStatus = EnumField(choices=CampaignStatus, default=CampaignStatus.DRAFT, null=False)
    notes: str = TextField(null=True)
    is_individual: bool = BooleanField(default=False, null=False)
    archive_reason: str = TextField(null=True)

    def _before_insert(self) -> None:
        super()._before_insert()
        if not self.campaign_number:
            self.campaign_number = _generate_campaign_number()

    @property
    def program_number(self) -> str:
        """Backward-compat alias kept for legacy code still using program_number."""
        return self.campaign_number

    def to_dto(self) -> CampaignDTO:
        return CampaignDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            campaign_number=self.campaign_number,
            name=self.name,
            account_id=str(self.account_id) if self.account_id else None,
            account_name=self.account.name if self.account_id else None,
            start_date=self.start_date,
            end_date=self.end_date,
            status=self.status,
            notes=self.notes,
            is_individual=bool(self.is_individual),
        )

    class Meta:
        table_name = "gws_care_medical_program"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
