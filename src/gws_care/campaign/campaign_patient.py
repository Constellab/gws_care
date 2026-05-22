"""Junction table: Campaign ↔ Patient (many-to-many)."""

from gws_core import Model
from peewee import ForeignKeyField

from gws_care.campaign.campaign import Campaign
from gws_care.core.care_db_manager import CareDbManager
from gws_care.patient.patient import Patient


class CampaignPatient(Model):
    """Associates a Patient with a Campaign.

    All patients in a campaign must belong to the campaign's billing account.
    """

    campaign: Campaign = ForeignKeyField(Campaign, null=False, backref="campaign_patients", on_delete="CASCADE", column_name='program_id')
    patient: Patient = ForeignKeyField(Patient, null=False, backref="campaign_patients", on_delete="CASCADE")

    class Meta:
        table_name = "gws_care_program_patient"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
        indexes = (
            (("campaign", "patient"), True),  # unique: one row per (campaign, patient)
        )
