"""DB migration v0.29.0 — Drop detected_* columns from gws_care_uploaded_document."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.29.0",
    short_description="Drop detected_type, detected_date, detected_patient_name from uploaded_document",
    db_manager=CareDbManager.get_instance(),
)
class Migration0290(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        db = CareDbManager.get_instance().db
        db.execute_sql("ALTER TABLE gws_care_uploaded_document DROP COLUMN detected_type")
        db.execute_sql("ALTER TABLE gws_care_uploaded_document DROP COLUMN detected_date")
        db.execute_sql("ALTER TABLE gws_care_uploaded_document DROP COLUMN detected_patient_name")
