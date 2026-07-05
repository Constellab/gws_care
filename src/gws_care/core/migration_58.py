"""DB migration v0.65.2 — Delete remaining campaigns and all assigned exam data."""

from gws_care.core.care_db_manager import CareDbManager
from gws_core import BrickMigration, SqlMigrator, Version, brick_migration


@brick_migration(
    "0.65.2",
    short_description="Reset: delete all campaign records and assigned exam data",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration580(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        db = sql_migrator.migrator.database
        for table in [
            "gws_care_exam_audit_entry",
            "gws_care_exam_file",
            "gws_care_exam_parameter_result",
            "gws_care_exam_result",
            "gws_care_exam_validation_workflow",
            "gws_care_exam",
            "gws_care_campaign_visit_validation_workflow",
            "gws_care_visit",
            "gws_care_tube_qr",
            "gws_care_campaign_exam_doctor",
            "gws_care_campaign_exam",
            "gws_care_campaign_doctor",
            "gws_care_campaign_patient",
            "gws_care_campaign_validation_workflow",
            "gws_care_medical_program",
            "gws_care_campaign",
        ]:
            try:
                db.execute_sql(f"DELETE FROM {table}")
            except Exception:
                pass
