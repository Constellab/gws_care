"""Enumeration of visit validation steps."""

from enum import Enum


class VisitValidationStep(Enum):
    """Each distinct validation step a visit passes through.

    Rows in VisitValidationWorkflow record who performed each step
    and when, providing a complete audit trail of the visit lifecycle.
    """

    TERRAIN_DONE = "on-site_done"
    """Patient seen on on-site — samples collected. Marked by Opérateur Terrain."""

    RESULTS_ENTERED = "results_entered"
    """All exam results entered by HQ Operator (not yet lab-validated)."""

    LAB_VALIDATED = "lab_validated"
    """Results locked by HQ Operator (Lab Validation)."""

    DOCTOR_CLINIC_VALIDATED = "doctor_clinic_validated"
    """Visit interpreted and signed off by Clinic Doctor."""

    DOCTOR_COMPANY_VALIDATED = "doctor_company_validated"
    """Visit validated by Company Doctor — patient notified."""

    def get_label(self) -> str:
        labels = {
            VisitValidationStep.TERRAIN_DONE: "On-site Done",
            VisitValidationStep.RESULTS_ENTERED: "Results Entered",
            VisitValidationStep.LAB_VALIDATED: "Lab Validated",
            VisitValidationStep.DOCTOR_CLINIC_VALIDATED: "Clinic Doctor Validated",
            VisitValidationStep.DOCTOR_COMPANY_VALIDATED: "Company Doctor Validated",
        }
        return labels.get(self, self.value)
