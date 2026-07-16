"""Unit tests for CampaignService doctor-scope helpers and PermissionService.require_campaign_doctor_scope.

Covers the isolation mechanism that replaced the MEDECIN_PSC / MEDECIN_ENTREPRISE
role split: a doctor's visibility on a campaign ("internal" vs "company" vs
"none") is now derived from CampaignExamDoctor / CampaignDoctor assignment
rather than from a role.
"""

import uuid
from datetime import date

from gws_care.account.account_dto import SaveAccountDTO
from gws_care.account.account_service import AccountService
from gws_care.campaign.campaign_dto import SaveCampaignDTO
from gws_care.campaign.campaign_service import CampaignService
from gws_care.doctor.medical_doctor import MedicalDoctor
from gws_care.exam_type_ref.exam_type_ref_dto import SaveExamTypeRefDTO
from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService
from gws_care.role.care_role import CareRole
from gws_care.role.permission_service import PermissionService
from gws_care.user.care_user_sync_service import CareUserSyncService
from gws_care.user.user import User
from gws_core import BaseTestCase, ForbiddenException

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_user(suffix: str | None = None) -> User:
    tag = suffix or uuid.uuid4().hex[:6]
    u = User()
    u.id = uuid.uuid4()
    u.email = f"scope_test_{tag}@test.local"
    u.first_name = "Scope"
    u.last_name = f"Tester{tag}"
    u.is_active = True
    u.save(force_insert=True)
    return u


def _make_doctor(user: User | None = None, suffix: str | None = None) -> MedicalDoctor:
    tag = suffix or uuid.uuid4().hex[:6]
    d = MedicalDoctor()
    d.first_name = "Doc"
    d.last_name = f"Tor{tag}"
    d.is_active = True
    d.is_archived = False
    if user is not None:
        d.user = user
    d.save(force_insert=True)
    return d


def _make_account() -> "Account":
    return AccountService.create_account(SaveAccountDTO(name=f"Scope Test Account {uuid.uuid4().hex[:8]}"))


def _make_campaign():
    account = _make_account()
    campaign = CampaignService.create_campaign(SaveCampaignDTO(
        name="Scope Test Campaign",
        account_id=str(account.id),
        start_date="2025-06-01",
        end_date="2025-06-30",
    ))
    return campaign


