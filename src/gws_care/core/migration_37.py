"""Migration 0.46.0 — motif de visite + antécédents au niveau de la consultation (Visit)."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.46.0",
    short_description="Add reason_for_visit and medical_history to Visit (consultation-level)",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration370(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        db = sql_migrator.migrator.database
        for col in ("reason_for_visit", "medical_history"):
            db.execute_sql(
                f"ALTER TABLE gws_care_visit ADD COLUMN IF NOT EXISTS {col} LONGTEXT NULL DEFAULT NULL"
            )
