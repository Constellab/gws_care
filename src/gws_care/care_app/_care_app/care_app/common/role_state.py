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

    # ── Computed role shortcuts (public — read by frontend) ───────────────────

    @rx.var
    def is_admin(self) -> bool:
        # TODO: remove dev bypass before production
        return True

    @rx.var
    def is_doctor(self) -> bool:
        # TODO: remove dev bypass before production
        return True

    @rx.var
    def is_operator(self) -> bool:
        # TODO: remove dev bypass before production
        return True

    @rx.var
    def has_any_role(self) -> bool:
        return True

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
                # Check if the user is a gws_core platform admin
                try:
                    local_user = User.get_by_id(str(auth_user.id))
                    self._is_platform_admin = local_user.group == UserGroup.ADMIN
                except Exception:
                    self._is_platform_admin = False
        except Exception:
            self._care_roles = []
            self._is_platform_admin = False
