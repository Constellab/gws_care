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
            AppointmentMode.AT_WORK: "Au travail",
            AppointmentMode.AT_HOME: "À domicile",
            AppointmentMode.ADDRESS: "Adresse",
            AppointmentMode.VISIO: "Visio",
            AppointmentMode.HOSPITAL: "Hôpital",
        }[self]
