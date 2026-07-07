"""ExamParameter — configurable parameter of an ExamTypeRef (US-041)."""

from enum import Enum

from peewee import BooleanField, CharField, DoubleField, ForeignKeyField, IntegerField, TextField

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
    # Computed parameter support
    code: str = CharField(max_length=50, null=True)
    is_computed: bool = BooleanField(default=False, null=False)
    formula: str = TextField(null=True)
    # Gender applicability: 'ALL' | 'M' | 'F'
    target_gender: str = CharField(max_length=5, default="ALL", null=False)
    # Gender-specific reference thresholds (override common when patient gender matches)
    ref_low_m: float = DoubleField(null=True)
    ref_high_m: float = DoubleField(null=True)
    critical_low_m: float = DoubleField(null=True)
    critical_high_m: float = DoubleField(null=True)
    ref_low_f: float = DoubleField(null=True)
    ref_high_f: float = DoubleField(null=True)
    critical_low_f: float = DoubleField(null=True)
    critical_high_f: float = DoubleField(null=True)
    # Custom interpretation labels (operator-defined, optional)
    label_normal: str = TextField(null=True)
    label_low: str = TextField(null=True)
    label_high: str = TextField(null=True)
    label_critical_low: str = TextField(null=True)
    label_critical_high: str = TextField(null=True)

    class Meta:
        table_name = "gws_care_exam_parameter"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