def _make_exam_ref(suffix: str | None = None):
    tag = suffix or uuid.uuid4().hex[:6]
    dto = ExamTypeRefService.create(SaveExamTypeRefDTO(name=f"Exam Ref {tag}", category="OTHER"))
    return dto


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestCampaignDoctorScope(BaseTestCase):
    """Tests for CampaignService.get_doctor_scope_for_campaign and related helpers."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    def test_scope_none_when_no_medical_doctor_profile(self):
        """A user with no MedicalDoctor profile at all has scope 'none'."""
        campaign = _make_campaign()
        user = _make_user("nodoc")
        scope = CampaignService.get_doctor_scope_for_campaign(str(campaign.id), str(user.id))
        self.assertEqual(scope, "none")

    def test_scope_none_when_doctor_not_assigned_to_campaign(self):
        """A MedicalDoctor exists but was never assigned to this campaign."""
        campaign = _make_campaign()
        user = _make_user("unassigned")
        _make_doctor(user=user, suffix="unassigned")
        scope = CampaignService.get_doctor_scope_for_campaign(str(campaign.id), str(user.id))
        self.assertEqual(scope, "none")

    def test_scope_company_when_only_in_doctor_pool(self):
        """A doctor added via the campaign 'Doctors' tab only (no exam assignment) is 'company'."""
        campaign = _make_campaign()
        user = _make_user("company")
        doctor = _make_doctor(user=user, suffix="company")
        CampaignService.add_doctor_to_campaign(str(campaign.id), str(doctor.id))
        scope = CampaignService.get_doctor_scope_for_campaign(str(campaign.id), str(user.id))
        self.assertEqual(scope, "company")

    def test_scope_internal_when_assigned_to_exam(self):
        """A doctor assigned to an exam ref on the campaign is 'internal' (first interpretation)."""
        campaign = _make_campaign()
        user = _make_user("internal")
        doctor = _make_doctor(user=user, suffix="internal")
        exam_ref = _make_exam_ref("internal")
        CampaignService.add_exam_ref(str(campaign.id), exam_ref.id)
        CampaignService.assign_doctors_to_exam_ref(str(campaign.id), exam_ref.id, [str(doctor.id)])
        scope = CampaignService.get_doctor_scope_for_campaign(str(campaign.id), str(user.id))
        self.assertEqual(scope, "internal")

    def test_internal_doctor_also_in_campaign_doctor_pool(self):
        """Exam-level assignment cascades into CampaignDoctor, but scope stays 'internal', not 'company'."""
        campaign = _make_campaign()
        user = _make_user("cascade")
        doctor = _make_doctor(user=user, suffix="cascade")
        exam_ref = _make_exam_ref("cascade")
        CampaignService.add_exam_ref(str(campaign.id), exam_ref.id)
        CampaignService.assign_doctors_to_exam_ref(str(campaign.id), exam_ref.id, [str(doctor.id)])
        campaign_doctors = CampaignService.list_campaign_doctors(str(campaign.id))
        self.assertIn(str(doctor.id), [str(d.id) for d in campaign_doctors])
        scope = CampaignService.get_doctor_scope_for_campaign(str(campaign.id), str(user.id))
        self.assertEqual(scope, "internal")

    def test_get_internal_doctor_user_ids_for_campaign(self):
        campaign = _make_campaign()
        user = _make_user("listinternal")
        doctor = _make_doctor(user=user, suffix="listinternal")
        exam_ref = _make_exam_ref("listinternal")
        CampaignService.add_exam_ref(str(campaign.id), exam_ref.id)
        CampaignService.assign_doctors_to_exam_ref(str(campaign.id), exam_ref.id, [str(doctor.id)])
        ids = CampaignService.get_internal_doctor_user_ids_for_campaign(str(campaign.id))
        self.assertEqual(ids, [str(user.id)])

    def test_get_company_doctor_user_ids_excludes_internal(self):
        campaign = _make_campaign()
        internal_user = _make_user("compinternal")
        internal_doctor = _make_doctor(user=internal_user, suffix="compinternal")
        exam_ref = _make_exam_ref("compinternal")
        CampaignService.add_exam_ref(str(campaign.id), exam_ref.id)
        CampaignService.assign_doctors_to_exam_ref(str(campaign.id), exam_ref.id, [str(internal_doctor.id)])

        company_user = _make_user("componly")
        company_doctor = _make_doctor(user=company_user, suffix="componly")
        CampaignService.add_doctor_to_campaign(str(campaign.id), str(company_doctor.id))

        company_ids = CampaignService.get_company_doctor_user_ids_for_campaign(str(campaign.id))
        self.assertEqual(company_ids, [str(company_user.id)])
        self.assertNotIn(str(internal_user.id), company_ids)

    # ── PermissionService.require_campaign_doctor_scope ───────────────────────

    def test_require_campaign_doctor_scope_admin_bypasses(self):
        campaign = _make_campaign()
        user = _make_user("permadmin")
        from gws_care.role.user_role_service import UserRoleService
        UserRoleService.assign_role(str(user.id), CareRole.ADMIN)
        # No doctor profile / assignment at all — still passes for ADMIN.
        PermissionService.require_campaign_doctor_scope(user, str(campaign.id), {"internal"})

    def test_require_campaign_doctor_scope_raises_for_wrong_scope(self):
        campaign = _make_campaign()
        user = _make_user("permcompany")
        doctor = _make_doctor(user=user, suffix="permcompany")
        CampaignService.add_doctor_to_campaign(str(campaign.id), str(doctor.id))
        # User is "company"-scoped, not "internal" — must raise.
        with self.assertRaises(ForbiddenException):
            PermissionService.require_campaign_doctor_scope(user, str(campaign.id), {"internal"})

    def test_require_campaign_doctor_scope_passes_for_matching_scope(self):
        campaign = _make_campaign()
        user = _make_user("permmatch")
        doctor = _make_doctor(user=user, suffix="permmatch")
        exam_ref = _make_exam_ref("permmatch")
        CampaignService.add_exam_ref(str(campaign.id), exam_ref.id)
        CampaignService.assign_doctors_to_exam_ref(str(campaign.id), exam_ref.id, [str(doctor.id)])
        PermissionService.require_campaign_doctor_scope(user, str(campaign.id), {"internal"})
