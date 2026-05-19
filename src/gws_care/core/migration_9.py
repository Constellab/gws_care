"""DB migration v0.10.0 — Add Campaign and CampaignPatient tables."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.9.1",
    short_description="Add Campaign and CampaignPatient tables for V2 dashboard",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration091(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database

        from gws_care.campaign.campaign import Campaign
        from gws_care.campaign.campaign_patient import CampaignPatient

        db.create_tables([Campaign, CampaignPatient], safe=True)
