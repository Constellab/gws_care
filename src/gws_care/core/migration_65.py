"""DB migration v0.68.1 — Remove obsolete test campaigns and their dependents.

One-off cleanup of 3 test/demo campaigns ("vvv", "bill", "ccccccccccccc")
requested by the user, along with their cascade-linked visits, exam configs,
and doctor assignments. Scoped to these specific IDs only — a no-op on any
install where they don't exist. Follows the same explicit-delete-order
pattern as migration_44.py rather than relying on DB-level FK cascade.
"""

from gws_care.core.care_db_manager import CareDbManager
from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

_CAMPAIGN_IDS = [
    "0f9f7787-72ad-42f7-83c6-04c1a8c24662",
    "1fb76318-b317-47d0-8cf1-5cdfa96c651e",
    "ba0b410b-5032-47be-add6-e95f2d4ff64d",
]


@brick_migration(
    "0.68.1",
    short_description="Remove obsolete test campaigns and their cascade-linked visits/exams/doctor links",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration650(BrickMigration):
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
        if not campaigns:
            return
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
