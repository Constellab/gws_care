"""DB migration v0.1.0 — Initial tables: User, Account, Patient.

Note: We create tables using peewee's `create_tables(safe=True)` (= IF NOT EXISTS)
because the old `SqlMigrator.create_table_if_not_exists` helper no longer exists.
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.1.0",
    short_description="Initial tables: User, Account, Patient",
    db_manager=CareDbManager.get_instance(),
)
class Migration010(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database

        from gws_care.account.account import Account
        from gws_care.patient.patient import Patient
        from gws_care.user.user import User

        # Create base tables (IF NOT EXISTS is idempotent)
        db.create_tables([User, Account, Patient], safe=True)
