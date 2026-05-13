"""RoleState — mixin providing role-based computed vars for any Reflex state.

Usage:
    class MyPageState(RoleState):
        ...

    # In component:
    rx.cond(MyPageState.is_doctor, doctor_only_section(), rx.fragment())
"""

import reflex as rx
from gws_reflex_main import ReflexMainState


class RoleState(ReflexMainState):
    """Mixin that loads the current user's CareRoles and exposes helper vars.

    Keeps a list of role values (strings) in state so Reflex can react to them.
    Call `await self._load_roles()` inside any `on_load` handler.
    """

    _care_roles: list[str] = []   # private — backend use only
    _is_platform_admin: bool = False  # private — True when gws_core UserGroup is ADMIN
    _linked_account_id: str = ""  # private — set for ACCOUNT_ADMIN role
    _linked_patient_id: str = ""  # private — set for PATIENT role

    # ── Computed role shortcuts (public — read by frontend) ───────────────────

    @rx.var
    def is_admin(self) -> bool:
        """True for the platform super-admin or any user with the ADMIN care role."""
        return self._is_platform_admin or "ADMIN" in self._care_roles

    @rx.var
    def is_doctor(self) -> bool:
        """True for Clinic Doctor PSC (DOCTOR role) or ADMIN."""
        return self.is_admin or "DOCTOR" in self._care_roles

    @rx.var
    def is_operator(self) -> bool:
        """True for HQ Operator PSC (OPERATOR role) or ADMIN."""
        return self.is_admin or "OPERATOR" in self._care_roles

    @rx.var
    def is_account_admin(self) -> bool:
        """True for Company Doctor / Responsable RH (ACCOUNT_ADMIN role) or ADMIN."""
        return self.is_admin or "ACCOUNT_ADMIN" in self._care_roles

    @rx.var
    def is_rh(self) -> bool:
        """Alias for is_account_admin — used in RH / company-doctor context."""
        return self.is_account_admin

    @rx.var
    def is_patient_user(self) -> bool:
        """True when the user is a linked patient (PATIENT role)."""
        return "PATIENT" in self._care_roles

    @rx.var
    def has_any_role(self) -> bool:
        """True when the user has at least one CareRole (or is platform admin)."""
        return self._is_platform_admin or len(self._care_roles) > 0

    @rx.var
    def linked_account_id(self) -> str:
        return self._linked_account_id

    @rx.var
    def linked_patient_id(self) -> str:
        return self._linked_patient_id

    # ── Internal loader ───────────────────────────────────────────────────────

    async def _load_roles(self) -> None:
        """Fetch the current user's roles from DB.

        Must be called from within an authenticate_user() context.
        Also detects platform-level admins (gws_core UserGroup.ADMIN) to allow
        bootstrapping role assignments on a fresh install.
        """
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.role.user_role_service import UserRoleService
                from gws_care.user.user import User
                from gws_core import UserGroup
                roles = UserRoleService.get_roles_for_user(str(auth_user.id))
                self._care_roles = [r.value for r in roles]
                # Linked entity IDs for ACCOUNT_ADMIN / PATIENT roles
                self._linked_account_id = UserRoleService.get_linked_account_id(str(auth_user.id)) or ""
                self._linked_patient_id = UserRoleService.get_linked_patient_id(str(auth_user.id)) or ""
                # Check if the user is a gws_core platform admin
                try:
                    local_user = User.get_by_id(str(auth_user.id))
                    self._is_platform_admin = local_user.group == UserGroup.ADMIN
                except Exception:
                    self._is_platform_admin = False
        except Exception:
            self._care_roles = []
            self._linked_account_id = ""
            self._linked_patient_id = ""
            self._is_platform_admin = False

    async def _require_any_of(self, *role_checks: bool, redirect_to: str = "/dashboard"):
        """Redirect to *redirect_to* if none of the given role conditions are True.

        Call this **after** ``await self._load_roles()`` inside ``on_load``.

        Example::

            await self._load_roles()
            yield await self._require_any_of(self.is_operator, self.is_doctor)
        """
        if not any(role_checks):
            return rx.redirect(redirect_to)
        return None
