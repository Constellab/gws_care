"""Service for managing CareRole assignments."""

from gws_care.role.care_role import CareRole
from gws_care.role.user_care_role import UserCareRole
from gws_care.role.user_care_role_account import UserCareRoleAccount
from gws_care.user.user import User


class UserRoleService:
    """Assign, revoke, and query CareRoles for local users."""

    @classmethod
    def get_roles_for_user(cls, user_id: str) -> list[CareRole]:
        """Return all CareRoles held by the given user."""
        rows = list(UserCareRole.select().where(UserCareRole.user == user_id))
        return [r.role for r in rows]

    @classmethod
    def has_role(cls, user_id: str, role: CareRole) -> bool:
        return (
            UserCareRole.select()
            .where(UserCareRole.user == user_id, UserCareRole.role == role)
            .exists()
        )

    @classmethod
    def assign_role(cls, user_id: str, role: CareRole) -> None:
        """Assign a role to a user (idempotent).

        For DOCTOR: ``all_patients`` defaults to True (global patient access).
        """
        user = User.get_by_id(user_id)
        defaults = {}
        if role == CareRole.DOCTOR:
            defaults["all_patients"] = True
        UserCareRole.get_or_create(user=user, role=role, defaults=defaults)

    @classmethod
    def assign_role_with_link(
        cls,
        user_id: str,
        role: CareRole,
        linked_patient_id: str | None = None,
    ) -> None:
        """Assign a role to a user with an optional patient link (PATIENT role only).

        For DOCTOR and ACCOUNT_ADMIN account links, use
        ``add_account_link`` / ``remove_account_link`` instead.
        """
        user = User.get_by_id(user_id)
        row, created = UserCareRole.get_or_create(user=user, role=role)
        if linked_patient_id is not None:
            row.linked_patient_id = linked_patient_id
        if not created or linked_patient_id:
            row.save()

    # ── Account links (DOCTOR and ACCOUNT_ADMIN) ──────────────────────────────

    @classmethod
    def get_linked_account_ids(cls, user_id: str, role: CareRole) -> list[str]:
        """Return all account IDs linked to this user/role pair."""
        rows = list(
            UserCareRoleAccount.select()
            .where(UserCareRoleAccount.user == user_id, UserCareRoleAccount.role == role)
        )
        return [r.account_id for r in rows]

    @classmethod
    def add_account_link(cls, user_id: str, role: CareRole, account_id: str) -> None:
        """Link an account to a user/role pair (idempotent)."""
        user = User.get_by_id(user_id)
        UserCareRoleAccount.get_or_create(user=user, role=role, account_id=account_id)

    @classmethod
    def remove_account_link(cls, user_id: str, role: CareRole, account_id: str) -> None:
        """Remove an account link from a user/role pair (no-op if absent)."""
        UserCareRoleAccount.delete().where(
            UserCareRoleAccount.user == user_id,
            UserCareRoleAccount.role == role,
            UserCareRoleAccount.account_id == account_id,
        ).execute()

    @classmethod
    def get_doctor_all_patients(cls, user_id: str) -> bool:
        """Return True when the DOCTOR has global access to all patients."""
        row = (
            UserCareRole.select()
            .where(UserCareRole.user == user_id, UserCareRole.role == CareRole.DOCTOR)
            .first()
        )
        return row.all_patients if row else True

    @classmethod
    def set_doctor_all_patients(cls, user_id: str, all_patients: bool) -> None:
        """Set the all_patients flag on a DOCTOR's UserCareRole row."""
        (
            UserCareRole.update(all_patients=all_patients)
            .where(UserCareRole.user == user_id, UserCareRole.role == CareRole.DOCTOR)
            .execute()
        )

    @classmethod
    def set_doctor_link(cls, user_id: str, doctor_id: str | None) -> None:
        """Link or unlink a registered MedicalDoctor profile for a DOCTOR user."""
        (
            UserCareRole.update(linked_doctor_id=doctor_id)
            .where(UserCareRole.user == user_id, UserCareRole.role == CareRole.DOCTOR)
            .execute()
        )

    # ── Patient link (PATIENT role) ───────────────────────────────────────────

    @classmethod
    def get_linked_patient_id(cls, user_id: str) -> str | None:
        """Return the linked patient ID for a PATIENT user, or None."""
        row = (
            UserCareRole.select()
            .where(UserCareRole.user == user_id, UserCareRole.role == CareRole.PATIENT)
            .first()
        )
        return row.linked_patient_id if row else None

    # ── Revoke ────────────────────────────────────────────────────────────────

    @classmethod
    def revoke_role(cls, user_id: str, role: CareRole) -> None:
        """Remove a role from a user and clean up all linked account entries."""
        UserCareRoleAccount.delete().where(
            UserCareRoleAccount.user == user_id,
            UserCareRoleAccount.role == role,
        ).execute()
        UserCareRole.delete().where(
            UserCareRole.user == user_id,
            UserCareRole.role == role,
        ).execute()

    # ── Admin panel query ─────────────────────────────────────────────────────

    @classmethod
    def list_users_with_roles(cls) -> list[dict]:
        """Return all users with their role lists, for the admin panel."""
        users = list(User.select().where(User.is_active == True).order_by(User.last_name))
        result = []
        for u in users:
            rows = list(UserCareRole.select().where(UserCareRole.user == u.id))
            role_values = [r.role.value for r in rows]
            linked_patient_id = next(
                (r.linked_patient_id for r in rows if r.role == CareRole.PATIENT),
                None,
            )
            linked_doctor_id = next(
                (r.linked_doctor_id for r in rows if r.role == CareRole.DOCTOR),
                None,
            )
            acct_rows = list(
                UserCareRoleAccount.select()
                .where(UserCareRoleAccount.user == u.id)
            )
            account_admin_account_ids = [
                r.account_id for r in acct_rows if r.role == CareRole.ACCOUNT_ADMIN
            ]
            result.append(
                {
                    "id": str(u.id),
                    "full_name": f"{u.first_name} {u.last_name}",
                    "email": u.email,
                    "roles": role_values,
                    "linked_patient_id": linked_patient_id or "",
                    "linked_doctor_id": linked_doctor_id or "",
                    "account_admin_account_ids": account_admin_account_ids,
                }
            )
        return result

