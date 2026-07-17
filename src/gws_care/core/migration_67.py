"""DB migration v0.68.3 — Remove test campaign "test_subway" and 2 test certificates.

One-off cleanup of a test/demo campaign requested by the user, along with its
cascade-linked visits, exam configs, and doctor assignments, plus 2 test
certificates left over from manual testing. Scoped to these specific IDs
only — a no-op on any install where they don't exist. Follows the same
explicit-delete-order pattern as migration_65.py rather than relying on
DB-level FK cascade.
"""

from gws_care.core.care_db_manager import CareDbManager
from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

_CAMPAIGN_IDS = [
    "dae61ae0-638f-45a8-8075-32106ca5960b",  # "test_subway"
]

_CERTIFICATE_IDS = [
    "460b7fce-d86b-4cd7-8a09-e6a0872b3bc6",  # Asma BENNEJI, "il ne peut pas"
    "dea04191-6c79-4c7e-bbb1-7b5d7115ca8a",  # Asma BENNEJI, "il ne peut"
]


@brick_migration(
    "0.68.3",
    short_description="Remove test_subway campaign and its cascade-linked visits/exams/doctor links",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration670(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        from gws_care.campaign.campaign import Campaign
        from gws_care.campaign.campaign_doctor import CampaignDoctor
        from gws_care.campaign.campaign_exam import CampaignExam
        from gws_care.campaign.campaign_exam_doctor import CampaignExamDoctor
        from gws_care.campaign.campaign_patient import CampaignPatient
        from gws_care.visit.visit import Visit
        from gws_care.workflow.campaign_validation_workflow import CampaignValidationWorkflow
        from gws_care.workflow.campaign_visit_validation_workflow import CampaignVisitValidationWorkflow

        campaigns = list(Campaign.select().where(Campaign.id.in_(_CAMPAIGN_IDS)))
        if campaigns:
            campaign_ids = [c.id for c in campaigns]

            exam_ids = [
                e.id for e in CampaignExam.select(CampaignExam.id).where(CampaignExam.campaign.in_(campaign_ids))
            ]
            if exam_ids:
                CampaignExamDoctor.delete().where(CampaignExamDoctor.campaign_exam.in_(exam_ids)).execute()
            CampaignExam.delete().where(CampaignExam.campaign.in_(campaign_ids)).execute()
            CampaignDoctor.delete().where(CampaignDoctor.campaign.in_(campaign_ids)).execute()
            CampaignValidationWorkflow.delete().where(CampaignValidationWorkflow.campaign.in_(campaign_ids)).execute()

            visit_ids = [v.id for v in Visit.select(Visit.id).where(Visit.campaign.in_(campaign_ids))]
            if visit_ids:
                CampaignVisitValidationWorkflow.delete().where(
                    CampaignVisitValidationWorkflow.visit.in_(visit_ids)
                ).execute()
            Visit.delete().where(Visit.campaign.in_(campaign_ids)).execute()

            CampaignPatient.delete().where(CampaignPatient.campaign.in_(campaign_ids)).execute()

            Campaign.delete().where(Campaign.id.in_(campaign_ids)).execute()

        from gws_care.certificate.medical_certificate import MedicalCertificate
        MedicalCertificate.delete().where(MedicalCertificate.id.in_(_CERTIFICATE_IDS)).execute()
