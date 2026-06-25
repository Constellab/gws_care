"""DB migration v0.34.0 — ExamParameter: is_active column."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.34.0",
    short_description="ExamParameter: is_active column",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration250(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database

        db.execute_sql(
            "ALTER TABLE gws_care_exam_parameter ADD COLUMN IF NOT EXISTS is_active TINYINT(1) NOT NULL DEFAULT 1"
        )
