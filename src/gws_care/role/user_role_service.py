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
        specialty: str | None = None,
    ) -> None:
        """Assign a role to a user with an optional entity link.

        For ACCOUNT_ADMIN, pass linked_account_id.
        For PATIENT, pass linked_patient_id.
        For MEDECIN_PSC / MEDECIN_ENTREPRISE, pass specialty.
        Creates the row if absent; updates the link columns if already present.
        """
        user = User.get_by_id(user_id)
        row, created = UserCareRole.get_or_create(user=user, role=role)
        if linked_account_id is not None:
            row.linked_account_id = linked_account_id
        if linked_patient_id is not None:
            row.linked_patient_id = linked_patient_id
        if specialty is not None:
            row.specialty = specialty or None
        if not created or linked_account_id or linked_patient_id or specialty is not None:
            row.save()

    @classmethod
    def get_linked_account_id(cls, user_id: str) -> str | None:
        """Return the linked account ID for a company role user, or None."""
        company_roles = (CareRole.RH_ENTREPRISE, CareRole.MEDECIN_ENTREPRISE)
        for role in company_roles:
            row = (
                UserCareRole.select()
                .where(UserCareRole.user == user_id, UserCareRole.role == role)
                .first()
            )
            if row and row.linked_account_id:
                return row.linked_account_id
        # Backward compat: legacy ACCOUNT_ADMIN row
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
        """Return all active users with their role lists, for the admin panel."""
        users = list(User.select().where(User.is_active == True).order_by(User.last_name))
        if not users:
            return []
        # Batch-load ALL care role rows at once (avoids N+1: one SELECT instead of N)
        user_ids = [u.id for u in users]
        all_role_rows = list(UserCareRole.select().where(UserCareRole.user.in_(user_ids)))
        roles_by_user: dict[str, list] = {}
        for r in all_role_rows:
            roles_by_user.setdefault(str(r.user_id), []).append(r)
        _account_roles = {CareRole.ACCOUNT_ADMIN, CareRole.RH_ENTREPRISE, CareRole.MEDECIN_ENTREPRISE}
        _doctor_roles = {CareRole.MEDECIN_PSC, CareRole.MEDECIN_ENTREPRISE}
        result = []
        for u in users:
            rows = roles_by_user.get(str(u.id), [])
            role_values = [r.role.value for r in rows]
            # Return linked account from any enterprise role row (Medecin, RH, or legacy AccountAdmin)
            linked_account_id = next(
                (r.linked_account_id for r in rows
                 if r.role in _account_roles and r.linked_account_id),
                None,
            )
            linked_patient_id = next(
                (r.linked_patient_id for r in rows if r.role == CareRole.PATIENT),
                None,
            )
            specialty = next(
                (r.specialty for r in rows if r.role in _doctor_roles and r.specialty),
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
                    "specialty": specialty or "",
                }
            )
        return result
