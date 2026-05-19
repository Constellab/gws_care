"""DB migration v0.10.1 — Create gws_care_company table + add company_id to patient."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.10.1",
    short_description="Create Company table and add company_id FK to gws_care_patient",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration101(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database

        # 1. Create Company table (IF NOT EXISTS — idempotent)
        from gws_care.company.company import Company
        db.create_tables([Company], safe=True)

        # 2. Add company_id column to gws_care_patient (IF NOT EXISTS)
        db.execute_sql(
            "ALTER TABLE gws_care_patient "
            "ADD COLUMN IF NOT EXISTS company_id VARCHAR(36) NULL DEFAULT NULL"
        )
