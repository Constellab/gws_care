"""DB migration v0.9.0 — Add lab_results JSON column to exam table."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.9.0",
    short_description="Add lab_results column to exam table for dynamic laboratory results",
    db_manager=CareDbManager.get_instance(),
)
class Migration090(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database
        db.execute_sql("ALTER TABLE gws_care_exam ADD COLUMN IF NOT EXISTS lab_results LONGTEXT NULL DEFAULT NULL")
