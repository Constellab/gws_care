"""DB migration v0.28.0 — New appointment modes, appointment address fields, patient address fields."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.28.0",
    short_description="Rename onsite→at_work appointment mode; add appointment_address to visits",
    db_manager=CareDbManager.get_instance(),
)
class Migration0280(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        db = CareDbManager.get_instance().db
        # Rename existing onsite mode to at_work
        db.execute_sql("UPDATE gws_care_visit SET appointment_mode = 'at_work' WHERE appointment_mode = 'onsite'")
        # Add appointment address field to visits
        db.execute_sql("ALTER TABLE gws_care_visit ADD COLUMN appointment_address TEXT")
