"""DB migration v0.8.0 — Add medical sections to exam table."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.8.0",
    short_description="Add medical sections to exam: reason_for_visit, medical_history, physical examination fields, conclusion",
    db_manager=CareDbManager.get_instance(),
)
class Migration080(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database

        db.execute_sql("ALTER TABLE gws_care_exam ADD COLUMN reason_for_visit TEXT NULL DEFAULT NULL")
        db.execute_sql("ALTER TABLE gws_care_exam ADD COLUMN medical_history TEXT NULL DEFAULT NULL")
        db.execute_sql("ALTER TABLE gws_care_exam ADD COLUMN weight DOUBLE NULL DEFAULT NULL")
        db.execute_sql("ALTER TABLE gws_care_exam ADD COLUMN height DOUBLE NULL DEFAULT NULL")
        db.execute_sql("ALTER TABLE gws_care_exam ADD COLUMN bmi DOUBLE NULL DEFAULT NULL")
        db.execute_sql("ALTER TABLE gws_care_exam ADD COLUMN blood_pressure VARCHAR(50) NULL DEFAULT NULL")
        db.execute_sql("ALTER TABLE gws_care_exam ADD COLUMN heart_rate DOUBLE NULL DEFAULT NULL")
        db.execute_sql("ALTER TABLE gws_care_exam ADD COLUMN temperature DOUBLE NULL DEFAULT NULL")
        db.execute_sql("ALTER TABLE gws_care_exam ADD COLUMN conclusion TEXT NULL DEFAULT NULL")
