"""DB migration v0.29.0 — Baseline schema.

All tables are created from model definitions on first startup.
This migration marks the current schema baseline so the migration system
knows no further migrations need to run on a fresh install.
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.29.0",
    short_description="Baseline schema — all tables created at startup",
    db_manager=CareDbManager.get_instance(),
)
class Migration0290(BrickMigration):
    @classmethod
    def migrate(
        cls, _sql_migrator: SqlMigrator, _from_version: Version, _to_version: Version
    ) -> None:
        pass  # Tables are created at startup; nothing to migrate on a fresh install
