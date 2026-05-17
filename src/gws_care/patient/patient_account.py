from peewee import ForeignKeyField

from gws_care.account.account import Account
from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser

from .patient import Patient


class PatientAccount(ModelWithUser):
    """
    Join table: a patient can belong to multiple billing accounts (many-to-many).
    """

    patient = ForeignKeyField(Patient, backref="account_links", on_delete="CASCADE")
    account = ForeignKeyField(Account, backref="patient_links", on_delete="CASCADE")

    class Meta:
        table_name = "gws_care_patient_account"
        database = CareDbManager.get_instance().db
        indexes = ((("patient", "account"), True),)
        is_table = True
        db_manager = CareDbManager.get_instance()
