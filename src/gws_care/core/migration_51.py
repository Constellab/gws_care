"""DB migration v0.60.0 — Add terrain_notes to CampaignPatient."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.60.0",
    short_description="Add terrain_notes field to CampaignPatient for on-site operator notes",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration510(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database
        db.execute_sql(
            "ALTER TABLE gws_care_program_patient "
            "ADD COLUMN IF NOT EXISTS terrain_notes TEXT NULL DEFAULT NULL"
        )
