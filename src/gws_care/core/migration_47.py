"""Migration 0.56.0 — fix gws_care_campaign_exam FK to point to gws_care_medical_program.

The gws_care_campaign_exam table was created when the Campaign model's table was
named gws_care_campaign. The table was later renamed to gws_care_medical_program,
but the FK constraint in campaign_exam still references the old name, causing every
INSERT to fail with a FK violation.
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.56.0",
    short_description="Fix gws_care_campaign_exam FK: point campaign_id to gws_care_medical_program",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration470(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        db = sql_migrator.migrator.database
        # Drop the stale FK that still points at the old gws_care_campaign table.
        # Wrapped in try/except in case the constraint was already fixed manually.
        try:
            db.execute_sql(
                "ALTER TABLE gws_care_campaign_exam "
                "DROP FOREIGN KEY gws_care_campaign_exam_ibfk_1"
            )
        except Exception:
            pass
        # Add the corrected FK pointing at the current campaign table name.
        db.execute_sql(
            "ALTER TABLE gws_care_campaign_exam "
            "ADD CONSTRAINT gws_care_campaign_exam_fk_campaign "
            "FOREIGN KEY (campaign_id) REFERENCES gws_care_medical_program(id) ON DELETE CASCADE"
        )
