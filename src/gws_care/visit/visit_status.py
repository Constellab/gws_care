"""VisitStatus enumeration."""

from enum import Enum


class VisitStatus(Enum):
    """Lifecycle status of a Visit."""

    PENDING = "pending"                             # Appointment scheduled, patient not yet seen
    TERRAIN_DONE = "on-site_done"                   # Patient seen on-site, samples collected
    RESULTS_ENTERED = "results_entered"             # Lab results entered (not yet validated)
    LAB_VALIDATED = "lab_validated"                 # Lab results validated — data locked
    DOCTOR_CLINIC_VALIDATED = "doctor_clinic_validated"     # Clinic doctor interpreted and signed off
    DOCTOR_COMPANY_VALIDATED = "doctor_company_validated"   # Company doctor validated and messaged patient
    CANCELLED = "cancelled"                         # Visit cancelled

    def get_label(self) -> str:
        labels = {
            VisitStatus.PENDING: "Pending",
            VisitStatus.TERRAIN_DONE: "On-site Done",
            VisitStatus.RESULTS_ENTERED: "Results Entered",
            VisitStatus.LAB_VALIDATED: "Lab Validated",
            VisitStatus.DOCTOR_CLINIC_VALIDATED: "Clinic Doctor Validated",
            VisitStatus.DOCTOR_COMPANY_VALIDATED: "Company Doctor Validated",
            VisitStatus.CANCELLED: "Cancelled",
        }
        return labels.get(self, self.value)
