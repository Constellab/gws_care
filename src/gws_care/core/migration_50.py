"""DB migration v0.59.0 — Campaign patient workflow + ExamTypeRef lab flag.

- Adds requires_lab_validation to gws_care_exam_type_ref
- Adds treating_doctor_transmitted_at + missing medical workflow columns to gws_care_program_patient
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.59.0",
    short_description="Add requires_lab_validation to ExamTypeRef and treating doctor transmission tracking",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration500(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database

        # Add requires_lab_validation to ExamTypeRef (True = lab needed, False = on-site)
        db.execute_sql(
            "ALTER TABLE gws_care_exam_type_ref "
            "ADD COLUMN IF NOT EXISTS requires_lab_validation BOOLEAN NOT NULL DEFAULT TRUE"
        )

        # Ensure medical workflow columns exist in gws_care_program_patient (idempotent)
        db.execute_sql(
            "ALTER TABLE gws_care_program_patient "
            "ADD COLUMN IF NOT EXISTS medical_status VARCHAR(30) NOT NULL DEFAULT 'PENDING'"
        )
        db.execute_sql(
            "ALTER TABLE gws_care_program_patient "
            "ADD COLUMN IF NOT EXISTS psc_notes TEXT NULL DEFAULT NULL"
        )
        db.execute_sql(
            "ALTER TABLE gws_care_program_patient "
            "ADD COLUMN IF NOT EXISTS enterprise_notes TEXT NULL DEFAULT NULL"
        )
        db.execute_sql(
            "ALTER TABLE gws_care_program_patient "
            "ADD COLUMN IF NOT EXISTS patient_message TEXT NULL DEFAULT NULL"
        )
        db.execute_sql(
            "ALTER TABLE gws_care_program_patient "
            "ADD COLUMN IF NOT EXISTS psc_validated_at DATETIME NULL DEFAULT NULL"
        )
        db.execute_sql(
            "ALTER TABLE gws_care_program_patient "
            "ADD COLUMN IF NOT EXISTS enterprise_validated_at DATETIME NULL DEFAULT NULL"
        )
        db.execute_sql(
            "ALTER TABLE gws_care_program_patient "
            "ADD COLUMN IF NOT EXISTS published_at DATETIME NULL DEFAULT NULL"
        )
        # New: tracking transmission to treating doctor
        db.execute_sql(
            "ALTER TABLE gws_care_program_patient "
            "ADD COLUMN IF NOT EXISTS treating_doctor_transmitted_at DATETIME NULL DEFAULT NULL"
        )

        # One-time data cleanup: remove test campaign "Awarness_2026" (and any spelling variant)
        try:
            db.execute_sql(
                "DELETE ced FROM gws_care_campaign_exam_doctor ced "
                "INNER JOIN gws_care_campaign_exam ce ON ced.campaign_exam_id = ce.id "
                "INNER JOIN gws_care_medical_program p ON p.id = ce.campaign_id "
                "WHERE p.name LIKE 'Awarness_2026%' OR p.name LIKE 'Awareness_2026%'"
            )
            db.execute_sql(
                "DELETE FROM gws_care_campaign_exam WHERE campaign_id IN "
                "(SELECT id FROM (SELECT id FROM gws_care_medical_program "
                " WHERE name LIKE 'Awarness_2026%' OR name LIKE 'Awareness_2026%') AS t)"
            )
            db.execute_sql(
                "DELETE FROM gws_care_campaign_doctor WHERE campaign_id IN "
                "(SELECT id FROM (SELECT id FROM gws_care_medical_program "
                " WHERE name LIKE 'Awarness_2026%' OR name LIKE 'Awareness_2026%') AS t)"
            )
            db.execute_sql(
                "DELETE FROM gws_care_program_patient WHERE program_id IN "
                "(SELECT id FROM (SELECT id FROM gws_care_medical_program "
                " WHERE name LIKE 'Awarness_2026%' OR name LIKE 'Awareness_2026%') AS t)"
            )
            db.execute_sql(
                "DELETE FROM gws_care_visit WHERE program_id IN "
                "(SELECT id FROM (SELECT id FROM gws_care_medical_program "
                " WHERE name LIKE 'Awarness_2026%' OR name LIKE 'Awareness_2026%') AS t)"
            )
            db.execute_sql(
                "DELETE FROM gws_care_medical_program "
                "WHERE name LIKE 'Awarness_2026%' OR name LIKE 'Awareness_2026%'"
            )
        except Exception:
            pass  # Campaign not found or already deleted — safe to ignore
