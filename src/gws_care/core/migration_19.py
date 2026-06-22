"""DB migration v0.10.9 — Add all missing columns to prescription and prescription_line tables."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.10.9",
    short_description="Add missing FK and field columns to gws_care_prescription and prescription_line",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration109(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database

        # ── gws_care_prescription ────────────────────────────────────────────
        stmts = [
            # FK columns (Peewee appends _id to the field name)
            "ALTER TABLE gws_care_prescription ADD COLUMN IF NOT EXISTS patient_id VARCHAR(36) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_prescription ADD COLUMN IF NOT EXISTS consultation_id VARCHAR(36) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_prescription ADD COLUMN IF NOT EXISTS prescribing_doctor_id VARCHAR(36) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_prescription ADD COLUMN IF NOT EXISTS created_by_id VARCHAR(36) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_prescription ADD COLUMN IF NOT EXISTS last_modified_by_id VARCHAR(36) NULL DEFAULT NULL",
            # Regular fields
            "ALTER TABLE gws_care_prescription ADD COLUMN IF NOT EXISTS prescription_type VARCHAR(20) NOT NULL DEFAULT 'DRUG'",
            "ALTER TABLE gws_care_prescription ADD COLUMN IF NOT EXISTS issued_at DATE NULL DEFAULT NULL",
            "ALTER TABLE gws_care_prescription ADD COLUMN IF NOT EXISTS valid_until DATE NULL DEFAULT NULL",
            "ALTER TABLE gws_care_prescription ADD COLUMN IF NOT EXISTS is_renewable TINYINT(1) NOT NULL DEFAULT 0",
            "ALTER TABLE gws_care_prescription ADD COLUMN IF NOT EXISTS renewal_count INT NOT NULL DEFAULT 0",
            "ALTER TABLE gws_care_prescription ADD COLUMN IF NOT EXISTS general_instructions LONGTEXT NULL DEFAULT NULL",
        ]

        # ── gws_care_prescription_line ───────────────────────────────────────
        stmts += [
            "ALTER TABLE gws_care_prescription_line ADD COLUMN IF NOT EXISTS prescription_id VARCHAR(36) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_prescription_line ADD COLUMN IF NOT EXISTS created_by_id VARCHAR(36) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_prescription_line ADD COLUMN IF NOT EXISTS last_modified_by_id VARCHAR(36) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_prescription_line ADD COLUMN IF NOT EXISTS item_name VARCHAR(300) NOT NULL DEFAULT ''",
            "ALTER TABLE gws_care_prescription_line ADD COLUMN IF NOT EXISTS dosage VARCHAR(300) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_prescription_line ADD COLUMN IF NOT EXISTS duration VARCHAR(200) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_prescription_line ADD COLUMN IF NOT EXISTS quantity VARCHAR(100) NULL DEFAULT NULL",
            "ALTER TABLE gws_care_prescription_line ADD COLUMN IF NOT EXISTS instructions LONGTEXT NULL DEFAULT NULL",
            "ALTER TABLE gws_care_prescription_line ADD COLUMN IF NOT EXISTS display_order INT NOT NULL DEFAULT 0",
        ]

        for stmt in stmts:
            db.execute_sql(stmt)
