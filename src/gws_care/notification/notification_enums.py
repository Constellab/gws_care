"""Notification channel and status enumerations."""

from enum import Enum


class NotificationChannel(str, Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"
    IN_APP = "IN_APP"


class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class NotificationType(str, Enum):
    APPOINTMENT_REMINDER = "APPOINTMENT_REMINDER"
    MANUAL_PATIENT = "MANUAL_PATIENT"
    MANUAL_ACCOUNT = "MANUAL_ACCOUNT"
