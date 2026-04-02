from datetime import date

from peewee import CharField, DateField, ForeignKeyField

from gws_care.account.account import Account
from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser

from .patient_dto import PatientDTO


class Patient(ModelWithUser):
    """
    Patient file. The patient_number is auto-generated and unique.
    """

    patient_number: str = CharField(max_length=50, unique=True, null=False, index=True)
    last_name: str = CharField(max_length=150, null=False)
    first_name: str = CharField(max_length=150, null=False)
    birth_name: str = CharField(max_length=150, null=True)
    date_of_birth: date = DateField(null=False)
    # M / F / Other
    gender: str = CharField(max_length=10, null=False)
    photo: str = CharField(max_length=500, null=True)
    address: str = CharField(max_length=500, null=True)
    postal_code: str = CharField(max_length=20, null=True)
    city: str = CharField(max_length=100, null=True)
    phone: str = CharField(max_length=50, null=True)
    email: str = CharField(max_length=255, null=True)
    primary_physician_name: str = CharField(max_length=255, null=True)
    primary_physician_phone: str = CharField(max_length=50, null=True)
    billing_account: Account = ForeignKeyField(Account, null=True, backref="patients", on_delete="SET NULL")

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def get_age(self) -> int:
        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - (
                (today.month, today.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )
        )

    def to_dto(self) -> PatientDTO:
        return PatientDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            patient_number=self.patient_number,
            last_name=self.last_name,
            first_name=self.first_name,
            birth_name=self.birth_name,
            date_of_birth=self.date_of_birth,
            gender=self.gender,
            photo=self.photo,
            address=self.address,
            postal_code=self.postal_code,
            city=self.city,
            phone=self.phone,
            email=self.email,
            primary_physician_name=self.primary_physician_name,
            primary_physician_phone=self.primary_physician_phone,
            account_id=str(self.billing_account_id) if self.billing_account_id else None,
        )

    class Meta:
        table_name = "gws_care_patient"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
