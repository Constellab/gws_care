"""DB migration v0.20.0 — consolidate all incremental schema changes.

All the ALTER TABLE / CREATE TABLE operations that were previously run on every
Reflex app start (via _ensure_care_db_tables in care_app.py) are moved here so
they run exactly once through the standard brick-migration system.

Every operation is guarded by column_exists / table_exists checks so this
migration is safe to run against a database that already has all the columns
(i.e. existing production installations).
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.20.0",
    short_description="Consolidate all incremental schema changes into brick migrations",
    db_manager=CareDbManager.get_instance(),
)
class Migration0200(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        pass  # Tables are created at startup; nothing to migrate on a fresh install
