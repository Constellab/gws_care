"""CorrectionRequest model (US-200, US-201)."""

from datetime import datetime
from enum import Enum

from peewee import CharField, DateTimeField, ForeignKeyField, TextField

from gws_care.campaign.campaign import Campaign
from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.exam.exam import Exam
from gws_care.patient.patient import Patient
from gws_care.user.user import User


class CorrectionStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REFUSED = "REFUSED"
    APPLIED = "APPLIED"

    def get_label(self) -> str:
        return {
            "PENDING": "En attente",
            "ACCEPTED": "Acceptée",
            "REFUSED": "Refusée",
            "APPLIED": "Appliquée",
        }[self.value]

    def get_color(self) -> str:
        return {
            "PENDING": "orange",
            "ACCEPTED": "blue",
            "REFUSED": "red",
            "APPLIED": "green",
        }[self.value]


class CorrectionRequest(ModelWithUser):
    """A request to correct a validated value (US-200).

    Preserves old value, adds proposed new value, tracks approval workflow.
    """

    patient: Patient = ForeignKeyField(
        Patient, null=True, backref="corrections", on_delete="SET NULL"
    )
    campaign: Campaign = ForeignKeyField(
        Campaign, null=True, backref="corrections", on_delete="SET NULL"
    )
    exam: Exam = ForeignKeyField(
        Exam, null=True, backref="corrections", on_delete="SET NULL"
    )
    field_name: str = CharField(max_length=200, null=False)
    old_value: str = TextField(null=True)
    new_value: str = TextField(null=True)
    reason: str = TextField(null=False)
    status: str = CharField(max_length=20, default=CorrectionStatus.PENDING.value, null=False)
    reviewed_by: User = ForeignKeyField(
        User, null=True, backref="+", on_delete="SET NULL"
    )
    review_date: datetime = DateTimeField(null=True)
    review_reason: str = TextField(null=True)

    class Meta:
        table_name = "gws_care_correction_request"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
