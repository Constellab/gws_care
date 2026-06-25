from peewee import BooleanField, CharField, ForeignKeyField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.user.user import User


class MedicalDoctor(ModelWithUser):
    """Registered medical doctor (médecin traitant) in the system.

    A doctor can exist in the registry without a system account (external /
    referring physician). When the doctor also has a login, ``user`` links their
    ``gws_care_user`` record so the platform can scope their planning view.
    """

    first_name: str = CharField(max_length=150, null=False)
    last_name: str = CharField(max_length=150, null=False)
    specialization: str = CharField(max_length=255, null=True)
    phone: str = CharField(max_length=50, null=True)
    email: str = CharField(max_length=255, null=True)
    rpps_number: str = CharField(max_length=20, null=True)
    address: str = CharField(max_length=500, null=True)
    is_active: bool = BooleanField(default=True, null=False)
    is_archived: bool = BooleanField(default=False, null=False)
    status_reason: str = CharField(max_length=1000, null=True)
    user: User = ForeignKeyField(User, null=True, backref="medical_doctor_profile", on_delete="SET NULL", unique=True)

    def get_full_name(self) -> str:
        return f"Dr. {self.first_name} {self.last_name}"

    class Meta:
        table_name = "gws_care_medical_doctor"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
