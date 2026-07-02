"""Migration 0.57.0 — create gws_care_campaign_exam_doctor (M2M: CampaignExam ↔ MedicalDoctor).

Allows multiple doctors to be assigned to a single exam type within a campaign.
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.57.0",
    short_description="Add campaign_exam_doctor M2M table (multi-doctor per exam)",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration480(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        from gws_care.campaign.campaign_exam_doctor import CampaignExamDoctor
        db = sql_migrator.migrator.database
        db.create_tables([CampaignExamDoctor], safe=True)
