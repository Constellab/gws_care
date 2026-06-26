"""DB migration v0.41.0 — Ensure consultation/appointment columns exist on Visit table.

The Visit table was created in migration_20 (v0.29.0). If the appointment-booking
columns were added to the model after that migration ran, they would be absent from
the database schema. This migration adds them with IF NOT EXISTS to be safe.
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.41.0",
    short_description="Ensure appointment-booking columns exist on gws_care_visit",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration320(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database
        stmts = [
            # consultation visit lifecycle
            "ALTER TABLE gws_care_visit ADD COLUMN IF NOT EXISTS consultation_visit_status VARCHAR(255) NULL DEFAULT NULL",
            # appointment booking fields
            "ALTER TABLE gws_care_visit ADD COLUMN IF NOT EXISTS doctor_id VARCHAR(36) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_visit ADD COLUMN IF NOT EXISTS appointment_mode VARCHAR(255) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_visit ADD COLUMN IF NOT EXISTS patient_notes LONGTEXT NULL DEFAULT NULL",
            "ALTER TABLE gws_care_visit ADD COLUMN IF NOT EXISTS appointment_address LONGTEXT NULL DEFAULT NULL",
        ]
        for stmt in stmts:
            db.execute_sql(stmt)
