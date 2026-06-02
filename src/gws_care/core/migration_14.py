"""DB migration v0.10.4 — Add prescribed_exam_ref_ids JSON column to gws_care_exam."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.10.4",
    short_description="Add prescribed_exam_ref_ids LONGTEXT column to gws_care_exam (follow-up exam prescriptions)",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration104(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database

        db.execute_sql(
            "ALTER TABLE gws_care_exam "
            "ADD COLUMN IF NOT EXISTS prescribed_exam_ref_ids LONGTEXT NULL DEFAULT NULL"
        )
