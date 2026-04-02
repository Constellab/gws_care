"""DB migration v0.6.0 — Add company_id column to patient table."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager
from gws_care.patient.patient import Patient


@brick_migration(
    "0.6.0",
    short_description="Add company_id FK column to gws_care_patient",
    db_manager=CareDbManager.get_instance(),
)
class Migration060(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        # Use raw SQL for FK column — playhouse MySQLMigrator requires an explicit
        # `field=` argument for ForeignKeyField which is not supported this way.
        if not Patient.column_exists("company_id"):
            sql_migrator.migrator.database.execute_sql(
                "ALTER TABLE gws_care_patient ADD COLUMN company_id VARCHAR(36) NULL DEFAULT NULL"
            )
