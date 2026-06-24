"""DB migration v0.32.0 — Patient: archive support."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.32.0",
    short_description="Patient: is_archived, archived_reason, archived_at columns",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration230(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database

        db.execute_sql(
            "ALTER TABLE gws_care_patient ADD COLUMN IF NOT EXISTS is_archived TINYINT(1) NOT NULL DEFAULT 0"
        )
        db.execute_sql(
            "ALTER TABLE gws_care_patient ADD COLUMN IF NOT EXISTS archived_reason TEXT NULL"
        )
        db.execute_sql(
            "ALTER TABLE gws_care_patient ADD COLUMN IF NOT EXISTS archived_at VARCHAR(50) NULL"
        )
