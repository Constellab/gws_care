"""ThresholdService — automatic appreciation calculation from ExamTypeModel thresholds."""

from __future__ import annotations

from gws_care.exam.appreciation import Appreciation


class ThresholdService:
    """Pure-logic service for computing exam appreciations from numeric thresholds.

    The ExamTypeModel stores four optional threshold boundaries:
        threshold_critical_low < threshold_low ≤ (normal range) ≤ threshold_high < threshold_critical_high

    Classification rules (first matching rule wins):
    1. value < threshold_critical_low  →  CRITICAL_LOW
    2. value < threshold_low           →  LOW
    3. value > threshold_critical_high →  CRITICAL_HIGH
    4. value > threshold_high          →  HIGH
    5. otherwise                       →  NORMAL
    """

    @classmethod
    def calculate_appreciation(
        cls,
        exam_type_model: "ExamTypeModel",  # noqa: F821  (lazy import to avoid circular)
        value: float,
    ) -> Appreciation:
        """Return the appreciation for *value* using the thresholds from *exam_type_model*.

        Thresholds that are None are simply ignored (treated as ±∞).
        """
        tcl = exam_type_model.threshold_critical_low
        tl = exam_type_model.threshold_low
        th = exam_type_model.threshold_high
        tch = exam_type_model.threshold_critical_high

        if tcl is not None and value < tcl:
            return Appreciation.CRITICAL_LOW
        if tl is not None and value < tl:
            return Appreciation.LOW
        if tch is not None and value > tch:
            return Appreciation.CRITICAL_HIGH
        if th is not None and value > th:
            return Appreciation.HIGH
        return Appreciation.NORMAL

    @classmethod
    def has_thresholds(cls, exam_type_model: "ExamTypeModel") -> bool:  # noqa: F821
        """Return True if the exam type model has at least one threshold defined."""
        return any(
            v is not None
            for v in (
                exam_type_model.threshold_critical_low,
                exam_type_model.threshold_low,
                exam_type_model.threshold_high,
                exam_type_model.threshold_critical_high,
            )
        )

    @classmethod
    def find_exam_type_model_for_exam(cls, exam: "Exam") -> "ExamTypeModel | None":  # noqa: F821
        """Return the best matching ExamTypeModel for an exam.

        Strategy: look for an active ExamTypeModel whose category matches the
        exam's exam_type.  If multiple match, take the one with at least one
        threshold defined (first match wins).  Returns None if no match found.
        """
        from gws_care.exam.exam_type_model import ExamTypeModel

        candidates = list(
            ExamTypeModel.select().where(
                ExamTypeModel.category == exam.exam_type,
                ExamTypeModel.is_active == True,
            )
        )
        # Prefer one with thresholds
        for candidate in candidates:
            if cls.has_thresholds(candidate):
                return candidate
        # Fall back to first match without thresholds (so callers can still check)
        return candidates[0] if candidates else None
