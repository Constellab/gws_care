"""ConsultationVisitStatus enumeration — lifecycle of a consultation visit."""

from enum import Enum


class ConsultationVisitStatus(str, Enum):
    """Lifecycle status of a consultation Visit."""

    SCHEDULED = "scheduled"        # Consultation created, patient not yet seen
    IN_PROGRESS = "in_progress"    # Patient currently being seen
    DONE = "done"                  # Consultation completed
    CANCELLED = "cancelled"        # Consultation cancelled

    def get_label(self) -> str:
        labels = {
            ConsultationVisitStatus.SCHEDULED: "Scheduled",
            ConsultationVisitStatus.IN_PROGRESS: "In Progress",
            ConsultationVisitStatus.DONE: "Done",
            ConsultationVisitStatus.CANCELLED: "Cancelled",
        }
        return labels.get(self, self.value)
