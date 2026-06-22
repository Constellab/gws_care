"""ExamTypeModel — configurable exam type DB model.

This is the database-backed counterpart to the ExamType enum.
It stores thresholds, units and descriptions per exam type,
and is used by Campaign to declare which exam types are required.
"""

from gws_core import EnumField
from peewee import BooleanField, CharField, FloatField, TextField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.exam.exam_type import ExamType

from .exam_type_dto import ExamTypeModelDTO


class ExamTypeModel(ModelWithUser):
    """A configurable exam type record.

    Each row represents one kind of medical exam (e.g. Biology, ECG).
    Thresholds drive the automatic appreciation engine (Normal / Haut / Bas / Critique).
    Seeded from the ExamType enum during migration.
    """

    code: str = CharField(max_length=50, unique=True, null=False, index=True)
    name: str = CharField(max_length=255, null=False)
    category: ExamType = EnumField(choices=ExamType, null=False)
    description: str = TextField(null=True)
    unit: str = CharField(max_length=50, null=True)
    threshold_low: float = FloatField(null=True)
    threshold_high: float = FloatField(null=True)
    threshold_critical_low: float = FloatField(null=True)
    threshold_critical_high: float = FloatField(null=True)
    is_active: bool = BooleanField(default=True, null=False)

    def to_dto(self) -> ExamTypeModelDTO:
        return ExamTypeModelDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            code=self.code,
            name=self.name,
            category=self.category,
            description=self.description,
            unit=self.unit,
            threshold_low=self.threshold_low,
            threshold_high=self.threshold_high,
            threshold_critical_low=self.threshold_critical_low,
            threshold_critical_high=self.threshold_critical_high,
            is_active=self.is_active,
        )

    class Meta:
        table_name = "gws_care_exam_type"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
