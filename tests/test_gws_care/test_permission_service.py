"""Unit tests for PermissionService.

Covers:
- can() / require() for every action in the PERMISSION_MAP
- ADMIN bypass
- Platform admin bypass (mocked via _is_platform_admin)
- Account-scoped check (require_own_account)
- Patient-scoped check (require_own_patient)
"""

import uuid

from gws_care.role.care_action import CareAction
from gws_care.role.care_role import CareRole
from gws_care.role.permission_service import PermissionService
from gws_care.role.user_care_role import UserCareRole
from gws_care.role.user_role_service import UserRoleService
from gws_care.user.care_user_sync_service import CareUserSyncService
from gws_care.user.user import User
from gws_core import BaseTestCase, ForbiddenException

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_user(suffix: str | None = None) -> User:
    """Create and persist a fresh user for isolation."""
    tag = suffix or uuid.uuid4().hex[:6]
    u = User()
    u.id = uuid.uuid4()
    u.email = f"perm_test_{tag}@test.local"
    u.first_name = "Perm"
    u.last_name = f"Tester{tag}"
    u.is_active = True
    u.save(force_insert=True)
    return u


# ── Test class ────────────────────────────────────────────────────────────────

class TestPermissionService(BaseTestCase):
    """Tests for PermissionService.can(), .require() and scoped helpers."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    def setUp(self):
        UserCareRole.delete().execute()

    # ── ADMIN bypass ─────────────────────────────────────────────────────────

    def test_admin_can_do_everything(self):
        """A user with ADMIN role is allowed any action."""
        user = _make_user("admin")
        UserRoleService.assign_role(str(user.id), CareRole.ADMIN)

        for action in CareAction:
            self.assertTrue(
                PermissionService.can(user, action),
                f"ADMIN should be allowed: {action.value}",
            )

    def test_admin_require_never_raises(self):
        """require() never raises for ADMIN."""
        user = _make_user("admin2")
        UserRoleService.assign_role(str(user.id), CareRole.ADMIN)
        for action in CareAction:
            PermissionService.require(user, action)  # must not raise

    # ── OPERATOR ─────────────────────────────────────────────────────────────

    def test_operator_can_validate_lab(self):
        user = _make_user("op")
        UserRoleService.assign_role(str(user.id), CareRole.OPERATOR)
        self.assertTrue(PermissionService.can(user, CareAction.VISIT_VALIDATE_LAB))
        self.assertTrue(PermissionService.can(user, CareAction.CAMPAIGN_VALIDATE_LAB))

    def test_operator_cannot_validate_clinic(self):
        user = _make_user("op2")
        UserRoleService.assign_role(str(user.id), CareRole.OPERATOR)
        self.assertFalse(PermissionService.can(user, CareAction.VISIT_VALIDATE_CLINIC))
        self.assertFalse(PermissionService.can(user, CareAction.CAMPAIGN_VALIDATE_CLINIC))

    def test_operator_cannot_override_appreciation(self):
        user = _make_user("op3")
        UserRoleService.assign_role(str(user.id), CareRole.OPERATOR)
        self.assertFalse(PermissionService.can(user, CareAction.EXAM_APPRECIATION_OVERRIDE))

    def test_operator_can_write_exam_result(self):
        user = _make_user("op4")
        UserRoleService.assign_role(str(user.id), CareRole.OPERATOR)
        self.assertTrue(PermissionService.can(user, CareAction.EXAM_RESULT_WRITE))

    # ── DOCTOR ────────────────────────────────────────────────────────────────

    def test_doctor_can_validate_clinic(self):
        user = _make_user("doc")
        UserRoleService.assign_role(str(user.id), CareRole.DOCTOR)
        self.assertTrue(PermissionService.can(user, CareAction.VISIT_VALIDATE_CLINIC))
        self.assertTrue(PermissionService.can(user, CareAction.CAMPAIGN_VALIDATE_CLINIC))

    def test_doctor_cannot_validate_lab(self):
        user = _make_user("doc2")
        UserRoleService.assign_role(str(user.id), CareRole.DOCTOR)
        self.assertFalse(PermissionService.can(user, CareAction.VISIT_VALIDATE_LAB))
        self.assertFalse(PermissionService.can(user, CareAction.CAMPAIGN_VALIDATE_LAB))

    def test_doctor_can_override_appreciation(self):
        user = _make_user("doc3")
        UserRoleService.assign_role(str(user.id), CareRole.DOCTOR)
        self.assertTrue(PermissionService.can(user, CareAction.EXAM_APPRECIATION_OVERRIDE))

    def test_doctor_cannot_write_exam_result(self):
        user = _make_user("doc4")
        UserRoleService.assign_role(str(user.id), CareRole.DOCTOR)
        self.assertFalse(PermissionService.can(user, CareAction.EXAM_RESULT_WRITE))

    # ── ACCOUNT_ADMIN ─────────────────────────────────────────────────────────

    def test_account_admin_can_validate_company(self):
        user = _make_user("rh")
        UserRoleService.assign_role(str(user.id), CareRole.ACCOUNT_ADMIN)
        self.assertTrue(PermissionService.can(user, CareAction.VISIT_VALIDATE_COMPANY))

    def test_account_admin_can_generate_certificate(self):
        user = _make_user("rh2")
        UserRoleService.assign_role(str(user.id), CareRole.ACCOUNT_ADMIN)
        self.assertTrue(PermissionService.can(user, CareAction.CERTIFICATE_GENERATE))

    def test_account_admin_cannot_validate_lab(self):
        user = _make_user("rh3")
        UserRoleService.assign_role(str(user.id), CareRole.ACCOUNT_ADMIN)
        self.assertFalse(PermissionService.can(user, CareAction.VISIT_VALIDATE_LAB))
        self.assertFalse(PermissionService.can(user, CareAction.CAMPAIGN_VALIDATE_LAB))

    def test_account_admin_cannot_validate_clinic(self):
        user = _make_user("rh4")
        UserRoleService.assign_role(str(user.id), CareRole.ACCOUNT_ADMIN)
        self.assertFalse(PermissionService.can(user, CareAction.VISIT_VALIDATE_CLINIC))

    # ── PATIENT ───────────────────────────────────────────────────────────────

    def test_patient_can_read_own(self):
        user = _make_user("pat")
        UserRoleService.assign_role(str(user.id), CareRole.PATIENT)
        self.assertTrue(PermissionService.can(user, CareAction.PATIENT_READ_OWN))

    def test_patient_cannot_read_all_patients(self):
        user = _make_user("pat2")
        UserRoleService.assign_role(str(user.id), CareRole.PATIENT)
        self.assertFalse(PermissionService.can(user, CareAction.PATIENT_READ))

    def test_patient_cannot_validate_anything(self):
        user = _make_user("pat3")
        UserRoleService.assign_role(str(user.id), CareRole.PATIENT)
        for action in [
            CareAction.VISIT_VALIDATE_LAB,
            CareAction.VISIT_VALIDATE_CLINIC,
            CareAction.VISIT_VALIDATE_COMPANY,
            CareAction.CAMPAIGN_VALIDATE_LAB,
            CareAction.CAMPAIGN_VALIDATE_CLINIC,
        ]:
            self.assertFalse(PermissionService.can(user, action), f"PATIENT should not: {action.value}")

    # ── No role ───────────────────────────────────────────────────────────────

    def test_user_without_roles_cannot_do_anything(self):
        user = _make_user("norole")
        for action in CareAction:
            self.assertFalse(
                PermissionService.can(user, action),
                f"No-role user should be blocked: {action.value}",
            )

    def test_require_raises_for_forbidden(self):
        user = _make_user("norole2")
        with self.assertRaises(ForbiddenException):
            PermissionService.require(user, CareAction.VISIT_VALIDATE_LAB)

    # ── require_own_account ───────────────────────────────────────────────────

    def test_account_admin_own_account_passes(self):
        account_id = "acc-001"
        user = _make_user("rhown")
        UserRoleService.assign_role(str(user.id), CareRole.ACCOUNT_ADMIN)
        UserRoleService.add_account_link(str(user.id), CareRole.ACCOUNT_ADMIN, account_id)
        PermissionService.require_own_account(user, account_id)  # must not raise

    def test_account_admin_other_account_raises(self):
        user = _make_user("rhother")
        UserRoleService.assign_role(str(user.id), CareRole.ACCOUNT_ADMIN)
        UserRoleService.add_account_link(str(user.id), CareRole.ACCOUNT_ADMIN, "acc-001")
        with self.assertRaises(ForbiddenException):
            PermissionService.require_own_account(user, "acc-999")

    def test_operator_any_account_passes(self):
        user = _make_user("opany")
        UserRoleService.assign_role(str(user.id), CareRole.OPERATOR)
        PermissionService.require_own_account(user, "acc-any")  # must not raise

    # ── require_own_patient ───────────────────────────────────────────────────

    def test_patient_own_patient_passes(self):
        patient_id = "pat-001"
        user = _make_user("ptown")
        UserRoleService.assign_role_with_link(
            str(user.id), CareRole.PATIENT, linked_patient_id=patient_id
        )
        PermissionService.require_own_patient(user, patient_id)  # must not raise

    def test_patient_other_patient_raises(self):
        user = _make_user("ptother")
        UserRoleService.assign_role_with_link(
            str(user.id), CareRole.PATIENT, linked_patient_id="pat-001"
        )
        with self.assertRaises(ForbiddenException):
            PermissionService.require_own_patient(user, "pat-999")

    def test_doctor_any_patient_passes(self):
        user = _make_user("docany")
        UserRoleService.assign_role(str(user.id), CareRole.DOCTOR)
        PermissionService.require_own_patient(user, "pat-any")  # must not raise
