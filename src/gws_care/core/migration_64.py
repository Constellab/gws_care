"""DB migration v0.68.0 — Collapse CareRole tiers (V2 → V3 role simplification).

SUPER_ADMIN_PSC / DIRECTEUR_PSC / ADMIN_PSC -> ADMIN
OPERATEUR_TERRAIN / OPERATEUR_LABO          -> OPERATEUR
MEDECIN_PSC / MEDECIN_ENTREPRISE            -> MEDECIN

Applied to gws_care_user_role (unique on user_id+role) and
gws_care_user_role_account (unique on user_id+role+account_id). A user who
already held two roles from the same merge group — or who already held a
literal row for the *target* value itself (e.g. a legacy pre-V2 "ADMIN" row
that predates the SUPER_ADMIN_PSC/DIRECTEUR_PSC/ADMIN_PSC naming) — would
violate the unique index on a plain UPDATE. Duplicates are removed first
(keeping the pre-existing target-value row if there is one, else the
lowest-id row in the merge group) before the role value is rewritten.
"""

from gws_care.core.care_db_manager import CareDbManager
from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

_MERGE_GROUPS = [
    (["SUPER_ADMIN_PSC", "DIRECTEUR_PSC", "ADMIN_PSC"], "ADMIN"),
    (["OPERATEUR_TERRAIN", "OPERATEUR_LABO"], "OPERATEUR"),
    (["MEDECIN_PSC", "MEDECIN_ENTREPRISE"], "MEDECIN"),
]


@brick_migration(
    "0.68.0",
    short_description="Collapse CareRole tiers (admin/operator/doctor merge)",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration640(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        db = sql_migrator.migrator.database
        for old_values, new_value in _MERGE_GROUPS:
            old_in_clause = ", ".join(f"'{v}'" for v in old_values)
            # Include the target value itself so a pre-existing row for it
            # (legacy or from a previous partial run) is part of the dedup set.
            all_in_clause = ", ".join(f"'{v}'" for v in old_values + [new_value])
            try:
                # gws_care_user_role: unique on (user_id, role) — dedup per user_id,
                # preferring an existing target-value row as the one to keep.
                db.execute_sql(
                    "DELETE a FROM `gws_care_user_role` a "
                    "JOIN ("
                    "    SELECT user_id, "
                    f"           COALESCE(MIN(CASE WHEN role = '{new_value}' THEN id END), MIN(id)) AS keep_id "
                    "    FROM `gws_care_user_role` "
                    f"    WHERE role IN ({all_in_clause}) GROUP BY user_id"
                    ") keep ON a.user_id = keep.user_id "
                    f"WHERE a.role IN ({all_in_clause}) AND a.id <> keep.keep_id"
                )
                db.execute_sql(
                    f"UPDATE `gws_care_user_role` SET role = '{new_value}' WHERE role IN ({old_in_clause})"
                )
            except Exception:
                pass
            try:
                # gws_care_user_role_account: unique on (user_id, role, account_id) — dedup per (user_id, account_id).
                db.execute_sql(
                    "DELETE a FROM `gws_care_user_role_account` a "
                    "JOIN ("
                    "    SELECT user_id, account_id, "
                    f"           COALESCE(MIN(CASE WHEN role = '{new_value}' THEN id END), MIN(id)) AS keep_id "
                    "    FROM `gws_care_user_role_account` "
                    f"    WHERE role IN ({all_in_clause}) GROUP BY user_id, account_id"
                    ") keep ON a.user_id = keep.user_id AND a.account_id = keep.account_id "
                    f"WHERE a.role IN ({all_in_clause}) AND a.id <> keep.keep_id"
                )
                db.execute_sql(
                    "UPDATE `gws_care_user_role_account` SET role = "
                    f"'{new_value}' WHERE role IN ({old_in_clause})"
                )
            except Exception:
                pass
