"""CampaignValidationWorkflow model — audit trail of campaign validation steps."""

from datetime import datetime

from gws_core import EnumField, Model
from peewee import CompositeKey, DateTimeField, ForeignKeyField, TextField

from gws_care.campaign.campaign import Campaign
from gws_care.core.care_db_manager import CareDbManager
from gws_care.user.user import User
from gws_care.workflow.campaign_validation_step import CampaignValidationStep


class CampaignValidationWorkflow(Model):
    """One row per completed validation step for a campaign.

    Uniqueness is enforced on (campaign, step): each step can only be
    recorded once per campaign, reflecting the sequential, non-reversible
    nature of the validation chain.

    Example query — full audit trail for a campaign:
        CampaignValidationWorkflow
            .select()
            .where(CampaignValidationWorkflow.campaign == campaign_id)
            .order_by(CampaignValidationWorkflow.validated_at)
    """

    campaign: Campaign = ForeignKeyField(Campaign, null=False, backref="validation_workflow", on_delete="CASCADE", column_name='campaign_id')
    step: CampaignValidationStep = EnumField(choices=CampaignValidationStep, null=False)
    validated_by: User = ForeignKeyField(User, null=True, backref="+")
    validated_at: datetime = DateTimeField(null=False)
    notes: str = TextField(null=True)

    class Meta:
        table_name = "gws_care_campaign_validation_workflow"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
        primary_key = CompositeKey("campaign", "step")


