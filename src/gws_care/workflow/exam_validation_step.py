"""Enumeration of exam validation steps."""

from enum import Enum


class ExamValidationStep(Enum):
    """Each distinct validation step an exam passes through.

    Rows in ExamValidationWorkflow record who performed each step
    and when, providing a complete audit trail of the exam lifecycle.
    """

    IN_PROGRESS_RESULTS = "in_progress_results"
    """Informations saved by operator — exam moves to Results step."""

    IN_PROGRESS_INTERPRETATION = "in_progress_interpretation"
    """Results submitted for medical review by operator."""

    DONE = "done"
    """Medical interpretation submitted by doctor — exam complete."""

    def get_label(self) -> str:
        labels = {
            ExamValidationStep.IN_PROGRESS_RESULTS: "Informations Saved",
            ExamValidationStep.IN_PROGRESS_INTERPRETATION: "Submitted for Review",
            ExamValidationStep.DONE: "Interpreted",
        }
        return labels.get(self, self.value)
