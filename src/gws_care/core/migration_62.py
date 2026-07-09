"""DB migration v0.66.0 — Add ExamParameterAgeRange table for age/gender-based thresholds."""

from gws_care.core.care_db_manager import CareDbManager
from gws_core import BrickMigration, SqlMigrator, Version, brick_migration


@brick_migration(
    "0.66.0",
    short_description="Add age/gender-based reference range table for exam parameters",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration620(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        from gws_care.exam_type_ref.exam_param_age_range import ExamParameterAgeRange
        sql_migrator.migrator.database.create_tables([ExamParameterAgeRange], safe=True)
