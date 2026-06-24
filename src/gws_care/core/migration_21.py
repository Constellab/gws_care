"""DB migration v0.30.0 — Address complement/country on patient, department on ExamTypeRef."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.30.0",
    short_description="Patient: address_complement + country; ExamTypeRef: department",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration210(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database

        stmts = [
            "ALTER TABLE gws_care_patient ADD COLUMN IF NOT EXISTS address_complement LONGTEXT NULL DEFAULT NULL",
            "ALTER TABLE gws_care_patient ADD COLUMN IF NOT EXISTS country VARCHAR(100) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_exam_type_ref ADD COLUMN IF NOT EXISTS department VARCHAR(100) NULL DEFAULT NULL",
            # archive_reason may have been missed in migration_20 if the server was already at 0.29.0
            "ALTER TABLE gws_care_medical_program ADD COLUMN IF NOT EXISTS archive_reason LONGTEXT NULL DEFAULT NULL",
        ]
        for stmt in stmts:
            db.execute_sql(stmt)
