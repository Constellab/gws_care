"""DB migration v0.42.0 — Add cancellation_reason column to gws_care_visit."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.42.0",
    short_description="Add cancellation_reason to gws_care_visit",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration330(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database
        db.execute_sql(
            "ALTER TABLE gws_care_visit ADD COLUMN IF NOT EXISTS cancellation_reason LONGTEXT NULL DEFAULT NULL"
        )
