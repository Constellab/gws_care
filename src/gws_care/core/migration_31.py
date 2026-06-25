"""DB migration v0.40.0 — Create gws_care_campaign_doctor linking table."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.40.0",
    short_description="Create CampaignDoctor linking table (Campaign ↔ MedicalDoctor)",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration310(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database
        from gws_care.campaign.campaign_doctor import CampaignDoctor
        db.create_tables([CampaignDoctor], safe=True)
