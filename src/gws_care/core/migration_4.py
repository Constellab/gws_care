"""DB migration v0.23.0 — PatientDoctor many-to-many.

Changes applied:
1. CREATE TABLE gws_care_patient_doctor
2. Migrate existing primary_physician_id data → PatientDoctor rows (is_referent=True)
3. DROP COLUMNS primary_physician_id, primary_physician_name, primary_physician_phone
   from gws_care_patient
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.23.0",
    short_description="PatientDoctor many-to-many: multiple doctors per patient with referent flag",
    db_manager=CareDbManager.get_instance(),
)
class Migration0230(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        db = CareDbManager.get_instance().db

        # 1. Create the PatientDoctor junction table
        db.execute_sql("""
            CREATE TABLE IF NOT EXISTS gws_care_patient_doctor (
                id VARCHAR(36) NOT NULL PRIMARY KEY,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_modified_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                created_by_id VARCHAR(36) NULL,
                last_modified_by_id VARCHAR(36) NULL,
                patient_id VARCHAR(36) NOT NULL,
                doctor_id VARCHAR(36) NOT NULL,
                is_referent TINYINT(1) NOT NULL DEFAULT 0,
                UNIQUE KEY uq_patient_doctor (patient_id, doctor_id),
                CONSTRAINT fk_pd_patient FOREIGN KEY (patient_id)
                    REFERENCES gws_care_patient (id) ON DELETE CASCADE,
                CONSTRAINT fk_pd_doctor FOREIGN KEY (doctor_id)
                    REFERENCES gws_care_medical_doctor (id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # 2. Migrate existing primary_physician_id data
        #    For every patient with a non-null primary_physician_id that still exists
        #    in gws_care_medical_doctor, insert a PatientDoctor row (is_referent=True).
        cursor = db.execute_sql("""
            SELECT p.id AS patient_id, p.primary_physician_id AS doctor_id
            FROM gws_care_patient p
            INNER JOIN gws_care_medical_doctor d ON d.id = p.primary_physician_id
            WHERE p.primary_physician_id IS NOT NULL
              AND p.primary_physician_id != ''
        """)
        rows = cursor.fetchall()
        for patient_id, doctor_id in rows:
            import uuid as _uuid
            new_id = str(_uuid.uuid4())
            db.execute_sql(
                "INSERT IGNORE INTO gws_care_patient_doctor "
                "(id, patient_id, doctor_id, is_referent) VALUES (%s, %s, %s, 1)",
                (new_id, patient_id, doctor_id)
            )

        # 3. Drop the legacy physician columns from gws_care_patient
        for col in ("primary_physician_id", "primary_physician_name", "primary_physician_phone"):
            cursor2 = db.execute_sql(
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() "
                "  AND TABLE_NAME = 'gws_care_patient' "
                f"  AND COLUMN_NAME = '{col}'"
            )
            (exists,) = cursor2.fetchone()
            if exists:
                # Drop FK if any
                fk_cursor = db.execute_sql(
                    "SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE "
                    "WHERE TABLE_SCHEMA = DATABASE() "
                    "  AND TABLE_NAME = 'gws_care_patient' "
                    f"  AND COLUMN_NAME = '{col}' "
                    "  AND REFERENCED_TABLE_NAME IS NOT NULL"
                )
                for (fk_name,) in fk_cursor.fetchall():
                    db.execute_sql(
                        f"ALTER TABLE gws_care_patient DROP FOREIGN KEY `{fk_name}`"
                    )
                db.execute_sql(
                    f"ALTER TABLE gws_care_patient DROP COLUMN `{col}`"
                )
