"""DB migration v0.10.2 — Add qr_token column to gws_care_patient and backfill."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.10.2",
    short_description="Add qr_token column to gws_care_patient (unique 12-char identifier for QR codes)",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration102(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        import uuid

        db = sql_migrator.migrator.database

        # 1. Add qr_token column (idempotent)
        db.execute_sql(
            "ALTER TABLE gws_care_patient "
            "ADD COLUMN IF NOT EXISTS qr_token VARCHAR(12) NULL DEFAULT NULL"
        )

        # 2. Add unique index (idempotent — MariaDB does not support partial indexes)
        db.execute_sql(
            "CREATE UNIQUE INDEX IF NOT EXISTS gws_care_patient_qr_token "
            "ON gws_care_patient (qr_token)"
        )

        # 3. Backfill existing patients that have no qr_token yet
        from gws_care.patient.patient import Patient
        patients_without_token = list(
            Patient.select(Patient.id).where(Patient.qr_token.is_null(True))
        )
        for p in patients_without_token:
            token = uuid.uuid4().hex[:12].upper()
            # Ensure uniqueness (extremely unlikely collision, but safe)
            while Patient.get_or_none(Patient.qr_token == token):
                token = uuid.uuid4().hex[:12].upper()
            Patient.update(qr_token=token).where(Patient.id == p.id).execute()
