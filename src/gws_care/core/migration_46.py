"""Migration 0.55.0 — wipe all visits, exams and related data for every patient.

Removes every visit, exam (with results, audit log, files), prescription,
certificate, doctor link and individual campaign for all patients, while
keeping patient records, accounts, companies, shared campaigns and
exam-type referentials intact.
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.55.0",
    short_description="Wipe all visits/exams/prescriptions/certificates/doctor links for all patients",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration460(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        # NEUTRALISED — this migration has been disabled to avoid accidental
        # data loss. Do not re-enable without an explicit user confirmation.
        pass
