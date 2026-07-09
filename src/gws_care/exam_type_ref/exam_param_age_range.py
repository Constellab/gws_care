"""ExamParameterAgeRange — age/gender-specific reference thresholds for an ExamParameter."""

from peewee import CharField, DoubleField, ForeignKeyField, IntegerField, TextField

from gws_care.core.care_db_manager import CareDbManager
from gws_core import Model
from gws_care.exam_type_ref.exam_parameter import ExamParameter


class ExamParameterAgeRange(Model):
    """Age and gender-specific reference thresholds that override generic param thresholds.

    When evaluating a patient result, the system finds the most specific matching
    range (age+gender > age-ALL > gender columns > generic). Thresholds set here
    override the flat columns on ExamParameter for the matched patient.
    """

    exam_parameter: ExamParameter = ForeignKeyField(
        ExamParameter, null=False, backref="age_ranges", on_delete="CASCADE"
    )
    age_min: int = IntegerField(null=True)   # inclusive lower bound (None = 0)
    age_max: int = IntegerField(null=True)   # inclusive upper bound (None = ∞)
    gender: str = CharField(max_length=5, default="ALL", null=False)  # "ALL" | "M" | "F"
    ref_low: float = DoubleField(null=True)
    ref_high: float = DoubleField(null=True)
    critical_low: float = DoubleField(null=True)
    critical_high: float = DoubleField(null=True)
    label_normal: str = TextField(null=True)
    label_low: str = TextField(null=True)
    label_high: str = TextField(null=True)
    label_critical_low: str = TextField(null=True)
    label_critical_high: str = TextField(null=True)

    class Meta:
        table_name = "gws_care_exam_param_age_range"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()


def resolve_param_thresholds(
    param: ExamParameter,
    patient_age: int | None,
    patient_gender: str | None,
    preloaded_ranges: list | None = None,
) -> dict:
    """Return resolved reference thresholds and labels for a param + patient context.

    Priority: age+gender range > age-ALL range > gender-specific columns > generic columns.

    Returns dict with keys:
      ref_low, ref_high, crit_low, crit_high,
      label_normal, label_low, label_high, label_crit_low, label_crit_high
    """
    if preloaded_ranges is not None:
        ranges = [r for r in preloaded_ranges if str(r.exam_parameter_id) == str(param.id)]
    else:
        ranges = list(ExamParameterAgeRange.select().where(
            ExamParameterAgeRange.exam_parameter == param.id
        ))

    if ranges:
        gender_matches = []
        all_matches = []
        for r in ranges:
            if patient_age is not None:
                age_ok = (
                    (r.age_min is None or patient_age >= r.age_min)
                    and (r.age_max is None or patient_age <= r.age_max)
                )
            else:
                # Age unknown: only match ranges with no age restrictions
                age_ok = r.age_min is None and r.age_max is None
            if age_ok:
                if patient_gender and r.gender == patient_gender:
                    gender_matches.append(r)
                elif r.gender == "ALL":
                    all_matches.append(r)
        best = gender_matches[0] if gender_matches else (all_matches[0] if all_matches else None)
        if best:
            return {
                "ref_low": best.ref_low,
                "ref_high": best.ref_high,
                "crit_low": best.critical_low,
                "crit_high": best.critical_high,
                "label_normal": best.label_normal or param.label_normal or "",
                "label_low": best.label_low or param.label_low or "",
                "label_high": best.label_high or param.label_high or "",
                "label_crit_low": best.label_critical_low or param.label_critical_low or "",
                "label_crit_high": best.label_critical_high or param.label_critical_high or "",
            }

    # Fall back to existing gender-specific column logic
    if patient_gender == "M" and (param.ref_low_m is not None or param.ref_high_m is not None):
        return {
            "ref_low": param.ref_low_m,
            "ref_high": param.ref_high_m,
            "crit_low": param.critical_low_m,
            "crit_high": param.critical_high_m,
            "label_normal": param.label_normal or "",
            "label_low": param.label_low or "",
            "label_high": param.label_high or "",
            "label_crit_low": param.label_critical_low or "",
            "label_crit_high": param.label_critical_high or "",
        }
    if patient_gender == "F" and (param.ref_low_f is not None or param.ref_high_f is not None):
        return {
            "ref_low": param.ref_low_f,
            "ref_high": param.ref_high_f,
            "crit_low": param.critical_low_f,
            "crit_high": param.critical_high_f,
            "label_normal": param.label_normal or "",
            "label_low": param.label_low or "",
            "label_high": param.label_high or "",
            "label_crit_low": param.label_critical_low or "",
            "label_crit_high": param.label_critical_high or "",
        }
    return {
        "ref_low": param.ref_low,
        "ref_high": param.ref_high,
        "crit_low": param.critical_low,
        "crit_high": param.critical_high,
        "label_normal": param.label_normal or "",
        "label_low": param.label_low or "",
        "label_high": param.label_high or "",
        "label_crit_low": param.label_critical_low or "",
        "label_crit_high": param.label_critical_high or "",
    }
