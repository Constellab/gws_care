"""DB migration v0.68.2 — Add psc_notified_at to gws_care_program_patient.

Tracks the explicit hand-off from lab validation to the internal
interpreting doctor (distinct from psc_validated_at, which marks when that
doctor has finished their own interpretation).
"""

from gws_care.core.care_db_manager import CareDbManager
from gws_core import BrickMigration, SqlMigrator, Version, brick_migration


@brick_migration(
    "0.68.2",
    short_description="Add psc_notified_at (lab-to-doctor hand-off timestamp) to gws_care_program_patient",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration660(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        db = sql_migrator.migrator.database
        db.execute_sql(
            "ALTER TABLE gws_care_program_patient "
            "ADD COLUMN IF NOT EXISTS psc_notified_at DATETIME NULL DEFAULT NULL"
        )
