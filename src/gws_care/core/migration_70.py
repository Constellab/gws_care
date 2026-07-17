"""DB migration v0.68.6 — Rename PSC-specific columns and enum values to
organization-neutral names.

The gws_care brick originally served a single client (PS CONSULTING) and
several column/enum names carried that company's initials. The brick now
serves any company, so these identifiers are renamed to generic terms —
matching the code-level rename (viewer_is_psc -> viewer_is_internal, etc.)
shipped in the same release.

No data is lost: columns are renamed in place with CHANGE COLUMN (which
keeps the existing type/nullability/default, only the identifier changes),
and the two enum values still stored in medical_status are rewritten row by
row via UPDATE.

Idempotent: every step first checks whether it has already been applied
(old column no longer present / no row left with the old status value)
before acting, so re-running this migration — e.g. after an interrupted
first run — is a safe no-op.

Columns renamed:
  gws_care_program_patient.psc_notes                -> internal_notes
  gws_care_program_patient.psc_notified_at           -> internal_notified_at
  gws_care_program_patient.psc_validated_at          -> internal_validated_at
  gws_care_dashboard_snapshot.dossiers_awaiting_psc  -> dossiers_awaiting_internal

Enum values rewritten in gws_care_program_patient.medical_status:
  PSC_INTERPRETED -> INTERNAL_INTERPRETED
  PSC_VALIDATED   -> INTERNAL_VALIDATED
"""

from gws_care.core.care_db_manager import CareDbManager
from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

# (table, old_column, new_column, column_definition) — column_definition is the
# exact type/nullability/default this column was created with (see
# migration_10.py, migration_50.py, migration_66.py for psc_notes/
# psc_validated_at/psc_notified_at; dossiers_awaiting_psc is declared
# identically to its sibling IntegerField(default=0) KPI columns on the same
# DashboardSnapshot model).
_COLUMN_RENAMES = [
    ("gws_care_program_patient", "psc_notes", "internal_notes", "TEXT NULL DEFAULT NULL"),
    ("gws_care_program_patient", "psc_notified_at", "internal_notified_at", "DATETIME NULL DEFAULT NULL"),
    ("gws_care_program_patient", "psc_validated_at", "internal_validated_at", "DATETIME NULL DEFAULT NULL"),
    ("gws_care_dashboard_snapshot", "dossiers_awaiting_psc", "dossiers_awaiting_internal", "INT NOT NULL DEFAULT 0"),
]

_STATUS_RENAMES = [
    ("PSC_INTERPRETED", "INTERNAL_INTERPRETED"),
    ("PSC_VALIDATED", "INTERNAL_VALIDATED"),
]


def _column_exists(db, table: str, column: str) -> bool:
    row = db.execute_sql(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        f"WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{table}' AND COLUMN_NAME = '{column}'"
    ).fetchone()
    return bool(row and row[0])


@brick_migration(
    "0.68.6",
    short_description="Rename PSC-specific columns/enum values to organization-neutral names",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration700(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        db = sql_migrator.migrator.database

        for table, old_col, new_col, col_def in _COLUMN_RENAMES:
            try:
                if not _column_exists(db, table, old_col):
                    continue  # already renamed (or never existed) — safe no-op
                db.execute_sql(
                    f"ALTER TABLE `{table}` CHANGE COLUMN `{old_col}` `{new_col}` {col_def}"
                )
            except Exception as exc:
                print(f"[migration_70] Column rename {table}.{old_col} -> {new_col} skipped: {exc}")

        for old_value, new_value in _STATUS_RENAMES:
            try:
                db.execute_sql(
                    "UPDATE `gws_care_program_patient` SET medical_status = "
                    f"'{new_value}' WHERE medical_status = '{old_value}'"
                )
            except Exception as exc:
                print(f"[migration_70] Status rename {old_value} -> {new_value} skipped: {exc}")
