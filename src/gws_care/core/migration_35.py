"""DB migration v0.44.0 — Add target_gender to gws_care_exam_parameter.

Values: 'ALL' (indifferent), 'M' (homme), 'F' (femme).
Existing rows default to 'ALL'.
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.44.0",
    short_description="Add target_gender to gws_care_exam_parameter",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration350(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database
        db.execute_sql(
            "ALTER TABLE gws_care_exam_parameter"
            " ADD COLUMN IF NOT EXISTS target_gender VARCHAR(5) NOT NULL DEFAULT 'ALL'"
        )
