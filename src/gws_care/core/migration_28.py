"""DB migration v0.37.0 — MedicalDoctor: status_reason column."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.37.0",
    short_description="MedicalDoctor: add status_reason column",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration280(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database
        db.execute_sql(
            "ALTER TABLE gws_care_medical_doctor ADD COLUMN IF NOT EXISTS status_reason VARCHAR(1000) NULL"
        )
