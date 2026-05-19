"""DB migration v0.4.0 — Phase 5: UserCareRole table."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager
from gws_care.role.user_care_role import UserCareRole


@brick_migration(
    "0.4.0",
    short_description="Phase 5: UserCareRole table",
    db_manager=CareDbManager.get_instance(),
)
class Migration040(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database
        db.create_tables([UserCareRole], safe=True)
