"""Migration 0.54.0 — add work_doctor_interpretation column to gws_care_exam."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.54.0",
    short_description="Add work_doctor_interpretation column to gws_care_exam",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration450(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        db = sql_migrator.migrator.database
        db.execute_sql(
            "ALTER TABLE gws_care_exam ADD COLUMN IF NOT EXISTS work_doctor_interpretation LONGTEXT NULL DEFAULT NULL"
        )
