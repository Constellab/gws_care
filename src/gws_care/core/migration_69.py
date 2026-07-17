"""DB migration v0.68.5 — Remove test campaign "test" and its dependents.

One-off cleanup of a test/demo campaign created while testing the campaign
workflow fixes (per-exam-type lab dispatch, direct-to-patient publishing),
along with its cascade-linked visits, exam configs, doctor assignments, and
the one test Exam record created via the new "Envoyer au labo" dispatch
mechanism. Scoped to these specific IDs only — a no-op on any install where
they don't exist. Follows the same explicit-delete-order pattern as
migration_65.py/migration_67.py/migration_68.py rather than relying on
DB-level FK cascade for the campaign/visit tables.
"""

from gws_care.core.care_db_manager import CareDbManager
from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

_CAMPAIGN_IDS = [
    "c1cc2bf2-39fa-4587-8b33-b42a4d35454e",  # "test"
]

_EXAM_IDS = [
    "28b58f9f-3f4f-4a7f-aa45-63ff06ba76a2",  # test exam dispatched to lab during testing
]


@brick_migration(
    "0.68.5",
    short_description="Remove test campaign and its cascade-linked visits/exams/doctor links",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration690(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        from gws_care.campaign.campaign import Campaign
        from gws_care.campaign.campaign_doctor import CampaignDoctor
        from gws_care.campaign.campaign_exam import CampaignExam
        from gws_care.campaign.campaign_exam_doctor import CampaignExamDoctor
        from gws_care.campaign.campaign_patient import CampaignPatient
        from gws_care.exam.exam import Exam
        from gws_care.visit.visit import Visit
        from gws_care.workflow.campaign_validation_workflow import CampaignValidationWorkflow
        from gws_care.workflow.campaign_visit_validation_workflow import CampaignVisitValidationWorkflow

        Exam.delete().where(Exam.id.in_(_EXAM_IDS)).execute()

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
