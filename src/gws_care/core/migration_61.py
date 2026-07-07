"""DB migration v0.65.5 — Add interpretation label fields to exam_parameter."""

from gws_care.core.care_db_manager import CareDbManager
from gws_core import BrickMigration, SqlMigrator, Version, brick_migration


@brick_migration(
    "0.65.5",
    short_description="Add interpretation label fields to exam_parameter",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration610(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        db = sql_migrator.migrator.database
        for col in ("label_normal", "label_low", "label_high", "label_critical_low", "label_critical_high"):
            try:
                db.execute_sql(
                    f"ALTER TABLE gws_care_exam_parameter "
                    f"ADD COLUMN IF NOT EXISTS {col} LONGTEXT NULL DEFAULT NULL"
                )
            except Exception:
                pass
