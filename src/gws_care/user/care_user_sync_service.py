from gws_core import User as GwsCoreUser
from gws_core import UserGroup, UserSyncService, event_listener

from .user import User


@event_listener
class CareUserSyncService(UserSyncService[User]):
    """
    Syncs users from gws_core into the gws_care local User table.

    Handles system.started, user.created, user.updated, user.activated events.
    Required so that ModelWithUser (created_by / last_modified_by FKs) can resolve.

    Platform admins (gws_core UserGroup.ADMIN) are automatically assigned the
    CareRole.ADMIN role on sync, ensuring they always have full access.
    """

    def get_user_type(self) -> type[User]:
        return User

    def from_gws_core_user(self, gws_core_user: GwsCoreUser) -> User:
        return User.from_gws_core_user(gws_core_user)

    def sync_user(self, gws_core_user: GwsCoreUser) -> User:
        """Sync user and auto-assign ADMIN care role to platform admins."""
        user = super().sync_user(gws_core_user)
        if gws_core_user.group == UserGroup.ADMIN:
            try:
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_role_service import UserRoleService
                UserRoleService.assign_role(str(user.id), CareRole.ADMIN)
            except Exception:
                pass  # Table may not exist yet during initial migration
        return user
