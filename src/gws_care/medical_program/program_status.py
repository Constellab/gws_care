"""ProgramStatus enumeration."""

from enum import Enum


class ProgramStatus(Enum):
    """Lifecycle status of a MedicalProgram."""

    DRAFT = "draft"                             # Created, not yet validated
    VALIDATED = "validated"                     # Validated by clinic doctor or admin — ready for field
    IN_PROGRESS = "in_progress"                 # Field operations started
    LAB_DONE = "lab_done"                       # All lab results entered and lab-validated
    DOCTOR_CLINIC_VALIDATED = "doctor_clinic_validated"     # Clinic doctor has interpreted all visits
    DOCTOR_COMPANY_VALIDATED = "doctor_company_validated"   # Company doctor has validated all visits
    ARCHIVED = "archived"                       # Archived (manual or automatic)

    def get_label(self) -> str:
        labels = {
            ProgramStatus.DRAFT: "Draft",
            ProgramStatus.VALIDATED: "Validated",
            ProgramStatus.IN_PROGRESS: "In Progress",
            ProgramStatus.LAB_DONE: "Lab Done",
            ProgramStatus.DOCTOR_CLINIC_VALIDATED: "Clinic Doctor Validated",
            ProgramStatus.DOCTOR_COMPANY_VALIDATED: "Company Doctor Validated",
            ProgramStatus.ARCHIVED: "Archived",
        }
        return labels.get(self, self.value)
