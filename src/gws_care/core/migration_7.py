"""DB migration v0.26.0 — Drop unused conclusion column from gws_care_exam."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.26.0",
    short_description="Drop unused conclusion column from gws_care_exam (replaced by interpretation)",
    db_manager=CareDbManager.get_instance(),
)
class Migration0260(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        db = CareDbManager.get_instance().db
        db.execute_sql("ALTER TABLE gws_care_exam DROP COLUMN IF EXISTS conclusion")
