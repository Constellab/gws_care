"""State for the /switch_role page."""

import reflex as rx

from ..common.role_state import RoleState


class SwitchRoleState(RoleState):
    """State for the role-selection page."""

    @rx.event
    async def on_load(self):
        await self._load_roles()
