"""Migration 0.51.0 — add work_doctor_id to Visit.

Lets a campaign visit be assigned both a PSC clinic doctor (existing
`doctor_id` field) and a specific "médecin du travail" (company doctor,
CareRole.MEDECIN_ENTREPRISE), instead of broadcasting transmissions to every
user with that role.
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.51.0",
    short_description="Add work_doctor_id to Visit for per-visit médecin du travail assignment",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration420(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        db = sql_migrator.migrator.database
        db.execute_sql(
            "ALTER TABLE gws_care_visit ADD COLUMN IF NOT EXISTS work_doctor_id VARCHAR(36) NULL"
        )
