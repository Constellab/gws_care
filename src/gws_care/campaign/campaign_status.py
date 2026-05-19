"""CampaignStatus enumeration."""

from enum import Enum


class CampaignStatus(Enum):
    """Lifecycle status of a Campaign."""

    DRAFT = "draft"                             # Created, not yet validated
    VALIDATED = "validated"                     # Validated by clinic doctor or admin — ready for field
    IN_PROGRESS = "in_progress"                 # Field operations started
    LAB_DONE = "lab_done"                       # All lab results entered and lab-validated
    DOCTOR_CLINIC_VALIDATED = "doctor_clinic_validated"     # Clinic doctor has interpreted all visits
    DOCTOR_COMPANY_VALIDATED = "doctor_company_validated"   # Company doctor has validated all visits
    CLOSED = "closed"                           # All visits validated — campaign formally closed
    ARCHIVED = "archived"                       # Archived (manual or automatic)

    def get_label(self) -> str:
        labels = {
            CampaignStatus.DRAFT: "Draft",
            CampaignStatus.VALIDATED: "Validated",
            CampaignStatus.IN_PROGRESS: "In Progress",
            CampaignStatus.LAB_DONE: "Lab Done",
            CampaignStatus.DOCTOR_CLINIC_VALIDATED: "Clinic Doctor Validated",
            CampaignStatus.DOCTOR_COMPANY_VALIDATED: "Company Doctor Validated",
            CampaignStatus.CLOSED: "Closed",
            CampaignStatus.ARCHIVED: "Archived",
        }
        return labels.get(self, self.value)
