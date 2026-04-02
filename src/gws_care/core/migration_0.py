from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.company.company import Company
from gws_care.core.care_db_manager import CareDbManager
from gws_care.patient.patient import Patient
from gws_care.user.user import User


@brick_migration(
    "0.1.0",
    short_description="Initial schema: User, Company, Patient",
    db_manager=CareDbManager.get_instance(),
)
class Migration010(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        sql_migrator.create_table_if_not_exists(User)
        sql_migrator.create_table_if_not_exists(Company)
        sql_migrator.create_table_if_not_exists(Patient)
        sql_migrator.migrate()
