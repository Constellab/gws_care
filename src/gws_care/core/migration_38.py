"""Migration 0.47.0 — create gws_care_exam_audit_entry table.

Tracks unusual exam actions (add/remove a test, modify a value, lab
transmission) separately from Exam.interpretation.
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.47.0",
    short_description="Create ExamAuditEntry table for per-exam action history",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration380(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        from gws_care.exam.exam_audit_entry import ExamAuditEntry

        db = sql_migrator.migrator.database
        db.create_tables([ExamAuditEntry], safe=True)
