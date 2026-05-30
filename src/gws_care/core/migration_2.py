"""DB migration v0.21.0 — Add per-user app configuration table.

The gws_care_user_app_config table is created automatically at startup
via the is_table = True flag on UserAppConfig. This migration bumps the
version so the system records the schema change.
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.21.0",
    short_description="Add per-user app configuration table (page size, color theme)",
    db_manager=CareDbManager.get_instance(),
)
class Migration0210(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        pass  # Table created automatically at startup via UserAppConfig.is_table = True
