from peewee import BooleanField, CharField, TextField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser

from .company_dto import CompanyDTO


class Company(ModelWithUser):
    """
    Client company that sends employees for occupational health exams.
    """

    name: str = CharField(max_length=255, null=False)
    registration_number: str = CharField(max_length=100, null=True)
    address: str = TextField(null=True)
    postal_code: str = CharField(max_length=20, null=True)
    city: str = CharField(max_length=100, null=True)
    phone: str = CharField(max_length=50, null=True)
    email: str = CharField(max_length=255, null=True)
    contact_name: str = CharField(max_length=255, null=True)
    is_active: bool = BooleanField(default=True, null=False)

    def to_dto(self) -> CompanyDTO:
        return CompanyDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
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
        table_name = "gws_care_company"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
