"""DB migration v0.68.15 — Remove test campaign "PRG-CQRSW1EG".

One-off cleanup of a test campaign, along with its cascade-linked visits,
exam configs, doctor assignments, and campaign-linked Exam records (matched
by the "CAMP:{campaign_id}|" reason_for_visit marker, rather than a
hardcoded exam ID list, since any number of exams may have been
dispatched/entered against it).

Looked up by campaign_number rather than a hardcoded id, since the id
wasn't available when this migration was written — a no-op on any install
where this campaign_number doesn't exist. Follows the same explicit-
delete-order pattern as migration_65.py/67.py/68.py/69.py/71.py/72.py/
73.py/74.py/76.py/77.py/78.py rather than relying on DB-level FK cascade
for the campaign/visit tables.
"""

from gws_care.core.care_db_manager import CareDbManager
from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

_CAMPAIGN_NUMBERS = [
    "PRG-CQRSW1EG",
]


@brick_migration(
    "0.68.15",
    short_description="Remove test campaign PRG-CQRSW1EG and its cascade-linked visits/exams/doctor links",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration790(BrickMigration):
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

        campaigns = list(Campaign.select().where(Campaign.campaign_number.in_(_CAMPAIGN_NUMBERS)))
        if not campaigns:
            return
        campaign_ids = [c.id for c in campaigns]

        # Exams created against this campaign are linked via a text marker
        # ("CAMP:{campaign_id}|...") in reason_for_visit, not a real FK — so
        # they must be matched this way rather than by a fixed id list.
        for campaign_id in campaign_ids:
            Exam.delete().where(Exam.reason_for_visit % f"CAMP:{campaign_id}|%").execute()

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
