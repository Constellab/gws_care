"""ExamParameter — configurable parameter of an ExamTypeRef (US-041)."""

from enum import Enum

from peewee import BooleanField, CharField, DoubleField, ForeignKeyField, IntegerField

from gws_care.core.care_db_manager import CareDbManager
from gws_core import Model
from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef


class ParameterValueType(str, Enum):
    NUMERIC = "NUMERIC"
    TEXT = "TEXT"
    BOOLEAN = "BOOLEAN"  # Positif / Négatif

    def get_label(self) -> str:
        return {
            "NUMERIC": "Numérique",
            "TEXT": "Texte",
            "BOOLEAN": "Positif / Négatif",
        }[self.value]


class ExamParameter(Model):
    """One measurable parameter within an exam type.

    Defines expected value type, units, normal range and critical thresholds.
    """

    exam_type_ref: ExamTypeRef = ForeignKeyField(
        ExamTypeRef, null=False, backref="parameters", on_delete="CASCADE"
    )
    name: str = CharField(max_length=200, null=False)
    value_type: str = CharField(max_length=20, default=ParameterValueType.NUMERIC.value, null=False)
    unit: str = CharField(max_length=50, null=True)
    ref_low: float = DoubleField(null=True)
    ref_high: float = DoubleField(null=True)
    critical_low: float = DoubleField(null=True)
    critical_high: float = DoubleField(null=True)
    is_required: bool = BooleanField(default=False, null=False)
    is_active: bool = BooleanField(default=True, null=False)
    display_order: int = IntegerField(default=0, null=False)

    class Meta:
        table_name = "gws_care_exam_parameter"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
