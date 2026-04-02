"""Care-specific user role enum."""

from enum import Enum


class CareRole(str, Enum):
    """Application-level roles for gws_care.

    These roles are independent of gws_core's UserGroup (ADMIN/USER).
    A user can hold multiple CareRoles simultaneously.
    """

    ADMIN = "ADMIN"          # Full access: user management, all data
    DOCTOR = "DOCTOR"        # Can enter/validate exam interpretations
    OPERATOR = "OPERATOR"    # Scheduling and patient/account management

    def get_label(self) -> str:
        labels = {
            CareRole.ADMIN: "Administrator",
            CareRole.DOCTOR: "Doctor",
            CareRole.OPERATOR: "Operator",
        }
        return labels[self]
