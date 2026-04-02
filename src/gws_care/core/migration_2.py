"""DB migration v0.3.0 — Phase 4: Appointment table."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.appointment.appointment import Appointment
from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.3.0",
    short_description="Phase 4: Appointment table",
    db_manager=CareDbManager.get_instance(),
)
class Migration030(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        sql_migrator.create_table_if_not_exists(Appointment)
        sql_migrator.migrate()
