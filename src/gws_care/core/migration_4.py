"""DB migration v0.5.0 — Add document_type column to exam_file table."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration
from peewee import CharField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.exam.exam_file import ExamFile


@brick_migration(
    "0.5.0",
    short_description="Add document_type column to gws_care_exam_file",
    db_manager=CareDbManager.get_instance(),
)
class Migration050(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database
        db.create_tables([ExamFile], safe=True)
        sql_migrator.add_column_if_not_exists(ExamFile, CharField(null=True), "document_type")
        sql_migrator.migrate()
