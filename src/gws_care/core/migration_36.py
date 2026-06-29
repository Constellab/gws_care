"""Migration 0.45.0 — gender-specific reference thresholds on ExamParameter."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.45.0",
    short_description="Add M/F specific thresholds to exam_parameter",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration360(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        db = sql_migrator.migrator.database
        for col in (
            "ref_low_m", "ref_high_m", "critical_low_m", "critical_high_m",
            "ref_low_f", "ref_high_f", "critical_low_f", "critical_high_f",
        ):
            db.execute_sql(
                f"ALTER TABLE gws_care_exam_parameter"
                f" ADD COLUMN IF NOT EXISTS {col} DOUBLE NULL DEFAULT NULL"
            )
