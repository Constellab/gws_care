"""DB migration v0.61.0 — Remove test campaign Awarness_subway_2027."""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.61.0",
    short_description="Delete test campaign Awarness_subway_2027 and all related data",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration520(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = sql_migrator.migrator.database
        try:
            db.execute_sql(
                "DELETE ced FROM gws_care_campaign_exam_doctor ced "
                "INNER JOIN gws_care_campaign_exam ce ON ced.campaign_exam_id = ce.id "
                "INNER JOIN gws_care_medical_program p ON p.id = ce.campaign_id "
                "WHERE p.name = 'Awarness_subway_2027'"
            )
            db.execute_sql(
                "DELETE FROM gws_care_campaign_exam WHERE campaign_id IN "
                "(SELECT id FROM (SELECT id FROM gws_care_medical_program "
                " WHERE name = 'Awarness_subway_2027') AS t)"
            )
            db.execute_sql(
                "DELETE FROM gws_care_campaign_doctor WHERE campaign_id IN "
                "(SELECT id FROM (SELECT id FROM gws_care_medical_program "
                " WHERE name = 'Awarness_subway_2027') AS t)"
            )
            db.execute_sql(
                "DELETE FROM gws_care_program_patient WHERE program_id IN "
                "(SELECT id FROM (SELECT id FROM gws_care_medical_program "
                " WHERE name = 'Awarness_subway_2027') AS t)"
            )
            db.execute_sql(
                "DELETE FROM gws_care_visit WHERE program_id IN "
                "(SELECT id FROM (SELECT id FROM gws_care_medical_program "
                " WHERE name = 'Awarness_subway_2027') AS t)"
            )
            db.execute_sql(
                "DELETE FROM gws_care_medical_program WHERE name = 'Awarness_subway_2027'"
            )
        except Exception:
            pass  # Campaign not found or already deleted — safe to ignore
