"""DB migration v0.38.0 — DoctorSchedule/DoctorUnavailableDay: doctor FK now targets MedicalDoctor.

Previously, doctor_id stored User.id; it now stores MedicalDoctor.id so that
doctors without a platform account can still have schedules and unavailability.

Schema changes:
  1. Drop old FK constraint (REFERENCES gws_care_user)
  2. Migrate existing data: User.id → MedicalDoctor.id
  3. Add new FK constraint (REFERENCES gws_care_medical_doctor)
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


def _drop_fk_to_user(db, table: str) -> None:
    """Drop any FK on doctor_id that still references gws_care_user."""
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
        print(f"[migration_29] could not drop old FK on {table}: {exc}")


def _add_fk_to_medical_doctor(db, table: str) -> None:
    """Add FK on doctor_id pointing to gws_care_medical_doctor — idempotent."""
    constraint = f"{table}_fk_medical_doctor"
    try:
        # Drop if already exists (re-entrant safety)
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
        print(f"[migration_29] could not add new FK on {table}: {exc}")


@brick_migration(
    "0.38.0",
    short_description="DoctorSchedule: doctor FK migrated from User.id to MedicalDoctor.id",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration290(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database

        for table in ("gws_care_doctor_schedule", "gws_care_doctor_unavailable_day"):
            # 1. Drop old FK so we can freely update doctor_id values
            _drop_fk_to_user(db, table)

            # 2. Re-map existing rows: old doctor_id (User.id) → new MedicalDoctor.id
            db.execute_sql(f"""
                UPDATE `{table}`
                SET doctor_id = (
                    SELECT id FROM gws_care_medical_doctor
                    WHERE gws_care_medical_doctor.user_id = `{table}`.doctor_id
                    LIMIT 1
                )
                WHERE doctor_id IN (
                    SELECT user_id FROM gws_care_medical_doctor WHERE user_id IS NOT NULL
                )
            """)

            # 3. Remove rows that could not be mapped (no matching MedicalDoctor)
            db.execute_sql(f"""
                DELETE FROM `{table}`
                WHERE doctor_id NOT IN (SELECT id FROM gws_care_medical_doctor)
            """)

            # 4. Add new FK pointing to gws_care_medical_doctor
            _add_fk_to_medical_doctor(db, table)
