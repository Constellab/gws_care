"""State for the Admin panel — user role management."""

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


class UserRoleRowDTO(BaseModel):
    """Represents a user with their assigned role list for the admin panel."""

    id: str
    full_name: str
    email: str
    roles: list[str]   # list of CareRole values

    @property
    def is_admin(self) -> bool:
        return "ADMIN" in self.roles

    @property
    def is_doctor(self) -> bool:
        return "DOCTOR" in self.roles

    @property
    def is_operator(self) -> bool:
        return "OPERATOR" in self.roles


class AdminState(RoleState):
    """State for the /admin page."""

    users: list[UserRoleRowDTO] = []
    is_loading: bool = False
    error_message: str = ""
    success_message: str = ""

    @rx.event
    async def on_load(self):
        await self._load_roles()
        await self._load_users()

    @rx.event
    async def toggle_role(self, user_id: str, role: str):
        """Toggle a CareRole for a user (assign if missing, revoke if present)."""
        self.error_message = ""
        self.success_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_role_service import UserRoleService

                care_role = CareRole(role)
                if UserRoleService.has_role(user_id, care_role):
                    UserRoleService.revoke_role(user_id, care_role)
                    self.success_message = f"Role '{care_role.get_label()}' revoked."
                else:
                    UserRoleService.assign_role(user_id, care_role)
                    self.success_message = f"Role '{care_role.get_label()}' assigned."
            await self._load_users()
        except Exception as e:
            self.error_message = f"Error updating role: {e}"

    async def _load_users(self):
        if not await self.check_authentication():
            return
        self.is_loading = True
        try:
            with await self.authenticate_user():
                from gws_care.role.user_role_service import UserRoleService
                rows = UserRoleService.list_users_with_roles()
                self.users = [
                    UserRoleRowDTO(
                        id=r["id"],
                        full_name=r["full_name"],
                        email=r["email"],
                        roles=r["roles"],
                    )
                    for r in rows
                ]
        except Exception as e:
            self.error_message = f"Error loading users: {e}"
        finally:
            self.is_loading = False
