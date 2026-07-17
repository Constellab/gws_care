"""DB migration v0.68.7 — Remove test campaigns "tes_subbb" and "subsss".

One-off cleanup of two test campaigns (account "Subway France") created
while testing the lab-validation workflow fixes, along with their
cascade-linked visits, exam configs, doctor assignments, and campaign-linked
Exam records (matched by the "CAMP:{campaign_id}|" reason_for_visit marker,
rather than a hardcoded exam ID list, since any number of exams may have
been dispatched/entered against them).

Looked up by campaign_number (PRG-ODYPAL00 / PRG-LOB7K9MU) rather than a
hardcoded id, since the id wasn't available when this migration was
written — a no-op on any install where these campaign_numbers don't exist.
Follows the same explicit-delete-order pattern as migration_65.py/
migration_67.py/migration_68.py/migration_69.py rather than relying on
DB-level FK cascade for the campaign/visit tables.
"""

from gws_care.core.care_db_manager import CareDbManager
from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

_CAMPAIGN_NUMBERS = [
    "PRG-ODYPAL00",  # "tes_subbb"
    "PRG-LOB7K9MU",  # "subsss"
]


@brick_migration(
    "0.68.7",
    short_description="Remove 2 test campaigns and their cascade-linked visits/exams/doctor links",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration710(BrickMigration):
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

        # Exams created against these campaigns are linked via a text marker
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
