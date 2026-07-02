"""Migration 0.58.0 — add location_mode column to gws_care_campaign_exam.

Stores where / how each exam type takes place within a campaign
(AT_WORK, HOSPITAL, VISIO, AT_HOME, ADDRESS).
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.58.0",
    short_description="Add location_mode to campaign_exam (where/how each exam takes place)",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration490(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        db = sql_migrator.migrator.database
        db.execute_sql(
            "ALTER TABLE gws_care_campaign_exam "
            "ADD COLUMN IF NOT EXISTS location_mode VARCHAR(20) NULL DEFAULT NULL"
        )
