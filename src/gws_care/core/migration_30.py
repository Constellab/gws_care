"""DB migration v0.39.0 — DoctorSchedule/DoctorUnavailableDay: drop old FK to gws_care_user, add FK to gws_care_medical_doctor.

Migration 0.38.0 migrated the data but did not update the MySQL FK constraints.
This migration completes the schema change.
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


def _fix_fk(db, table: str) -> None:
    # Drop every FK on doctor_id that still points to gws_care_user
    try:
        result = db.execute_sql("""
            SELECT CONSTRAINT_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME   = %s
              AND COLUMN_NAME  = 'doctor_id'
              AND REFERENCED_TABLE_NAME = 'gws_care_user'
        """, (table,))
        for (constraint_name,) in result.fetchall():
            db.execute_sql(f"ALTER TABLE `{table}` DROP FOREIGN KEY `{constraint_name}`")
    except Exception as exc:
        print(f"[migration_30] drop old FK on {table}: {exc}")

    # Remove rows that still don't match any MedicalDoctor (safety cleanup)
    try:
        db.execute_sql(f"""
            DELETE FROM `{table}`
            WHERE doctor_id NOT IN (SELECT id FROM gws_care_medical_doctor)
        """)
    except Exception as exc:
        print(f"[migration_30] cleanup orphaned rows in {table}: {exc}")

    # Add new FK pointing to gws_care_medical_doctor — idempotent
    constraint = f"{table}_fk_medical_doctor"
    try:
        db.execute_sql(f"ALTER TABLE `{table}` DROP FOREIGN KEY `{constraint}`")
    except Exception:
        pass
    try:
        db.execute_sql(f"""
            ALTER TABLE `{table}`
            ADD CONSTRAINT `{constraint}`
            FOREIGN KEY (`doctor_id`)
            REFERENCES `gws_care_medical_doctor`(`id`)
            ON DELETE CASCADE
        """)
    except Exception as exc:
        print(f"[migration_30] add new FK on {table}: {exc}")


@brick_migration(
    "0.39.0",
    short_description="DoctorSchedule: drop old gws_care_user FK, add gws_care_medical_doctor FK",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration300(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database
        _fix_fk(db, "gws_care_doctor_schedule")
        _fix_fk(db, "gws_care_doctor_unavailable_day")
