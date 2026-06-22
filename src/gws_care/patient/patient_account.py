"""PatientAccount — M2M affiliation between a Patient and a billing Account."""

from datetime import date
from enum import Enum

from peewee import CharField, DateField, ForeignKeyField, TextField

from gws_care.account.account import Account
from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser

from .patient import Patient


class PatientAccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    FORMER = "FORMER"
    SUSPENDED = "SUSPENDED"

    def get_label(self) -> str:
        return {"ACTIVE": "Actif", "FORMER": "Ancien", "SUSPENDED": "Suspendu"}[self.value]

    def get_color(self) -> str:
        return {"ACTIVE": "green", "FORMER": "gray", "SUSPENDED": "orange"}[self.value]


class PatientAccount(ModelWithUser):
    """Affiliation of a patient to a billing account.

    A patient may have multiple active affiliations simultaneously.
    """

    patient = ForeignKeyField(Patient, null=False, backref="account_affiliations", on_delete="CASCADE")
    account = ForeignKeyField(Account, null=False, backref="patient_affiliations", on_delete="CASCADE")
    status: str = CharField(max_length=20, default=PatientAccountStatus.ACTIVE.value, null=False)
    start_date: date = DateField(null=True)
    end_date: date = DateField(null=True)
    employee_number: str = CharField(max_length=100, null=True)
    position: str = CharField(max_length=200, null=True)
    site: str = CharField(max_length=200, null=True)
    department: str = CharField(max_length=200, null=True)
    end_reason: str = TextField(null=True)

    class Meta:
        table_name = "gws_care_patient_account"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
