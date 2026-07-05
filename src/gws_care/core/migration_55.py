"""DB migration v0.64.0 — Delete all campaigns, appointments, and exam data."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.64.0",
    short_description="Delete all campaigns, appointments, visits, and exam data",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration550(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database
        for table in [
            # Exam children (must go before exam)
            "gws_care_exam_audit_entry",
            "gws_care_exam_file",
            "gws_care_exam_parameter_result",
            "gws_care_exam_result",
            "gws_care_exam_validation_workflow",
            # Exams
            "gws_care_exam",
            # Visit children
            "gws_care_campaign_visit_validation_workflow",
            # Visits
            "gws_care_visit",
            # Campaign children
            "gws_care_tube_qr",
            "gws_care_campaign_exam_doctor",
            "gws_care_campaign_exam",
            "gws_care_campaign_doctor",
            "gws_care_program_patient",
            "gws_care_program_exam_type",
            "gws_care_campaign_validation_workflow",
            # Campaigns
            "gws_care_medical_program",
            # Appointments (standalone, no campaign FK)
            "gws_care_appointment",
        ]:
            try:
                db.execute_sql(f"DELETE FROM {table}")
            except Exception:
                pass
