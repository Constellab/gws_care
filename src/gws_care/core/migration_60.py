"""DB migration v0.65.4 — Delete certificate data; add selected_param_ids to CampaignExam."""

from gws_care.core.care_db_manager import CareDbManager
from gws_core import BrickMigration, SqlMigrator, Version, brick_migration


@brick_migration(
    "0.65.4",
    short_description="Delete certificates; add selected_param_ids to campaign_exam",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration600(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        db = sql_migrator.migrator.database
        try:
            db.execute_sql("DELETE FROM gws_care_medical_certificate")
        except Exception:
            pass
        try:
            db.execute_sql(
                "ALTER TABLE gws_care_campaign_exam "
                "ADD COLUMN IF NOT EXISTS selected_param_ids LONGTEXT NULL DEFAULT NULL"
            )
        except Exception:
            pass
