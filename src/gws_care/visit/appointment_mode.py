"""AppointmentMode enum — how the patient/doctor will meet."""

from enum import Enum


class AppointmentMode(str, Enum):
    AT_WORK = "at_work"
    AT_HOME = "at_home"
    ADDRESS = "address"
    VISIO = "visio"
    HOSPITAL = "hospital"

    def get_label(self) -> str:
        return {
            AppointmentMode.AT_WORK: "At work",
            AppointmentMode.AT_HOME: "At home",
            AppointmentMode.ADDRESS: "Address",
            AppointmentMode.VISIO: "Visio",
            AppointmentMode.HOSPITAL: "Hospital",
        }[self]
