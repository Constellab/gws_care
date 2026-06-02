"""ExamParameterResult — normalized per-parameter results for an exam.

Replaces/supersedes the flat JSON blobs in Exam.lab_results and ExamResult.result_data.
One row per (exam, parameter) allows:
  - SQL queries on individual biological values
  - Automatic critical-value alerts
  - Cross-patient analytics / epidemiology
  - Proper audit trail per value
"""

from __future__ import annotations

from enum import Enum

from peewee import BooleanField, CharField, DoubleField, ForeignKeyField, TextField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.exam.exam import Exam
from gws_care.exam_type_ref.exam_parameter import ExamParameter
from gws_core import Model


class ResultStatus(str, Enum):
    NORMAL = "NORMAL"
    ABNORMAL_LOW = "LOW"
    ABNORMAL_HIGH = "HIGH"
    CRITICAL_LOW = "CRITICAL_LOW"
    CRITICAL_HIGH = "CRITICAL_HIGH"
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    PENDING = "PENDING"

    def get_label(self) -> str:
        return {
            "NORMAL": "Normal",
            "LOW": "Bas",
            "HIGH": "Élevé",
            "CRITICAL_LOW": "Critique bas",
            "CRITICAL_HIGH": "Critique élevé",
            "POSITIVE": "Positif",
            "NEGATIVE": "Négatif",
            "PENDING": "En attente",
        }[self.value]

    def get_color(self) -> str:
        return {
            "NORMAL": "green",
            "LOW": "orange",
            "HIGH": "orange",
            "CRITICAL_LOW": "red",
            "CRITICAL_HIGH": "red",
            "POSITIVE": "red",
            "NEGATIVE": "green",
            "PENDING": "gray",
        }[self.value]

    def is_alert(self) -> bool:
        return self in {ResultStatus.CRITICAL_LOW, ResultStatus.CRITICAL_HIGH, ResultStatus.POSITIVE}


class ExamParameterResult(Model):
    """One measured value for a specific parameter within an exam session.

    Exactly one of value_numeric / value_text / value_boolean is filled,
    matching the parameter's value_type. The status is computed on save
    by ExamParameterResultService against the parameter's reference ranges.
    """

    exam: Exam = ForeignKeyField(
        Exam, null=False, backref="parameter_results", on_delete="CASCADE", index=True
    )
    parameter: ExamParameter = ForeignKeyField(
        ExamParameter, null=False, backref="results", on_delete="CASCADE", index=True
    )
    value_numeric: float | None = DoubleField(null=True)
    value_text: str | None = TextField(null=True)
    value_boolean: bool | None = BooleanField(null=True)
    # Auto-computed from reference ranges
    status: str = CharField(max_length=20, default=ResultStatus.PENDING.value, null=False)
    comment: str | None = TextField(null=True)

    class Meta:
        table_name = "gws_care_exam_parameter_result"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
        indexes = (
            # Enforce one result per exam × parameter
            (("exam_id", "parameter_id"), True),
        )


class ExamParameterResultService:
    """Save, recompute and query normalized exam results."""

    @classmethod
    def upsert(
        cls,
        exam_id: str,
        parameter_id: str,
        value_numeric: float | None = None,
        value_text: str | None = None,
        value_boolean: bool | None = None,
        comment: str | None = None,
    ) -> ExamParameterResult:
        """Create or update a result row and auto-compute its status."""
        param = ExamParameter.get_by_id(parameter_id)
        status = cls._compute_status(param, value_numeric, value_text, value_boolean)
        result, _ = ExamParameterResult.get_or_create(
            exam_id=exam_id,
            parameter_id=parameter_id,
        )
        result.value_numeric = value_numeric
        result.value_text = value_text
        result.value_boolean = value_boolean
        result.status = status.value
        result.comment = comment
        result.save()
        return result

    @classmethod
    def bulk_upsert(cls, exam_id: str, entries: list[dict]) -> None:
        """Upsert multiple results at once.

        Each entry dict: {parameter_id, value_numeric?, value_text?, value_boolean?, comment?}
        """
        for entry in entries:
            cls.upsert(
                exam_id=exam_id,
                parameter_id=entry["parameter_id"],
                value_numeric=entry.get("value_numeric"),
                value_text=entry.get("value_text"),
                value_boolean=entry.get("value_boolean"),
                comment=entry.get("comment"),
            )

    @classmethod
    def list_for_exam(cls, exam_id: str) -> list[ExamParameterResult]:
        return list(
            ExamParameterResult.select(ExamParameterResult, ExamParameter)
            .join(ExamParameter)
            .where(ExamParameterResult.exam == exam_id)
            .order_by(ExamParameter.display_order)
        )

    @classmethod
    def has_critical_values(cls, exam_id: str) -> bool:
        return (
            ExamParameterResult.select()
            .where(
                (ExamParameterResult.exam == exam_id)
                & ExamParameterResult.status.in_([
                    ResultStatus.CRITICAL_LOW.value,
                    ResultStatus.CRITICAL_HIGH.value,
                    ResultStatus.POSITIVE.value,
                ])
            )
            .exists()
        )

    @classmethod
    def query_abnormal_by_parameter(
        cls,
        parameter_id: str,
        limit: int = 500,
    ) -> list[ExamParameterResult]:
        """Cross-patient analytics: all abnormal/critical readings for a parameter."""
        return list(
            ExamParameterResult.select()
            .where(
                (ExamParameterResult.parameter == parameter_id)
                & ExamParameterResult.status.not_in([
                    ResultStatus.NORMAL.value,
                    ResultStatus.NEGATIVE.value,
                    ResultStatus.PENDING.value,
                ])
            )
            .order_by(ExamParameterResult.id.desc())
            .limit(limit)
        )

    @classmethod
    def _compute_status(
        cls,
        param: ExamParameter,
        value_numeric: float | None,
        value_text: str | None,
        value_boolean: bool | None,
    ) -> ResultStatus:
        if value_boolean is not None:
            return ResultStatus.POSITIVE if value_boolean else ResultStatus.NEGATIVE
        if value_numeric is not None:
            if param.critical_low is not None and value_numeric <= param.critical_low:
                return ResultStatus.CRITICAL_LOW
            if param.critical_high is not None and value_numeric >= param.critical_high:
                return ResultStatus.CRITICAL_HIGH
            if param.ref_low is not None and value_numeric < param.ref_low:
                return ResultStatus.ABNORMAL_LOW
            if param.ref_high is not None and value_numeric > param.ref_high:
                return ResultStatus.ABNORMAL_HIGH
            return ResultStatus.NORMAL
        if value_text is not None:
            return ResultStatus.NORMAL
        return ResultStatus.PENDING
