"""Appreciation enum — automatic result quality level based on thresholds."""

from enum import Enum


class Appreciation(str, Enum):
    """Ordered appreciation levels for a numeric exam result.

    Ordered from worst low to worst high:
        CRITICAL_LOW < LOW < NORMAL < HIGH < CRITICAL_HIGH
    """

    CRITICAL_LOW = "critical_low"
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL_HIGH = "critical_high"

    def get_label(self) -> str:
        labels = {
            Appreciation.CRITICAL_LOW: "Critique bas",
            Appreciation.LOW: "Bas",
            Appreciation.NORMAL: "Normal",
            Appreciation.HIGH: "Haut",
            Appreciation.CRITICAL_HIGH: "Critique haut",
        }
        return labels[self]

    def is_abnormal(self) -> bool:
        """Return True for any non-normal appreciation."""
        return self != Appreciation.NORMAL

    def is_critical(self) -> bool:
        return self in (Appreciation.CRITICAL_LOW, Appreciation.CRITICAL_HIGH)
