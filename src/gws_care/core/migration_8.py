"""DB migration v0.27.0 — Rename ExamStatus values and create exam workflow table."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.27.0",
    short_description="Rename exam status values (draft→todo, pending→in_progress_interpretation, interpreted→done) and create exam workflow history table",
    db_manager=CareDbManager.get_instance(),
)
class Migration0270(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        db = CareDbManager.get_instance().db
        # Rename existing status values in place
        db.execute_sql("UPDATE gws_care_exam SET status = 'todo' WHERE status = 'draft'")
        db.execute_sql("UPDATE gws_care_exam SET status = 'in_progress_interpretation' WHERE status = 'pending'")
        db.execute_sql("UPDATE gws_care_exam SET status = 'done' WHERE status = 'interpreted'")
        # Create exam validation workflow history table
        db.execute_sql("""
            CREATE TABLE IF NOT EXISTS gws_care_exam_validation_workflow (
                id VARCHAR(36) NOT NULL PRIMARY KEY,
                exam_id VARCHAR(36) NOT NULL REFERENCES gws_care_exam(id) ON DELETE CASCADE,
                step VARCHAR(50) NOT NULL,
                reached_by_id VARCHAR(36) REFERENCES gws_care_user(id) ON DELETE SET NULL,
                reached_at DATETIME NOT NULL
            )
        """)
