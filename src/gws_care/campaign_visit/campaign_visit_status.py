"""CampaignVisitStatus enumeration."""

from enum import Enum


class CampaignVisitStatus(Enum):
    """Lifecycle status of a CampaignVisit."""

    PENDING = "pending"                             # Appointment scheduled, patient not yet seen
    VISIT_DONE = "visit_done"                       # Patient seen on-site, samples collected
    LAB_DONE = "lab_done"                           # Lab results validated — data locked
    DOCTOR_CLINIC_VALIDATED = "doctor_clinic_validated"     # Clinic doctor interpreted and signed off
    DOCTOR_COMPANY_VALIDATED = "doctor_company_validated"   # Company doctor validated and messaged patient
    CANCELLED = "cancelled"                         # Visit cancelled

    def get_label(self) -> str:
        labels = {
            CampaignVisitStatus.PENDING: "Pending",
            CampaignVisitStatus.VISIT_DONE: "Visit Done",
            CampaignVisitStatus.LAB_DONE: "Lab Done",
            CampaignVisitStatus.DOCTOR_CLINIC_VALIDATED: "Clinic Doctor Validated",
            CampaignVisitStatus.DOCTOR_COMPANY_VALIDATED: "Company Doctor Validated",
            CampaignVisitStatus.CANCELLED: "Cancelled",
        }
        return labels.get(self, self.value)
