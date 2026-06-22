"""Junction table: Campaign ↔ ExamTypeModel (many-to-many)."""

from gws_core import Model
from peewee import ForeignKeyField

from gws_care.campaign.campaign import Campaign
from gws_care.core.care_db_manager import CareDbManager
from gws_care.exam.exam_type_model import ExamTypeModel


class CampaignExamType(Model):
    """Associates an ExamTypeModel with a Campaign.

    Defines which exam types are to be performed during the campaign.
    """

    campaign: Campaign = ForeignKeyField(Campaign, null=False, backref="campaign_exam_types", on_delete="CASCADE", column_name='program_id')
    exam_type: ExamTypeModel = ForeignKeyField(ExamTypeModel, null=False, backref="campaign_exam_types", on_delete="CASCADE")

    class Meta:
        table_name = "gws_care_program_exam_type"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
        indexes = (
            (("campaign", "exam_type"), True),  # unique per pair
        )
