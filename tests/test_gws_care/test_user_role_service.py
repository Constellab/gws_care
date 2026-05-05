"""Unit tests for UserRoleService."""

from gws_care.role.care_role import CareRole
from gws_care.role.user_care_role import UserCareRole
from gws_care.role.user_role_service import UserRoleService
from gws_care.user.care_user_sync_service import CareUserSyncService
from gws_care.user.user import User
from gws_core import BaseTestCase

# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_user() -> User:
    """Return the first available active user."""
    return User.select().where(User.is_active == True).get()


def _get_or_create_second_user() -> User:
    """Return a second active user, creating a dummy one if needed."""
    users = list(User.select().where(User.is_active == True).limit(2))
    if len(users) >= 2:
        return users[1]
    # Create a temporary second user for isolation tests
    import uuid
    u = User()
    u.id = uuid.uuid4()
    u.email = f"testuser2_{uuid.uuid4().hex[:6]}@test.local"
    u.first_name = "Test"
    u.last_name = "UserTwo"
    u.is_active = True
    u.save(force_insert=True)
    return u


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestUserRoleService(BaseTestCase):
    """Tests for UserRoleService: assign, revoke, query and list."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    def setUp(self):
        # Clean all role assignments before each test for isolation
        UserCareRole.delete().execute()

    # ── assign_role ───────────────────────────────────────────────────────────

    def test_assign_role(self):
        """assign_role adds a role; has_role returns True."""
        user = _get_user()
        UserRoleService.assign_role(str(user.id), CareRole.DOCTOR)
        self.assertTrue(UserRoleService.has_role(str(user.id), CareRole.DOCTOR))

    def test_assign_role_idempotent(self):
        """Assigning the same role twice does not create duplicate rows."""
        user = _get_user()
        UserRoleService.assign_role(str(user.id), CareRole.OPERATOR)
        UserRoleService.assign_role(str(user.id), CareRole.OPERATOR)  # second call

        count = UserCareRole.select().where(
            UserCareRole.user == user.id,
            UserCareRole.role == CareRole.OPERATOR,
        ).count()
        self.assertEqual(count, 1)

    def test_assign_multiple_roles(self):
        """A user can hold multiple distinct roles simultaneously."""
        user = _get_user()
        UserRoleService.assign_role(str(user.id), CareRole.DOCTOR)
        UserRoleService.assign_role(str(user.id), CareRole.ADMIN)

        roles = UserRoleService.get_roles_for_user(str(user.id))
        self.assertIn(CareRole.DOCTOR, roles)
        self.assertIn(CareRole.ADMIN, roles)

    # ── revoke_role ───────────────────────────────────────────────────────────

    def test_revoke_role(self):
        """revoke_role removes the role; has_role returns False."""
        user = _get_user()
        UserRoleService.assign_role(str(user.id), CareRole.ADMIN)
        UserRoleService.revoke_role(str(user.id), CareRole.ADMIN)
        self.assertFalse(UserRoleService.has_role(str(user.id), CareRole.ADMIN))

    def test_revoke_role_no_op_when_not_assigned(self):
        """Revoking a role the user doesn't have does not raise."""
        user = _get_user()
        # User has no roles (setUp cleared all)
        UserRoleService.revoke_role(str(user.id), CareRole.DOCTOR)
        # Should reach here without exception
        self.assertFalse(UserRoleService.has_role(str(user.id), CareRole.DOCTOR))

    def test_revoke_one_role_leaves_others(self):
        """Revoking one role does not affect other roles held by the same user."""
        user = _get_user()
        UserRoleService.assign_role(str(user.id), CareRole.DOCTOR)
        UserRoleService.assign_role(str(user.id), CareRole.OPERATOR)

        UserRoleService.revoke_role(str(user.id), CareRole.DOCTOR)

        self.assertFalse(UserRoleService.has_role(str(user.id), CareRole.DOCTOR))
        self.assertTrue(UserRoleService.has_role(str(user.id), CareRole.OPERATOR))

    # ── has_role ──────────────────────────────────────────────────────────────

    def test_has_role_false_before_assign(self):
        """has_role returns False for a user with no roles."""
        user = _get_user()
        self.assertFalse(UserRoleService.has_role(str(user.id), CareRole.ADMIN))

    def test_has_role_true_after_assign(self):
        """has_role returns True after assign_role."""
        user = _get_user()
        UserRoleService.assign_role(str(user.id), CareRole.ADMIN)
        self.assertTrue(UserRoleService.has_role(str(user.id), CareRole.ADMIN))

    def test_has_role_false_after_revoke(self):
        """has_role returns False after role is revoked."""
        user = _get_user()
        UserRoleService.assign_role(str(user.id), CareRole.ADMIN)
        UserRoleService.revoke_role(str(user.id), CareRole.ADMIN)
        self.assertFalse(UserRoleService.has_role(str(user.id), CareRole.ADMIN))

    def test_has_role_per_user_isolation(self):
        """has_role for user A is not affected by user B's roles."""
        u1 = _get_user()
        u2 = _get_or_create_second_user()
        UserRoleService.assign_role(str(u1.id), CareRole.DOCTOR)

        self.assertTrue(UserRoleService.has_role(str(u1.id), CareRole.DOCTOR))
        self.assertFalse(UserRoleService.has_role(str(u2.id), CareRole.DOCTOR))

    # ── get_roles_for_user ────────────────────────────────────────────────────

    def test_get_roles_for_user_empty(self):
        """Returns empty list for a user with no roles assigned."""
        user = _get_user()
        roles = UserRoleService.get_roles_for_user(str(user.id))
        self.assertEqual(roles, [])

    def test_get_roles_for_user_multiple(self):
        """Returns all assigned roles for a user."""
        user = _get_user()
        UserRoleService.assign_role(str(user.id), CareRole.DOCTOR)
        UserRoleService.assign_role(str(user.id), CareRole.OPERATOR)

        roles = UserRoleService.get_roles_for_user(str(user.id))
        self.assertCountEqual(roles, [CareRole.DOCTOR, CareRole.OPERATOR])

    # ── list_users_with_roles ─────────────────────────────────────────────────

    def test_list_users_with_roles_includes_active_users(self):
        """list_users_with_roles includes all active users in the result."""
        results = UserRoleService.list_users_with_roles()
        self.assertGreater(len(results), 0)
        for entry in results:
            self.assertIn("id", entry)
            self.assertIn("full_name", entry)
            self.assertIn("email", entry)
            self.assertIn("roles", entry)
            self.assertIsInstance(entry["roles"], list)

    def test_list_users_with_roles_correct_roles(self):
        """User entry contains correct role values after assignment."""
        user = _get_user()
        UserRoleService.assign_role(str(user.id), CareRole.ADMIN)

        results = UserRoleService.list_users_with_roles()
        user_entry = next((e for e in results if e["id"] == str(user.id)), None)
        self.assertIsNotNone(user_entry)
        self.assertIn(CareRole.ADMIN.value, user_entry["roles"])

    def test_list_users_with_roles_no_roles(self):
        """User entry with no roles has an empty roles list."""
        user = _get_user()
        # No roles assigned (setUp cleared all)

        results = UserRoleService.list_users_with_roles()
        user_entry = next((e for e in results if e["id"] == str(user.id)), None)
        self.assertIsNotNone(user_entry)
        self.assertEqual(user_entry["roles"], [])

    def test_list_users_with_roles_excludes_inactive(self):
        """Inactive users do not appear in list_users_with_roles."""
        # Deactivate a user temporarily
        user = _get_user()
        original_active = user.is_active
        user.is_active = False
        user.save()

        try:
            results = UserRoleService.list_users_with_roles()
            ids = [e["id"] for e in results]
            self.assertNotIn(str(user.id), ids)
        finally:
            user.is_active = original_active
            user.save()
