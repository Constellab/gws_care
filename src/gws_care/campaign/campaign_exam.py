"""CampaignExam — M2M between a Campaign and an ExamTypeRef.

Defines which exam types are included in a given campaign.
"""

from gws_care.campaign.campaign import Campaign
from gws_care.core.care_db_manager import CareDbManager
from gws_care.visit.appointment_mode import AppointmentMode
from gws_core import Model, EnumField
from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
from peewee import CharField, ForeignKeyField


class CampaignExam(Model):
    """Associates an exam type to a campaign (M2M).

    An optional doctor (MedicalDoctor) can be assigned per exam slot so they
    receive the results and can submit their clinical interpretation.
    """

    campaign: Campaign = ForeignKeyField(
        Campaign, null=False, backref="exam_types", on_delete="CASCADE"
    )
    exam_type_ref: ExamTypeRef = ForeignKeyField(
        ExamTypeRef, null=False, backref="campaigns", on_delete="CASCADE"
    )
    # Optional doctor assignment per exam type in the campaign
    assigned_doctor_id: str = CharField(max_length=36, null=True, default=None)
    assigned_doctor_name: str = CharField(max_length=300, null=True, default=None)
    # Where / how this exam takes place (AT_WORK, HOSPITAL, VISIO, …)
    location_mode: AppointmentMode = EnumField(choices=AppointmentMode, null=True, default=None)

    class Meta:
        table_name = "gws_care_campaign_exam"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
        indexes = ((("campaign", "exam_type_ref"), True),)
