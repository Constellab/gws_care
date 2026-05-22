"""DB migration v0.19.0 — Baseline schema.

All tables are created by BaseModelService.create_database_tables on first
startup. This migration marks the current baseline version so the migration
system knows no further migrations need to run.
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.19.0",
    short_description="Baseline schema — all tables created at startup",
    db_manager=CareDbManager.get_instance(),
)
class Migration0190(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        pass  # Tables are created at startup; nothing to migrate on a fresh install
