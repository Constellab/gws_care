"""DB migration v0.10.8 — Add missing columns to existing tables."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.10.8",
    short_description="Add primary_physician_name/phone to patient; fix prescription schema",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration108(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database

        # Patient: physician fields added to model but never migrated
        db.execute_sql(
            "ALTER TABLE gws_care_patient "
            "ADD COLUMN IF NOT EXISTS primary_physician_name VARCHAR(255) NULL DEFAULT NULL"
        )
        db.execute_sql(
            "ALTER TABLE gws_care_patient "
            "ADD COLUMN IF NOT EXISTS primary_physician_phone VARCHAR(50) NULL DEFAULT NULL"
        )

        # Prescription: prescribing_doctor_id may be missing if the table existed
        # in a partial state before migration_17 ran (safe=True skips recreation)
        db.execute_sql(
            "ALTER TABLE gws_care_prescription "
            "ADD COLUMN IF NOT EXISTS prescribing_doctor_id VARCHAR(36) NULL DEFAULT NULL"
        )
