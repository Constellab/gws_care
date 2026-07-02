"""CampaignExamDoctor — M2M between CampaignExam and MedicalDoctor."""

from gws_care.campaign.campaign_exam import CampaignExam
from gws_care.core.care_db_manager import CareDbManager
from gws_care.doctor.medical_doctor import MedicalDoctor
from gws_core import Model
from peewee import ForeignKeyField


class CampaignExamDoctor(Model):
    """Links one or more MedicalDoctors to a specific exam slot within a campaign."""

    campaign_exam: CampaignExam = ForeignKeyField(
        CampaignExam, null=False, backref="exam_doctors", on_delete="CASCADE"
    )
    doctor: MedicalDoctor = ForeignKeyField(
        MedicalDoctor, null=False, backref="campaign_exam_doctors", on_delete="CASCADE"
    )

    class Meta:
        table_name = "gws_care_campaign_exam_doctor"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
        indexes = ((("campaign_exam", "doctor"), True),)
