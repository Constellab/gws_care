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
        return (
            "SUPER_ADMIN_PSC" in self._care_roles
            or "ADMIN_PSC" in self._care_roles
            or self._is_platform_admin
        )

    @rx.var
    def is_doctor(self) -> bool:
        return "MEDECIN_PSC" in self._care_roles or "MEDECIN_ENTREPRISE" in self._care_roles

    @rx.var
    def is_operator(self) -> bool:
        return "OPERATEUR_TERRAIN" in self._care_roles or "OPERATEUR_LABO" in self._care_roles

    @rx.var
    def has_any_role(self) -> bool:
        return len(self._care_roles) > 0 or self._is_platform_admin

    @rx.var
    def is_account_admin(self) -> bool:
        return "ACCOUNT_ADMIN" in self._care_roles

    @rx.var
    def is_patient_user(self) -> bool:
        return "PATIENT" in self._care_roles

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
                except Exception as exc:
                    self._is_platform_admin = False
        except Exception as exc:
            self._care_roles = []
            self._linked_account_id = ""
            self._linked_patient_id = ""
            self._is_platform_admin = False
