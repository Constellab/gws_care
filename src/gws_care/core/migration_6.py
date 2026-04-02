"""DB migration v0.7.0 — Rename gws_care_company → gws_care_account and add billing_account_id columns."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.7.0",
    short_description="Rename company table to account; add billing_account_id to appointment and exam",
    db_manager=CareDbManager.get_instance(),
)
class Migration070(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database

        # Rename table
        db.execute_sql("RENAME TABLE gws_care_company TO gws_care_account")

        # Add billing_account_id to appointment (copy from company_id)
        db.execute_sql(
            "ALTER TABLE gws_care_appointment ADD COLUMN billing_account_id VARCHAR(36) NULL DEFAULT NULL"
        )
        db.execute_sql(
            "UPDATE gws_care_appointment SET billing_account_id = company_id WHERE company_id IS NOT NULL"
        )

        # Add billing_account_id to exam (copy from company_id)
        db.execute_sql(
            "ALTER TABLE gws_care_exam ADD COLUMN billing_account_id VARCHAR(36) NULL DEFAULT NULL"
        )
        db.execute_sql(
            "UPDATE gws_care_exam SET billing_account_id = company_id WHERE company_id IS NOT NULL"
        )
