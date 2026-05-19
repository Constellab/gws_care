"""DB migration v0.18.0 — Rename visit status values.

Renames deprecated CampaignVisitStatus and CampaignVisitValidationStep values:
  - 'on-site_done'    → 'visit_done'
  - 'results_entered' → 'visit_done'   (intermediate step collapsed)
  - 'lab_validated'   → 'lab_done'
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.18.0",
    short_description="Rename visit status: on-site_done→visit_done, results_entered→visit_done, lab_validated→lab_done",
    db_manager=CareDbManager.get_instance(),
)
class Migration0180(BrickMigration):
    @classmethod
    def migrate(
        cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version
    ) -> None:
        db = CareDbManager.get_instance().db

        # ── gws_care_visit.status ─────────────────────────────────────────────
        db.execute_sql(
            "UPDATE gws_care_visit SET status = 'visit_done' WHERE status = 'on-site_done'"
        )
        db.execute_sql(
            "UPDATE gws_care_visit SET status = 'visit_done' WHERE status = 'results_entered'"
        )
        db.execute_sql(
            "UPDATE gws_care_visit SET status = 'lab_done' WHERE status = 'lab_validated'"
        )

        # ── gws_care_visit_validation_workflow.step ───────────────────────────
        db.execute_sql(
            "UPDATE gws_care_visit_validation_workflow SET step = 'visit_done' WHERE step = 'on-site_done'"
        )
        db.execute_sql(
            "DELETE FROM gws_care_visit_validation_workflow WHERE step = 'results_entered'"
        )
        db.execute_sql(
            "UPDATE gws_care_visit_validation_workflow SET step = 'lab_done' WHERE step = 'lab_validated'"
        )
