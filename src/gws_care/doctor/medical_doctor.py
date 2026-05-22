from peewee import BooleanField, CharField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser


class MedicalDoctor(ModelWithUser):
    """Registered medical doctor (médecin traitant) in the system."""

    first_name: str = CharField(max_length=150, null=False)
    last_name: str = CharField(max_length=150, null=False)
    specialization: str = CharField(max_length=255, null=True)
    phone: str = CharField(max_length=50, null=True)
    email: str = CharField(max_length=255, null=True)
    rpps_number: str = CharField(max_length=20, null=True)
    address: str = CharField(max_length=500, null=True)
    is_active: bool = BooleanField(default=True, null=False)

    def get_full_name(self) -> str:
        return f"Dr. {self.first_name} {self.last_name}"

    class Meta:
        table_name = "gws_care_medical_doctor"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
