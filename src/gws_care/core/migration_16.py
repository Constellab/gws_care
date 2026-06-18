"""DB migration v0.10.6 — Add follow_up_exam_ids JSON column to gws_care_exam."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.10.6",
    short_description="Add follow_up_exam_ids LONGTEXT column to gws_care_exam (actual Exam records created from prescribed follow-ups)",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration106(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database

        db.execute_sql(
            "ALTER TABLE gws_care_exam "
            "ADD COLUMN IF NOT EXISTS follow_up_exam_ids LONGTEXT NULL DEFAULT NULL"
        )
        db.execute_sql(
            "ALTER TABLE gws_care_exam "
            "ADD COLUMN IF NOT EXISTS is_follow_up TINYINT(1) NOT NULL DEFAULT 0"
        )
