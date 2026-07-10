"""DB migration v0.67.0 — Add organization info fields to CareAppConfig."""

from gws_care.core.care_db_manager import CareDbManager
from gws_core import BrickMigration, SqlMigrator, Version, brick_migration


@brick_migration(
    "0.67.0",
    short_description="Add organization name, acronym, address, SIRET, phone, email to app config",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration630(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        db = sql_migrator.migrator.database
        table = "gws_care_app_config"
        try:
            db.execute_sql(
                f"ALTER TABLE `{table}` "
                f"ADD COLUMN IF NOT EXISTS `org_name` VARCHAR(200) NOT NULL DEFAULT '', "
                f"ADD COLUMN IF NOT EXISTS `org_acronym` VARCHAR(20) NOT NULL DEFAULT 'PSC', "
                f"ADD COLUMN IF NOT EXISTS `org_siret` VARCHAR(50) NOT NULL DEFAULT '', "
                f"ADD COLUMN IF NOT EXISTS `org_phone` VARCHAR(50) NOT NULL DEFAULT '', "
                f"ADD COLUMN IF NOT EXISTS `org_email` VARCHAR(200) NOT NULL DEFAULT '', "
                f"ADD COLUMN IF NOT EXISTS `org_address` VARCHAR(500) NOT NULL DEFAULT '', "
                f"ADD COLUMN IF NOT EXISTS `org_address_complement` VARCHAR(500) NOT NULL DEFAULT '', "
                f"ADD COLUMN IF NOT EXISTS `org_postal_code` VARCHAR(20) NOT NULL DEFAULT '', "
                f"ADD COLUMN IF NOT EXISTS `org_city` VARCHAR(100) NOT NULL DEFAULT '', "
                f"ADD COLUMN IF NOT EXISTS `org_country` VARCHAR(100) NOT NULL DEFAULT 'France'"
            )
        except Exception:
            pass
