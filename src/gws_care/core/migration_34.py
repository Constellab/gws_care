"""DB migration v0.43.0 — Add computed parameter fields to gws_care_exam_parameter.

Adds three columns:
  - code       VARCHAR(50) NULL  — short slug used in formulas to reference this param
  - is_computed TINYINT(1) NOT NULL DEFAULT 0  — True if value is derived from a formula
  - formula    LONGTEXT NULL     — arithmetic expression referencing other params by code
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.43.0",
    short_description="Add code, is_computed, formula to gws_care_exam_parameter",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration340(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database
        db.execute_sql(
            "ALTER TABLE gws_care_exam_parameter"
            " ADD COLUMN IF NOT EXISTS code VARCHAR(50) NULL DEFAULT NULL"
        )
        db.execute_sql(
            "ALTER TABLE gws_care_exam_parameter"
            " ADD COLUMN IF NOT EXISTS is_computed TINYINT(1) NOT NULL DEFAULT 0"
        )
        db.execute_sql(
            "ALTER TABLE gws_care_exam_parameter"
            " ADD COLUMN IF NOT EXISTS formula LONGTEXT NULL DEFAULT NULL"
        )
