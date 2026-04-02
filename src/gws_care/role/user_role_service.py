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
            roles = cls.get_roles_for_user(str(u.id))
            result.append(
                {
                    "id": str(u.id),
                    "full_name": f"{u.first_name} {u.last_name}",
                    "email": u.email,
                    "roles": [r.value for r in roles],
                }
            )
        return result
