"""DB migration v0.35.0 — CampaignExam: assigned_doctor columns."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.35.0",
    short_description="CampaignExam: assigned_doctor_id, assigned_doctor_name columns",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration260(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database

        db.execute_sql(
            "ALTER TABLE gws_care_campaign_exam ADD COLUMN IF NOT EXISTS assigned_doctor_id VARCHAR(36) NULL"
        )
        db.execute_sql(
            "ALTER TABLE gws_care_campaign_exam ADD COLUMN IF NOT EXISTS assigned_doctor_name VARCHAR(300) NULL"
        )
