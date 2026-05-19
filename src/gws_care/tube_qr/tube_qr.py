"""TubeQR — QR code for a laboratory sample tube (US-081)."""

from datetime import datetime
from enum import Enum

from peewee import BooleanField, CharField, DateTimeField, ForeignKeyField, TextField

from gws_care.campaign.campaign import Campaign
from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
from gws_care.patient.patient import Patient


class TubeQRStatus(str, Enum):
    BLANK = "BLANK"          # generated, not yet associated
    ASSOCIATED = "ASSOCIATED"  # linked to patient + exam
    COLLECTED = "COLLECTED"    # sample physically taken
    CANCELLED = "CANCELLED"    # voided

    def get_label(self) -> str:
        return {
            "BLANK": "Vierge",
            "ASSOCIATED": "Associé",
            "COLLECTED": "Prélevé",
            "CANCELLED": "Annulé",
        }[self.value]

    def get_color(self) -> str:
        return {
            "BLANK": "gray",
            "ASSOCIATED": "blue",
            "COLLECTED": "green",
            "CANCELLED": "red",
        }[self.value]


class TubeQR(ModelWithUser):
    """A unique QR code attached to a sample tube in a campaign.

    Workflow: BLANK → (scanned on site) → ASSOCIATED → (sample taken) → COLLECTED.
    A BLANK tube cannot be reused (US-081 rule).
    """

    campaign: Campaign = ForeignKeyField(
        Campaign, null=False, backref="tubes", on_delete="CASCADE"
    )
    qr_code: str = CharField(max_length=100, unique=True, null=False)
    short_id: str = CharField(max_length=20, null=False)
    status: str = CharField(max_length=20, default=TubeQRStatus.BLANK.value, null=False)
    patient: Patient = ForeignKeyField(
        Patient, null=True, backref="tubes", on_delete="SET NULL"
    )
    exam_type_ref: ExamTypeRef = ForeignKeyField(
        ExamTypeRef, null=True, backref="tubes", on_delete="SET NULL"
    )
    sample_type: str = CharField(max_length=100, null=True)
    associated_at: datetime = DateTimeField(null=True)
    collected_at: datetime = DateTimeField(null=True)
    cancelled_reason: str = TextField(null=True)
    cancelled_by_id: int = CharField(max_length=36, null=True)

    class Meta:
        table_name = "gws_care_tube_qr"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
