from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.certificate.medical_certificate import MedicalCertificate
from gws_care.core.care_db_manager import CareDbManager
from gws_care.exam.exam import Exam
from gws_care.exam.exam_result import ExamResult


@brick_migration(
    "0.2.0",
    short_description="Phase 3: Exam, ExamResult, MedicalCertificate tables",
    db_manager=CareDbManager.get_instance(),
)
class Migration020(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        sql_migrator.create_table_if_not_exists(Exam)
        sql_migrator.create_table_if_not_exists(ExamResult)
        sql_migrator.create_table_if_not_exists(MedicalCertificate)
        sql_migrator.migrate()
