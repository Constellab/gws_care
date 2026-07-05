"""DB migration v0.63.0 — Delete all campaigns and all related data."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.63.0",
    short_description="Delete all campaigns and all related data",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration540(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database
        try:
            db.execute_sql("DELETE FROM gws_care_campaign_exam_doctor")
            db.execute_sql("DELETE FROM gws_care_campaign_exam")
            db.execute_sql("DELETE FROM gws_care_campaign_doctor")
            db.execute_sql("DELETE FROM gws_care_program_patient")
            db.execute_sql("DELETE FROM gws_care_visit")
            db.execute_sql("DELETE FROM gws_care_medical_program")
        except Exception:
            pass
