"""CampaignDoctor — linking table between Campaign and MedicalDoctor (N:N)."""

from peewee import ForeignKeyField

from gws_care.campaign.campaign import Campaign
from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.doctor.medical_doctor import MedicalDoctor


class CampaignDoctor(ModelWithUser):
    """Associates one or more doctors with a campaign.

    A campaign can have multiple medical doctors (e.g. a GP and a cardiologist).
    Deleting the campaign or the doctor cascades and removes the link.
    """

    campaign: Campaign = ForeignKeyField(
        Campaign, null=False, backref="campaign_doctors", on_delete="CASCADE", index=True
    )
    doctor: MedicalDoctor = ForeignKeyField(
        MedicalDoctor, null=False, backref="campaign_assignments", on_delete="CASCADE", index=True
    )

    class Meta:
        table_name = "gws_care_campaign_doctor"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
        indexes = ((("campaign_id", "doctor_id"), True),)  # unique pair
