"""DB migration v0.22.0 — Doctor-linked appointments.

Changes applied:
1. gws_care_medical_doctor  : ADD COLUMN user_id (FK → gws_care_user, nullable, unique)
2. gws_care_visit           : ADD COLUMN doctor_id (FK → gws_care_medical_doctor, nullable)
3. gws_care_visit           : ADD COLUMN appointment_mode VARCHAR(20) nullable
4. gws_care_visit           : ADD COLUMN patient_notes TEXT nullable
5. gws_care_notification_log: ADD COLUMN related_visit_id (FK → gws_care_visit, nullable)
6. gws_care_notification_log: DROP FK + DROP COLUMN related_appointment_id
7. DROP TABLE gws_care_appointment
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.22.0",
    short_description="Doctor-linked appointments: add doctor/mode/notes to Visit, remove Appointment table",
    db_manager=CareDbManager.get_instance(),
)
class Migration0220(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        db = CareDbManager.get_instance().db

        # 1. MedicalDoctor ← user_id
        db.execute_sql(
            "ALTER TABLE gws_care_medical_doctor "
            "ADD COLUMN IF NOT EXISTS user_id VARCHAR(36) NULL DEFAULT NULL, "
            "ADD UNIQUE INDEX IF NOT EXISTS idx_medical_doctor_user_id (user_id)"
        )

        # 2–4. Visit ← doctor_id, appointment_mode, patient_notes
        db.execute_sql(
            "ALTER TABLE gws_care_visit "
            "ADD COLUMN IF NOT EXISTS doctor_id VARCHAR(36) NULL DEFAULT NULL, "
            "ADD COLUMN IF NOT EXISTS appointment_mode VARCHAR(20) NULL DEFAULT NULL, "
            "ADD COLUMN IF NOT EXISTS patient_notes TEXT NULL DEFAULT NULL"
        )

        # 5. NotificationLog ← related_visit_id
        db.execute_sql(
            "ALTER TABLE gws_care_notification_log "
            "ADD COLUMN IF NOT EXISTS related_visit_id VARCHAR(36) NULL DEFAULT NULL"
        )

        # 6. Drop the FK constraint pointing to gws_care_appointment.
        #    The constraint name varies; discover it from information_schema.
        cursor = db.execute_sql(
            "SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE "
            "WHERE TABLE_SCHEMA = DATABASE() "
            "  AND TABLE_NAME = 'gws_care_notification_log' "
            "  AND COLUMN_NAME = 'related_appointment_id' "
            "  AND REFERENCED_TABLE_NAME = 'gws_care_appointment'"
        )
        for (constraint_name,) in cursor.fetchall():
            db.execute_sql(
                f"ALTER TABLE gws_care_notification_log DROP FOREIGN KEY `{constraint_name}`"
            )

        # Drop the column itself (IF NOT EXISTS guard via information_schema)
        cursor2 = db.execute_sql(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() "
            "  AND TABLE_NAME = 'gws_care_notification_log' "
            "  AND COLUMN_NAME = 'related_appointment_id'"
        )
        (col_count,) = cursor2.fetchone()
        if col_count:
            db.execute_sql(
                "ALTER TABLE gws_care_notification_log DROP COLUMN related_appointment_id"
            )

        # 7. Drop the Appointment table — no FK constraints remain at this point.
        db.execute_sql("DROP TABLE IF EXISTS gws_care_appointment")
