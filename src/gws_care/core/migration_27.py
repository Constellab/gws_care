"""DB migration v0.36.0 — MedicalDoctor: is_archived column."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.36.0",
    short_description="MedicalDoctor: add is_archived column",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration270(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database
        db.execute_sql(
            "ALTER TABLE gws_care_medical_doctor ADD COLUMN IF NOT EXISTS is_archived BOOLEAN NOT NULL DEFAULT FALSE"
        )
