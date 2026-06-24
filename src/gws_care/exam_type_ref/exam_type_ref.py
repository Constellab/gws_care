"""ExamTypeRef — configurable exam type referential (US-040)."""

from enum import Enum

from peewee import BooleanField, CharField, TextField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser


class ExamCategory(str, Enum):
    BIOLOGY = "BIOLOGY"
    URINE = "URINE"
    CLINICAL = "CLINICAL"
    IMAGING = "IMAGING"
    ECG = "ECG"
    ORL = "ORL"
    OTHER = "OTHER"

    def get_label(self) -> str:
        return {
            "BIOLOGY": "Biologie",
            "URINE": "Urine",
            "CLINICAL": "Clinique",
            "IMAGING": "Imagerie",
            "ECG": "ECG",
            "ORL": "ORL",
            "OTHER": "Autre",
        }[self.value]


class ExamTypeRef(ModelWithUser):
    """Configurable exam type used as referential for campaigns.

    Admins create exam types; campaigns reference them.
    """

    name: str = CharField(max_length=200, null=False)
    category: str = CharField(max_length=50, default=ExamCategory.OTHER.value, null=False)
    department: str = CharField(max_length=100, null=True)
    description: str = TextField(null=True)
    is_active: bool = BooleanField(default=True, null=False)
    deactivation_reason: str = TextField(null=True)
    allows_attachment: bool = BooleanField(default=True, null=False)
    requires_attachment: bool = BooleanField(default=False, null=False)
    required_sample_type: str = CharField(max_length=200, null=True)  # e.g. "Sang total (EDTA)"

    def get_category_label(self) -> str:
        try:
            return ExamCategory(self.category).get_label()
        except ValueError:
            return self.category

    class Meta:
        table_name = "gws_care_exam_type_ref"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
