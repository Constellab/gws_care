"""AppointmentMode enum — how the patient/doctor will meet."""

from enum import Enum


class AppointmentMode(str, Enum):
    ONSITE = "onsite"
    VISIO = "visio"
    HOSPITAL = "hospital"

    def get_label(self) -> str:
        return {
            AppointmentMode.ONSITE: "On-site",
            AppointmentMode.VISIO: "Visio",
            AppointmentMode.HOSPITAL: "Hospital",
        }[self]
