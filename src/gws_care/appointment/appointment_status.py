"""Appointment status enum."""

from enum import Enum


class AppointmentStatus(str, Enum):
    """Lifecycle status for an appointment."""

    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCELLED = "CANCELLED"

    def get_label(self) -> str:
        labels = {
            AppointmentStatus.SCHEDULED: "Scheduled",
            AppointmentStatus.IN_PROGRESS: "In Progress",
            AppointmentStatus.DONE: "Done",
            AppointmentStatus.CANCELLED: "Cancelled",
        }
        return labels[self]
