"""DB migration v0.33.0 — ExamTypeRef: deactivation_reason column."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.33.0",
    short_description="ExamTypeRef: deactivation_reason column",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration240(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database

        db.execute_sql(
            "ALTER TABLE gws_care_exam_type_ref ADD COLUMN IF NOT EXISTS deactivation_reason TEXT NULL"
        )
