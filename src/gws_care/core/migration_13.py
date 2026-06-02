"""DB migration v0.10.3 — Add specialty column to gws_care_user_role."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.10.3",
    short_description="Add specialty column to gws_care_user_role (doctor specialty: Cardiologue, etc.)",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration103(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database

        db.execute_sql(
            "ALTER TABLE gws_care_user_role "
            "ADD COLUMN IF NOT EXISTS specialty VARCHAR(100) NULL DEFAULT NULL"
        )
