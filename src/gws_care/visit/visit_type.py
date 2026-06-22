"""VisitType enumeration."""

from enum import Enum


class VisitType(str, Enum):
    """Discriminator for visit types.

    CONSULTATION — standalone medical visit; doctor can attach prescriptions,
                   certificates, and/or exam records.
                   Simple PENDING → CLOSED lifecycle.

    CAMPAIGN     — visit within a campaign; full validation workflow applies:
                   PENDING → VISIT_DONE → LAB_DONE
                           → DOCTOR_CLINIC_VALIDATED → DOCTOR_COMPANY_VALIDATED
                   Validation steps tracked in CampaignVisitValidationWorkflow.
    """

    CONSULTATION = "consultation"
    CAMPAIGN = "campaign"

    def get_label(self) -> str:
        labels = {
            VisitType.CONSULTATION: "Consultation",
            VisitType.CAMPAIGN: "Campaign Visit",
        }
        return labels[self]
