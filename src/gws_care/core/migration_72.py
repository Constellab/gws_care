"""DB migration v0.68.8 — Remove test campaigns "tes_subbb" and "subsss" (retry).

migration_71.py targeted these same 2 campaigns but with two mistyped
campaign_number values (letter "O" vs digit "0" confused in both — a real
risk when reading these off a screenshot), so it silently matched nothing
and both campaigns are still present. This migration retries with the
corrected numbers, and additionally matches by campaign name (unambiguous
lowercase ASCII, no O/0 risk) as a second, independent condition — so a
future typo in either identifier alone still finds the right rows.

migration_71.py is left untouched (a harmless no-op on this install) rather
than edited after the fact, per this brick's convention of never rewriting
already-applied migrations.

Same cascade-linked visits/exam configs/doctor assignments/campaign-linked
Exam records (matched by the "CAMP:{campaign_id}|" reason_for_visit marker)
and explicit delete-order pattern as migration_65.py/67.py/68.py/69.py/71.py.
"""

from gws_care.core.care_db_manager import CareDbManager
from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

_CAMPAIGN_NUMBERS = [
    "PRG-ODYPALO0",  # "tes_subbb" — corrected: letter O then digit 0
    "PRG-L0B7K9MU",  # "subsss" — corrected: digit 0 as 2nd character
]

_CAMPAIGN_NAMES = [
    "tes_subbb",
    "subsss",
]


@brick_migration(
    "0.68.8",
    short_description="Retry removal of 2 test campaigns with corrected identifiers",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration720(BrickMigration):
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

        campaigns = list(
            Campaign.select().where(
                Campaign.campaign_number.in_(_CAMPAIGN_NUMBERS) | Campaign.name.in_(_CAMPAIGN_NAMES)
            )
        )
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
