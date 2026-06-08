"""DB migration v0.24.0 — Remove username column from gws_care_smtp_config.

Username is now provided exclusively via the Constellab BASIC Credentials record
referenced by credentials_name. Storing it redundantly in SmtpConfig is unnecessary.
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.24.0",
    short_description="Remove redundant username column from gws_care_smtp_config",
    db_manager=CareDbManager.get_instance(),
)
class Migration0240(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        db = CareDbManager.get_instance().db
        db.execute_sql("""
            ALTER TABLE gws_care_smtp_config
            DROP COLUMN IF EXISTS username
        """)
