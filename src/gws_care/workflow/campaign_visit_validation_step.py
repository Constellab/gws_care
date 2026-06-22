"""Enumeration of campaign visit validation steps."""

from enum import Enum


class CampaignVisitValidationStep(Enum):
    """Each distinct validation step a visit passes through.

    Rows in CampaignVisitValidationWorkflow record who performed each step
    and when, providing a complete audit trail of the visit lifecycle.
    """

    VISIT_DONE = "visit_done"
    """Patient seen on-site — samples collected. Marked by Opérateur Terrain."""

    LAB_DONE = "lab_done"
    """Results locked by HQ Operator (Lab Validation)."""

    DOCTOR_CLINIC_VALIDATED = "doctor_clinic_validated"
    """Visit interpreted and signed off by Clinic Doctor."""

    DOCTOR_COMPANY_VALIDATED = "doctor_company_validated"
    """Visit validated by Company Doctor — patient notified."""

    def get_label(self) -> str:
        labels = {
            CampaignVisitValidationStep.VISIT_DONE: "Visit Done",
            CampaignVisitValidationStep.LAB_DONE: "Lab Done",
            CampaignVisitValidationStep.DOCTOR_CLINIC_VALIDATED: "Clinic Doctor Validated",
            CampaignVisitValidationStep.DOCTOR_COMPANY_VALIDATED: "Company Doctor Validated",
        }
        return labels.get(self, self.value)


