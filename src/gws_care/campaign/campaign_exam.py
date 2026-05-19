"""CampaignExam — M2M between a Campaign and an ExamTypeRef.

Defines which exam types are included in a given campaign.
"""

from gws_care.campaign.campaign import Campaign
from gws_care.core.care_db_manager import CareDbManager
from gws_core import Model
from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
from peewee import ForeignKeyField


class CampaignExam(Model):
    """Associates an exam type to a campaign (M2M)."""

    campaign: Campaign = ForeignKeyField(
        Campaign, null=False, backref="exam_types", on_delete="CASCADE"
    )
    exam_type_ref: ExamTypeRef = ForeignKeyField(
        ExamTypeRef, null=False, backref="campaigns", on_delete="CASCADE"
    )

    class Meta:
        table_name = "gws_care_campaign_exam"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
        indexes = ((("campaign", "exam_type_ref"), True),)
