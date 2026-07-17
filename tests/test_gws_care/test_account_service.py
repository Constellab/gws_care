"""Unit tests for AccountService."""

import uuid

from gws_care.account.account_dto import SaveAccountDTO
from gws_care.account.account_service import AccountService
from gws_care.role.care_role import CareRole
from gws_care.user.care_user_sync_service import CareUserSyncService
from gws_care.user.user import User
from gws_core import BadRequestException, BaseTestCase, ForbiddenException, NotFoundException

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_account_dto(**kwargs) -> SaveAccountDTO:
    """Return a valid SaveAccountDTO, overridable via kwargs."""
    defaults = {"name": "TestCorp"}
    defaults.update(kwargs)
    return SaveAccountDTO(**defaults)


def _make_user(suffix: str | None = None) -> User:
    tag = suffix or uuid.uuid4().hex[:6]
    u = User()
    u.id = uuid.uuid4()
    u.email = f"account_svc_test_{tag}@test.local"
    u.first_name = "Test"
    u.last_name = f"User{tag}"
    u.is_active = True
    u.save(force_insert=True)
    return u


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestAccountService(BaseTestCase):
    """Tests for AccountService CRUD and deactivation."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    # ── create_account ────────────────────────────────────────────────────────

    def test_create_account_happy_path(self):
        """Account is created with all provided fields persisted."""
        dto = SaveAccountDTO(
            name="Dupont Industries",
            registration_number="RCS123",
            address="1 rue de la Paix",
            postal_code="75001",
            city="Paris",
            phone="0140000000",
            email="contact@dupont.fr",
            contact_name="M. Dupont",
        )
        account = AccountService.create_account(dto)

        self.assertIsNotNone(account.id)
        self.assertEqual(account.name, "Dupont Industries")
        self.assertEqual(account.registration_number, "RCS123")
        self.assertEqual(account.address, "1 rue de la Paix")
        self.assertEqual(account.postal_code, "75001")
        self.assertEqual(account.city, "Paris")
        self.assertEqual(account.phone, "0140000000")
        self.assertEqual(account.email, "contact@dupont.fr")
        self.assertEqual(account.contact_name, "M. Dupont")
        self.assertTrue(account.is_active)

    def test_create_account_missing_name(self):
        """Empty name raises BadRequestException."""
        with self.assertRaises(BadRequestException):
            AccountService.create_account(_make_account_dto(name=""))

    def test_create_account_whitespace_name(self):
        """Whitespace-only name raises BadRequestException."""
        with self.assertRaises(BadRequestException):
            AccountService.create_account(_make_account_dto(name="   "))

    def test_create_account_name_stripped(self):
        """Leading/trailing whitespace in name is stripped."""
        account = AccountService.create_account(_make_account_dto(name="  AcmeCorp  "))
        self.assertEqual(account.name, "AcmeCorp")

    def test_create_account_minimal(self):
        """Account can be created with only a name (all other fields optional)."""
        account = AccountService.create_account(SaveAccountDTO(name="MinimalCorp"))
        self.assertIsNotNone(account.id)
        self.assertIsNone(account.phone)
        self.assertIsNone(account.email)

    # ── update_account ────────────────────────────────────────────────────────

    def test_update_account(self):
        """update_account changes mutable fields."""
        account = AccountService.create_account(_make_account_dto(name="BeforeUpdate"))
        updated = AccountService.update_account(
            str(account.id),
            _make_account_dto(name="AfterUpdate", city="Lyon", phone="0499001122"),
        )

        self.assertEqual(updated.name, "AfterUpdate")
        self.assertEqual(updated.city, "Lyon")
        self.assertEqual(updated.phone, "0499001122")

    def test_update_account_not_found(self):
        """update_account raises NotFoundException for unknown id."""
        with self.assertRaises(NotFoundException):
            AccountService.update_account(
                "00000000-0000-0000-0000-000000000000",
                _make_account_dto(),
            )

    # ── get_account ───────────────────────────────────────────────────────────

    def test_get_account_not_found(self):
        """get_account raises NotFoundException for unknown id."""
        with self.assertRaises(NotFoundException):
            AccountService.get_account("00000000-0000-0000-0000-000000000000")

    def test_get_account_found(self):
        """get_account returns the correct account."""
        account = AccountService.create_account(_make_account_dto(name="GetAcct"))
        found = AccountService.get_account(str(account.id))
        self.assertEqual(str(found.id), str(account.id))

    def test_get_account_with_user_admin_bypasses(self):
        """get_account(user=...) never raises for an ADMIN caller."""
        from gws_care.role.user_role_service import UserRoleService
        account = AccountService.create_account(_make_account_dto(name="AdminAcct"))
        user = _make_user("admin")
        UserRoleService.assign_role(str(user.id), CareRole.ADMIN)
        found = AccountService.get_account(str(account.id), user=user)
        self.assertEqual(str(found.id), str(account.id))

    def test_get_account_with_user_rh_unlinked_raises(self):
        """get_account(user=...) raises for RH_ENTREPRISE without a link to this account."""
        from gws_care.role.user_role_service import UserRoleService
        account = AccountService.create_account(_make_account_dto(name="RhUnlinkedAcct"))
        user = _make_user("rhunlinked")
        UserRoleService.assign_role(str(user.id), CareRole.ACCOUNT_ADMIN)
        with self.assertRaises(ForbiddenException):
            AccountService.get_account(str(account.id), user=user)

    def test_get_account_with_user_rh_linked_succeeds(self):
        """get_account(user=...) succeeds for RH_ENTREPRISE linked to this account."""
        from gws_care.role.user_role_service import UserRoleService
        account = AccountService.create_account(_make_account_dto(name="RhLinkedAcct"))
        user = _make_user("rhlinked")
        UserRoleService.assign_role(str(user.id), CareRole.ACCOUNT_ADMIN)
        UserRoleService.add_account_link(str(user.id), CareRole.ACCOUNT_ADMIN, str(account.id))
        found = AccountService.get_account(str(account.id), user=user)
        self.assertEqual(str(found.id), str(account.id))

    # ── list_accounts ─────────────────────────────────────────────────────────

    def test_list_accounts_active_only_true(self):
        """Default list_accounts excludes deactivated accounts."""
        active = AccountService.create_account(_make_account_dto(name="ActiveListA"))
        inactive = AccountService.create_account(_make_account_dto(name="InactiveListA"))
        AccountService.deactivate_account(str(inactive.id))

        results = AccountService.list_accounts(active_only=True)
        ids = [str(a.id) for a in results]
        self.assertIn(str(active.id), ids)
        self.assertNotIn(str(inactive.id), ids)

    def test_list_accounts_active_only_false(self):
        """list_accounts(active_only=False) includes deactivated accounts."""
        inactive = AccountService.create_account(_make_account_dto(name="InactiveListB"))
        AccountService.deactivate_account(str(inactive.id))

        results = AccountService.list_accounts(active_only=False)
        ids = [str(a.id) for a in results]
        self.assertIn(str(inactive.id), ids)

    def test_list_accounts_ordered_by_name(self):
        """list_accounts returns accounts sorted alphabetically by name."""
        AccountService.create_account(_make_account_dto(name="ZetaCorp"))
        AccountService.create_account(_make_account_dto(name="AlphaCorp"))
        AccountService.create_account(_make_account_dto(name="MidCorp"))

        results = AccountService.list_accounts()
        names = [a.name for a in results]
        # Filter to only the ones we just created so the test is repeatable
        created = [n for n in names if n in {"ZetaCorp", "AlphaCorp", "MidCorp"}]
        self.assertEqual(created, sorted(created))

    # ── deactivate_account ────────────────────────────────────────────────────

    def test_deactivate_account(self):
        """deactivate_account sets is_active=False."""
        account = AccountService.create_account(_make_account_dto(name="DeactivateMe"))
        self.assertTrue(account.is_active)

        deactivated = AccountService.deactivate_account(str(account.id))
        self.assertFalse(deactivated.is_active)

    def test_deactivate_account_excluded_from_default_list(self):
        """Deactivated account no longer appears in list_accounts()."""
        account = AccountService.create_account(_make_account_dto(name="ExcludeMe"))
        AccountService.deactivate_account(str(account.id))

        results = AccountService.list_accounts()
        ids = [str(a.id) for a in results]
        self.assertNotIn(str(account.id), ids)

    def test_deactivate_already_inactive(self):
        """Calling deactivate again on an already-inactive account is safe."""
        account = AccountService.create_account(_make_account_dto(name="DoubleDeact"))
        AccountService.deactivate_account(str(account.id))
        # Should not raise
        result = AccountService.deactivate_account(str(account.id))
        self.assertFalse(result.is_active)

    def test_deactivate_account_not_found(self):
        """deactivate_account raises NotFoundException for unknown id."""
        with self.assertRaises(NotFoundException):
            AccountService.deactivate_account("00000000-0000-0000-0000-000000000000")
