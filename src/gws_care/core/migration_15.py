
from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.10.5",
    short_description="Add company_id VARCHAR(36) column to gws_care_account (Entreprise → Compte de facturation link)",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration105(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database

        db.execute_sql(
            "ALTER TABLE gws_care_account "
            "ADD COLUMN IF NOT EXISTS company_id VARCHAR(36) NULL DEFAULT NULL"
        )
