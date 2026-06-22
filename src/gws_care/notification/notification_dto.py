"""DTOs for the notification system."""

from gws_core import BaseModelDTO, ModelDTO

from gws_care.notification.notification_enums import (
    NotificationStatus,
    NotificationType,
)


class NotificationLogRowDTO(BaseModelDTO):
    """Lightweight row for the notification history list."""

    id: str
    created_at: str
    notification_type: str
    channel: str
    status: str
    recipient_name: str | None
    recipient_email: str | None
    subject: str
    sent_by_name: str | None


class SendManualNotificationDTO(BaseModelDTO):
    """DTO for sending a manual message to one or more recipients."""

    patient_id: str | None = None
    account_id: str | None = None
    subject: str
    body: str


class SendCustomMessageDTO(BaseModelDTO):
    """DTO for sending a free-form message to a single patient."""

    patient_id: str
    subject: str
    body: str


class NotificationPreferenceDTO(BaseModelDTO):
    """DTO for reading/updating a user's notification preferences."""

    reminder_days: list[int]
    email_reminders_enabled: bool


class NotificationBellDTO(BaseModelDTO):
    """DTO for an in-app bell notification."""

    id: str
    message: str
    is_read: bool
    related_log_id: str | None
    created_at: str


class SmtpConfigDTO(BaseModelDTO):
    """DTO for SMTP server configuration.

    credentials_name: name of a Constellab Credentials (type BASIC) that holds
    the SMTP username and password. Neither is stored directly here.
    """

    host: str = ""
    port: int = 587
    credentials_name: str = ""
    use_tls: bool = True
    from_email: str = ""
    from_name: str = ""
