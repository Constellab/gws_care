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
    # No reference thresholds configured on the parameter — nothing to evaluate against
    NOT_EVALUATED = "NOT_EVALUATED"

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
            "NOT_EVALUATED": "",
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
            "NOT_EVALUATED": "gray",
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
        patient_gender: str | None = None,
    ) -> ExamParameterResult:
        """Create or update a result row and auto-compute its status."""
        param = ExamParameter.get_by_id(parameter_id)
        status = cls._compute_status(param, value_numeric, value_text, value_boolean, patient_gender)
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
    def bulk_upsert(cls, exam_id: str, entries: list[dict], patient_gender: str | None = None) -> None:
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
                patient_gender=patient_gender,
            )

    @classmethod
    def bulk_upsert_with_computed(
        cls, exam_id: str, exam_type_ref_id: str, entries: list[dict],
        patient_gender: str | None = None,
    ) -> None:
        """Upsert manual entries then evaluate and save computed parameters.

        After saving manual values, any parameter with is_computed=True and a
        formula is auto-evaluated using the manual values as the variable context.
        Chaining is supported: computed params are evaluated in display_order so
        a computed param can reference another computed param defined earlier.

        entries: list of {parameter_id, value_numeric?, value_text?, value_boolean?, comment?}
        """
        from gws_care.exam_type_ref.exam_formula_engine import ExamFormulaEngine, FormulaEvaluationError

        # 1. Save all manual (non-computed) entries
        manual_only = [
            e for e in entries
            if not ExamParameter.get_by_id(e["parameter_id"]).is_computed
        ]
        cls.bulk_upsert(exam_id, manual_only, patient_gender=patient_gender)

        # 2. Build code → value context from manual results
        all_params = list(
            ExamParameter.select()
            .where(
                (ExamParameter.exam_type_ref == exam_type_ref_id)
                & (ExamParameter.is_active == True)
            )
            .order_by(ExamParameter.display_order)
        )

        # Seed context with manual values (by code)
        context: dict[str, float] = {}
        entry_by_id = {e["parameter_id"]: e for e in entries}
        for param in all_params:
            if param.code and not param.is_computed:
                entry = entry_by_id.get(str(param.id))
                val = entry.get("value_numeric") if entry else None
                if val is not None:
                    context[param.code] = float(val)

        # 3. Evaluate computed parameters in display_order (supports chaining)
        for param in all_params:
            if not param.is_computed or not param.formula:
                continue
            try:
                value = ExamFormulaEngine.evaluate(param.formula, context)
                cls.upsert(exam_id=exam_id, parameter_id=str(param.id), value_numeric=value,
                           patient_gender=patient_gender)
                if param.code:
                    context[param.code] = value
            except FormulaEvaluationError:
                # Missing dependencies — leave this param as PENDING
                pass

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
                    ResultStatus.NOT_EVALUATED.value,
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
        patient_gender: str | None = None,
    ) -> ResultStatus:
        if value_boolean is not None:
            return ResultStatus.POSITIVE if value_boolean else ResultStatus.NEGATIVE
        if value_numeric is not None:
            target = getattr(param, "target_gender", "ALL") or "ALL"
            # Parameter not applicable to this patient's gender
            if target != "ALL" and patient_gender and patient_gender != target:
                return ResultStatus.PENDING
            # Pick gender-specific thresholds when available, else fall back to common
            if patient_gender == "M" and (param.ref_low_m is not None or param.ref_high_m is not None):
                ref_low = param.ref_low_m
                ref_high = param.ref_high_m
                crit_low = param.critical_low_m
                crit_high = param.critical_high_m
            elif patient_gender == "F" and (param.ref_low_f is not None or param.ref_high_f is not None):
                ref_low = param.ref_low_f
                ref_high = param.ref_high_f
                crit_low = param.critical_low_f
                crit_high = param.critical_high_f
            else:
                ref_low = param.ref_low
                ref_high = param.ref_high
                crit_low = param.critical_low
                crit_high = param.critical_high
            if crit_low is not None and value_numeric <= crit_low:
                return ResultStatus.CRITICAL_LOW
            if crit_high is not None and value_numeric >= crit_high:
                return ResultStatus.CRITICAL_HIGH
            if ref_low is not None and value_numeric < ref_low:
                return ResultStatus.ABNORMAL_LOW
            if ref_high is not None and value_numeric > ref_high:
                return ResultStatus.ABNORMAL_HIGH
            # No threshold defined at all — nothing to evaluate the value against
            if ref_low is None and ref_high is None and crit_low is None and crit_high is None:
                return ResultStatus.NOT_EVALUATED
            return ResultStatus.NORMAL
        if value_text is not None:
            # Free text has no reference thresholds — never qualify it as "normal"
            return ResultStatus.NOT_EVALUATED
        return ResultStatus.PENDING
