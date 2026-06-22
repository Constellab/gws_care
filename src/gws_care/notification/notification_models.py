"""Notification models.

Three tables:
- NotificationLog       : history of every message sent or attempted
- NotificationPreference: per-user setting for appointment reminder days
- NotificationBell      : lightweight in-app notification for the bell icon
"""

from datetime import datetime

from gws_core import EnumField, Model
from gws_core.core.model.db_field import JSONField
from peewee import BooleanField, CharField, DateTimeField, ForeignKeyField, IntegerField, TextField

from gws_care.account.account import Account
from gws_care.core.care_db_manager import CareDbManager
from gws_care.notification.notification_enums import (
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)
from gws_care.patient.patient import Patient
from gws_care.user.user import User
from gws_care.visit.visit import Visit


class NotificationLog(Model):
    """Persistent record of every notification attempt."""

    notification_type: NotificationType = EnumField(choices=NotificationType, null=False)
    channel: NotificationChannel = EnumField(
        choices=NotificationChannel, default=NotificationChannel.EMAIL, null=False
    )
    status: NotificationStatus = EnumField(
        choices=NotificationStatus, default=NotificationStatus.PENDING, null=False
    )

    # Recipients (optional FKs — only one set at a time)
    patient: Patient = ForeignKeyField(Patient, null=True, backref="notification_logs", on_delete="SET NULL")
    account: Account = ForeignKeyField(Account, null=True, backref="notification_logs", on_delete="SET NULL")
    recipient_email: str = CharField(max_length=255, null=True)
    recipient_phone: str = CharField(max_length=50, null=True)
    recipient_name: str = CharField(max_length=255, null=True)

    # Content
    subject: str = TextField(null=False)
    body: str = TextField(null=False)

    # Metadata
    sent_by: User = ForeignKeyField(User, null=True, backref="+", on_delete="SET NULL")
    recipient_user: User = ForeignKeyField(User, null=True, backref="received_notifications", on_delete="SET NULL")
    parent_log = ForeignKeyField("self", null=True, backref="replies", on_delete="SET NULL")
    related_visit: Visit = ForeignKeyField(
        Visit, null=True, backref="notification_logs", on_delete="SET NULL"
    )
    error_message: str = TextField(null=True)
    extra_data: dict = JSONField(null=True)

    class Meta:
        table_name = "gws_care_notification_log"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()


class NotificationPreference(Model):
    """Per-user notification schedule: reminder days before appointments."""

    user: User = ForeignKeyField(User, null=False, unique=True, backref="notification_prefs", on_delete="CASCADE")
    # JSON list of integers, e.g. [15, 7, 1]
    reminder_days: list = JSONField(null=False, default=[7, 1])
    email_reminders_enabled: bool = BooleanField(default=True, null=False)

    class Meta:
        table_name = "gws_care_notification_preference"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()


class NotificationBell(Model):
    """In-app notification bell entry for a specific user."""

    user: User = ForeignKeyField(User, null=False, backref="bell_notifications", on_delete="CASCADE")
    message: str = TextField(null=False)
    is_read: bool = BooleanField(default=False, null=False)
    related_log: NotificationLog = ForeignKeyField(
        NotificationLog, null=True, backref="+", on_delete="CASCADE"
    )

    class Meta:
        table_name = "gws_care_notification_bell"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()


class SmtpConfig(Model):
    """Singleton SMTP server configuration for outgoing emails.

    The SMTP password is NOT stored here. Instead, 'credentials_name' references
    a Constellab Credentials object of type BASIC whose password field holds it.
    """

    host: str = CharField(max_length=255, null=True)
    port: int = IntegerField(default=587, null=False)
    credentials_name: str = CharField(max_length=255, null=True)
    use_tls: bool = BooleanField(default=True, null=False)
    from_email: str = CharField(max_length=255, null=True)
    from_name: str = CharField(max_length=255, null=True)

    class Meta:
        table_name = "gws_care_smtp_config"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()

