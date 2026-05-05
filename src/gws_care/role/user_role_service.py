"""Service for managing CareRole assignments."""

from gws_care.role.care_role import CareRole
from gws_care.role.user_care_role import UserCareRole
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
        """Assign a role to a user (idempotent)."""
        user = User.get_by_id(user_id)
        UserCareRole.get_or_create(user=user, role=role)

    @classmethod
    def assign_role_with_link(
        cls,
        user_id: str,
        role: CareRole,
        linked_account_id: str | None = None,
        linked_patient_id: str | None = None,
    ) -> None:
        """Assign a role to a user with an optional entity link.

        For ACCOUNT_ADMIN, pass linked_account_id.
        For PATIENT, pass linked_patient_id.
        Creates the row if absent; updates the link columns if already present.
        """
        user = User.get_by_id(user_id)
        row, created = UserCareRole.get_or_create(user=user, role=role)
        if linked_account_id is not None:
            row.linked_account_id = linked_account_id
        if linked_patient_id is not None:
            row.linked_patient_id = linked_patient_id
        if not created or linked_account_id or linked_patient_id:
            row.save()

    @classmethod
    def get_linked_account_id(cls, user_id: str) -> str | None:
        """Return the linked account ID for an ACCOUNT_ADMIN user, or None."""
        row = (
            UserCareRole.select()
            .where(UserCareRole.user == user_id, UserCareRole.role == CareRole.ACCOUNT_ADMIN)
            .first()
        )
        return row.linked_account_id if row else None

    @classmethod
    def get_linked_patient_id(cls, user_id: str) -> str | None:
        """Return the linked patient ID for a PATIENT user, or None."""
        row = (
            UserCareRole.select()
            .where(UserCareRole.user == user_id, UserCareRole.role == CareRole.PATIENT)
            .first()
        )
        return row.linked_patient_id if row else None

    @classmethod
    def revoke_role(cls, user_id: str, role: CareRole) -> None:
        """Remove a role from a user (no-op if not assigned)."""
        UserCareRole.delete().where(
            UserCareRole.user == user_id,
            UserCareRole.role == role,
        ).execute()

    @classmethod
    def list_users_with_roles(cls) -> list[dict]:
        """Return all users with their role lists, for the admin panel."""
        users = list(User.select().where(User.is_active == True).order_by(User.last_name))
        result = []
        for u in users:
            rows = list(UserCareRole.select().where(UserCareRole.user == u.id))
            role_values = [r.role.value for r in rows]
            # Collect linked IDs keyed by role
            linked_account_id = next(
                (r.linked_account_id for r in rows if r.role == CareRole.ACCOUNT_ADMIN),
                None,
            )
            linked_patient_id = next(
                (r.linked_patient_id for r in rows if r.role == CareRole.PATIENT),
                None,
            )
            result.append(
                {
                    "id": str(u.id),
                    "full_name": f"{u.first_name} {u.last_name}",
                    "email": u.email,
                    "roles": role_values,
                    "linked_account_id": linked_account_id or "",
                    "linked_patient_id": linked_patient_id or "",
                }
            )
        return result
