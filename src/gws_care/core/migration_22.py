"""DB migration v0.31.0 — Patient: is_draft flag."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.31.0",
    short_description="Patient: is_draft flag for incomplete records",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration220(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database

        db.execute_sql(
            "ALTER TABLE gws_care_patient ADD COLUMN IF NOT EXISTS is_draft TINYINT(1) NOT NULL DEFAULT 0"
        )
