from peewee import BooleanField, CharField, TextField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser

from .account_dto import AccountDTO


class Account(ModelWithUser):
    """
    Billing account — a company or individual who pays for health services.
    account_type is either "COMPANY" or "INDIVIDUAL".
    """

    account_type: str = CharField(max_length=20, default="COMPANY", null=False)
    name: str = CharField(max_length=255, null=False, unique=True)
    registration_number: str = CharField(max_length=100, null=True)
    address: str = TextField(null=True)
    postal_code: str = CharField(max_length=20, null=True)
    city: str = CharField(max_length=100, null=True)
    phone: str = CharField(max_length=50, null=True)
    email: str = CharField(max_length=255, null=True)
    contact_name: str = CharField(max_length=255, null=True)
    is_active: bool = BooleanField(default=True, null=False)

    def to_dto(self) -> AccountDTO:
        return AccountDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            account_type=self.account_type,
            name=self.name,
            registration_number=self.registration_number,
            address=self.address,
            postal_code=self.postal_code,
            city=self.city,
            phone=self.phone,
            email=self.email,
            contact_name=self.contact_name,
            is_active=self.is_active,
        )

    class Meta:
        table_name = "gws_care_account"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
