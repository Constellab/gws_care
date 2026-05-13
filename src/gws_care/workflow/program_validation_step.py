"""Enumeration of program validation steps."""

from enum import Enum


class ProgramValidationStep(Enum):
    """Each distinct validation step a program passes through.

    Rows in ProgramValidationWorkflow record who performed each step
    and when, providing a complete audit trail of the program lifecycle.
    """

    VALIDATED = "validated"
    """Initial validation by Clinic Doctor or Admin — program is ready for on-site."""

    LAB_DONE = "lab_done"
    """Lab validation by HQ Operator — all visit results are locked."""

    DOCTOR_CLINIC_VALIDATED = "doctor_clinic_validated"
    """All visits interpreted and signed off by Clinic Doctor."""

    DOCTOR_COMPANY_VALIDATED = "doctor_company_validated"
    """All visits validated by Company Doctor."""

    def get_label(self) -> str:
        labels = {
            ProgramValidationStep.VALIDATED: "Validated",
            ProgramValidationStep.LAB_DONE: "Lab Done",
            ProgramValidationStep.DOCTOR_CLINIC_VALIDATED: "Clinic Doctor Validated",
            ProgramValidationStep.DOCTOR_COMPANY_VALIDATED: "Company Doctor Validated",
        }
        return labels.get(self, self.value)
