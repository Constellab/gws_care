"""Unit tests for CampaignService."""

import uuid
from datetime import date

from gws_care.account.account_dto import SaveAccountDTO
from gws_care.account.account_service import AccountService
from gws_care.campaign.campaign_dto import SaveCampaignDTO
from gws_care.campaign.campaign_service import CampaignService
from gws_care.campaign.campaign_status import CampaignStatus
from gws_care.exam.exam_type import ExamType
from gws_care.exam.exam_type_dto import SaveExamTypeModelDTO
from gws_care.exam.exam_type_service import ExamTypeService
from gws_care.patient.patient_dto import SavePatientDTO
from gws_care.patient.patient_service import PatientService
from gws_care.role.care_role import CareRole
from gws_care.role.user_care_role import UserCareRole
from gws_care.role.user_role_service import UserRoleService
from gws_care.user.care_user_sync_service import CareUserSyncService
from gws_core import BadRequestException, BaseTestCase, NotFoundException

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_account(name: str | None = None) -> "Account":
    if name is None:
        name = f"Test Account {uuid.uuid4().hex[:8]}"
    return AccountService.create_account(SaveAccountDTO(name=name))


def _make_patient(account=None) -> "Patient":
    dto = SavePatientDTO(
        last_name="Doe",
        first_name="Jane",
        date_of_birth=date(1985, 6, 15),
        gender="F",
        account_id=str(account.id) if account else None,
    )
    return PatientService.create_patient(dto)


def _make_exam_type(code: str = "ET1") -> "ExamTypeModel":
    return ExamTypeService.create_exam_type(
        SaveExamTypeModelDTO(code=code, name=f"Exam {code}", category=ExamType.CLINICAL.value)
    )


def _make_campaign(account=None, **kwargs):
    if account is None:
        account = _make_account()
    defaults = {
        "name": "Campaign 2025",
        "account_id": str(account.id),
        "start_date": "2025-06-01",
        "end_date": "2025-06-30",
    }
    defaults.update(kwargs)
    return CampaignService.create_campaign(SaveCampaignDTO(**defaults)), account


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestCampaignService(BaseTestCase):
    """Tests for CampaignService: CRUD, lifecycle, and patient/exam_type management."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    # ── create ───────────────────────────────────────────────────────────────

    def test_create_campaign_happy_path(self):
        """Campaign is created with DRAFT status and auto campaign_number."""
        campaign, _ = _make_campaign()
        self.assertIsNotNone(campaign.id)
        self.assertTrue(campaign.campaign_number.startswith("PRG-"))
        self.assertEqual(campaign.status, CampaignStatus.DRAFT)
        self.assertEqual(campaign.name, "Campaign 2025")

    def test_create_campaign_missing_name_raises(self):
        account = _make_account()
        with self.assertRaises(BadRequestException):
            CampaignService.create_campaign(
                SaveCampaignDTO(name="", account_id=str(account.id), start_date="2025-01-01", end_date="2025-01-31")
            )

    def test_create_campaign_invalid_dates_raises(self):
        account = _make_account()
        with self.assertRaises(BadRequestException):
            CampaignService.create_campaign(
                SaveCampaignDTO(name="Bad", account_id=str(account.id), start_date="2025-12-01", end_date="2025-01-01")
            )

    def test_create_campaign_unknown_account_raises(self):
        with self.assertRaises(BadRequestException):
            CampaignService.create_campaign(
                SaveCampaignDTO(name="X", account_id="00000000-0000-0000-0000-000000000000", start_date="2025-01-01", end_date="2025-01-31")
            )

    # ── get / list ────────────────────────────────────────────────────────────

    def test_get_campaign_not_found_raises(self):
        with self.assertRaises(NotFoundException):
            CampaignService.get_campaign("00000000-0000-0000-0000-000000000000")

    def test_list_campaigns_by_account(self):
        account = _make_account("FilterAcct")
        _make_campaign(account=account)
        _make_campaign(account=account)
        campaigns = CampaignService.list_campaigns(account_id=str(account.id))
        self.assertEqual(len(campaigns), 2)

    def test_list_campaigns_by_status(self):
        campaign, _ = _make_campaign()
        # Validate it to change status
        from gws_care.user.user import User
        user = User.select().first()
        CampaignService.validate_campaign(str(campaign.id), user)
        validated = CampaignService.list_campaigns(status=CampaignStatus.VALIDATED)
        ids = [str(c.id) for c in validated]
        self.assertIn(str(campaign.id), ids)

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def test_full_lifecycle(self):
        """Campaign progresses through DRAFT → VALIDATED → IN_PROGRESS → LAB_DONE → ..."""
        from gws_care.user.user import User
        user = User.select().first()
        campaign, _ = _make_campaign()

        # DRAFT → VALIDATED
        campaign = CampaignService.validate_campaign(str(campaign.id), user)
        self.assertEqual(campaign.status, CampaignStatus.VALIDATED)

        # VALIDATED → TERRAIN_EXAM
        campaign = CampaignService.start_campaign(str(campaign.id))
        self.assertEqual(campaign.status, CampaignStatus.TERRAIN_EXAM)

        # IN_PROGRESS → LAB_DONE (mark_lab_done was dead code, removed; set directly)
        campaign.status = CampaignStatus.LAB_DONE
        campaign.save()
        self.assertEqual(campaign.status, CampaignStatus.LAB_DONE)

        # LAB_DONE → DOCTOR_CLINIC_VALIDATED
        campaign = CampaignService.validate_doctor_clinic(str(campaign.id))
        self.assertEqual(campaign.status, CampaignStatus.DOCTOR_CLINIC_VALIDATED)

        # DOCTOR_CLINIC_VALIDATED → DOCTOR_COMPANY_VALIDATED
        campaign = CampaignService.validate_doctor_company(str(campaign.id))
        self.assertEqual(campaign.status, CampaignStatus.DOCTOR_COMPANY_VALIDATED)

    def test_validate_campaign_wrong_status_raises(self):
        campaign, _ = _make_campaign()
        from gws_care.user.user import User
        user = User.select().first()
        CampaignService.validate_campaign(str(campaign.id), user)  # now VALIDATED
        with self.assertRaises(BadRequestException):
            CampaignService.validate_campaign(str(campaign.id), user)  # not DRAFT anymore

    def test_start_campaign_requires_validated_status(self):
        campaign, _ = _make_campaign()  # DRAFT
        with self.assertRaises(BadRequestException):
            CampaignService.start_campaign(str(campaign.id))

    def test_archive_campaign(self):
        campaign, _ = _make_campaign()
        campaign = CampaignService.archive_campaign(str(campaign.id))
        self.assertEqual(campaign.status, CampaignStatus.ARCHIVED)

    # ── patient management ────────────────────────────────────────────────────

    def test_add_patient_to_campaign(self):
        account = _make_account("PtAcct")
        campaign, _ = _make_campaign(account=account)
        patient = _make_patient(account=account)

        CampaignService.add_patient(str(campaign.id), str(patient.id))
        patients = CampaignService.get_patients(str(campaign.id))
        self.assertEqual(len(patients), 1)
        self.assertEqual(str(patients[0].id), str(patient.id))

    def test_add_patient_wrong_account_raises(self):
        account1 = _make_account("Acct1")
        account2 = _make_account("Acct2")
        campaign, _ = _make_campaign(account=account1)
        patient = _make_patient(account=account2)  # different account

        with self.assertRaises(BadRequestException):
            CampaignService.add_patient(str(campaign.id), str(patient.id))

    def test_add_patient_duplicate_raises(self):
        account = _make_account("DupPtAcct")
        campaign, _ = _make_campaign(account=account)
        patient = _make_patient(account=account)

        CampaignService.add_patient(str(campaign.id), str(patient.id))
        with self.assertRaises(BadRequestException):
            CampaignService.add_patient(str(campaign.id), str(patient.id))

    def test_remove_patient_from_campaign(self):
        account = _make_account("RemPtAcct")
        campaign, _ = _make_campaign(account=account)
        patient = _make_patient(account=account)

        CampaignService.add_patient(str(campaign.id), str(patient.id))
        CampaignService.remove_patient(str(campaign.id), str(patient.id))
        patients = CampaignService.get_patients(str(campaign.id))
        self.assertEqual(len(patients), 0)

    def test_add_patient_to_in_progress_campaign_raises(self):
        from gws_care.user.user import User
        user = User.select().first()
        account = _make_account("ProgAcct")
        campaign, _ = _make_campaign(account=account)
        patient = _make_patient(account=account)

        CampaignService.validate_campaign(str(campaign.id), user)
        CampaignService.start_campaign(str(campaign.id))

        with self.assertRaises(BadRequestException):
            CampaignService.add_patient(str(campaign.id), str(patient.id))

    # ── exam type management ──────────────────────────────────────────────────

    def test_add_exam_type_to_campaign(self):
        campaign, _ = _make_campaign()
        exam_type = _make_exam_type("ETC1")

        CampaignService.add_exam_type(str(campaign.id), str(exam_type.id))
        exam_types = CampaignService.get_exam_types(str(campaign.id))
        self.assertEqual(len(exam_types), 1)
        self.assertEqual(exam_types[0].code, "ETC1")

    def test_add_exam_type_duplicate_raises(self):
        campaign, _ = _make_campaign()
        et = _make_exam_type("ETDUP")
        CampaignService.add_exam_type(str(campaign.id), str(et.id))
        with self.assertRaises(BadRequestException):
            CampaignService.add_exam_type(str(campaign.id), str(et.id))

    def test_add_inactive_exam_type_raises(self):
        campaign, _ = _make_campaign()
        et = _make_exam_type("ETINACT")
        ExamTypeService.deactivate_exam_type(str(et.id))
        with self.assertRaises(BadRequestException):
            CampaignService.add_exam_type(str(campaign.id), str(et.id))

    def test_remove_exam_type_from_campaign(self):
        campaign, _ = _make_campaign()
        et = _make_exam_type("ETREM")
        CampaignService.add_exam_type(str(campaign.id), str(et.id))
        CampaignService.remove_exam_type(str(campaign.id), str(et.id))
        exam_types = CampaignService.get_exam_types(str(campaign.id))
        self.assertEqual(len(exam_types), 0)

    # ── to_row_dto ────────────────────────────────────────────────────────────

    def test_to_row_dto_counts(self):
        account = _make_account("RowDtoAcct")
        campaign, _ = _make_campaign(account=account)
        patient = _make_patient(account=account)
        et = _make_exam_type("ETROW")

        CampaignService.add_patient(str(campaign.id), str(patient.id))
        CampaignService.add_exam_type(str(campaign.id), str(et.id))

        row = CampaignService.to_row_dto(campaign)
        self.assertEqual(row.patient_count, 1)
        self.assertEqual(row.exam_type_count, 1)
        self.assertEqual(row.status, CampaignStatus.DRAFT.value)


# ── Phase 2 — Validation workflow tests ──────────────────────────────────────

def _make_campaign_in_progress():
    """Create a campaign with one patient/visit and advance to TERRAIN_EXAM.

    Returns (campaign, patient, user).
    """
    from gws_care.user.user import User

    user = User.select().first()
    account = _make_account()
    patient = _make_patient(account=account)
    campaign, _ = _make_campaign(account=account)
    CampaignService.add_patient(str(campaign.id), str(patient.id))
    CampaignService.validate_campaign(str(campaign.id), user)
    campaign = CampaignService.start_campaign(str(campaign.id))
    return campaign, patient, user


def _advance_visit_to_lab_validated(campaign, patient, user):
    """Helper: bring the visit all the way to LAB_DONE."""
    from gws_care.visit.visit import Visit
    from gws_care.visit.campaign_visit_service import CampaignVisitService

    visit = Visit.get((Visit.campaign == campaign.id) & (Visit.patient == patient.id))
    vid = str(visit.id)
    CampaignVisitService.mark_terrain_done(vid)
    CampaignVisitService.validate_lab(vid, user)
    return Visit.get_by_id(visit.id)


def _advance_visit_to_clinic_validated(campaign, patient, user):
    """Helper: bring the visit all the way to DOCTOR_CLINIC_VALIDATED."""
    from gws_care.visit.visit import Visit
    from gws_care.visit.visit_dto import ValidateDoctorClinicDTO
    from gws_care.visit.campaign_visit_service import CampaignVisitService

    _advance_visit_to_lab_validated(campaign, patient, user)
    visit = Visit.get((Visit.campaign == campaign.id) & (Visit.patient == patient.id))
    CampaignVisitService.validate_doctor_clinic(
        str(visit.id), user, ValidateDoctorClinicDTO(interpretation="Normal.")
    )
    return Visit.get_by_id(visit.id)


class TestCampaignPhase2(BaseTestCase):
    """Phase 2 — Validation workflow tests for CampaignService."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    def setUp(self):
        # Ensure the test user has ADMIN role so permission guards don't block
        # the business-logic assertions being tested here.
        UserCareRole.delete().execute()
        from gws_care.user.user import User
        user = User.select().first()
        if user:
            UserRoleService.assign_role(str(user.id), CareRole.ADMIN)

    # ── validate_lab_campaign ─────────────────────────────────────────────────

    def test_validate_lab_campaign_happy_path(self):
        """All visits LAB_VALIDATED → campaign becomes LAB_DONE."""
        campaign, patient, user = _make_campaign_in_progress()
        _advance_visit_to_lab_validated(campaign, patient, user)

        campaign = CampaignService.validate_lab_campaign(str(campaign.id), user)
        self.assertEqual(campaign.status, CampaignStatus.LAB_DONE)

    def test_validate_lab_campaign_not_all_validated_raises(self):
        """validate_lab_campaign raises if any visit is not LAB_VALIDATED."""
        campaign, patient, user = _make_campaign_in_progress()
        # CampaignVisit stays PENDING → should raise

        with self.assertRaises(BadRequestException):
            CampaignService.validate_lab_campaign(str(campaign.id), user)

    def test_validate_lab_campaign_wrong_status_raises(self):
        """validate_lab_campaign raises if campaign is not IN_PROGRESS."""
        campaign, _ = _make_campaign()  # DRAFT

        user = __import__("gws_care.user.user", fromlist=["User"]).User.select().first()
        with self.assertRaises(BadRequestException):
            CampaignService.validate_lab_campaign(str(campaign.id), user)

    def test_validate_lab_campaign_no_visits_raises(self):
        """validate_lab_campaign raises if campaign has no visits."""
        from gws_care.user.user import User
        user = User.select().first()

        # IN_PROGRESS campaign with no patients → no visits
        account = _make_account("NoVisitAcct")
        campaign, _ = _make_campaign(account=account)
        CampaignService.validate_campaign(str(campaign.id), user)
        campaign = CampaignService.start_campaign(str(campaign.id))

        with self.assertRaises(BadRequestException):
            CampaignService.validate_lab_campaign(str(campaign.id), user)

    # ── validate_doctor_clinic_campaign ───────────────────────────────────────

    def test_validate_doctor_clinic_campaign_happy_path(self):
        """All visits DOCTOR_CLINIC_VALIDATED → campaign becomes DOCTOR_CLINIC_VALIDATED."""
        campaign, patient, user = _make_campaign_in_progress()
        _advance_visit_to_clinic_validated(campaign, patient, user)

        campaign = CampaignService.validate_lab_campaign(str(campaign.id), user)
        campaign = CampaignService.validate_doctor_clinic_campaign(str(campaign.id), user)
        self.assertEqual(campaign.status, CampaignStatus.DOCTOR_CLINIC_VALIDATED)

    def test_validate_doctor_clinic_campaign_not_all_validated_raises(self):
        """validate_doctor_clinic_campaign raises if any visit is not DOCTOR_CLINIC_VALIDATED."""
        campaign, patient, user = _make_campaign_in_progress()
        _advance_visit_to_lab_validated(campaign, patient, user)
        campaign = CampaignService.validate_lab_campaign(str(campaign.id), user)
        # CampaignVisit is LAB_VALIDATED, not DOCTOR_CLINIC_VALIDATED → should raise

        with self.assertRaises(BadRequestException):
            CampaignService.validate_doctor_clinic_campaign(str(campaign.id), user)

    def test_validate_doctor_clinic_campaign_wrong_status_raises(self):
        """validate_doctor_clinic_campaign raises if campaign is not LAB_DONE."""
        campaign, patient, user = _make_campaign_in_progress()

        with self.assertRaises(BadRequestException):
            CampaignService.validate_doctor_clinic_campaign(str(campaign.id), user)

    # ── check_and_advance_to_company_validated ────────────────────────────────

    def test_auto_advance_campaign_when_all_visits_company_validated(self):
        """Campaign auto-advances to DOCTOR_COMPANY_VALIDATED when all visits done."""
        from gws_care.visit.visit import Visit
        from gws_care.visit.visit_dto import ValidateDoctorCompanyDTO
        from gws_care.visit.campaign_visit_service import CampaignVisitService

        campaign, patient, user = _make_campaign_in_progress()
        _advance_visit_to_clinic_validated(campaign, patient, user)
        campaign = CampaignService.validate_lab_campaign(str(campaign.id), user)
        campaign = CampaignService.validate_doctor_clinic_campaign(str(campaign.id), user)

        visit = Visit.get((Visit.campaign == campaign.id) & (Visit.patient == patient.id))
        CampaignVisitService.validate_doctor_company(
            str(visit.id), user, ValidateDoctorCompanyDTO(interpretation="Apte.", message="RAS.")
        )

        # Campaign should now be auto-advanced
        from gws_care.campaign.campaign import Campaign
        updated_campaign = Campaign.get_by_id(campaign.id)
        self.assertEqual(updated_campaign.status, CampaignStatus.DOCTOR_COMPANY_VALIDATED)

    def test_no_auto_advance_when_some_visits_pending(self):
        """Campaign stays DOCTOR_CLINIC_VALIDATED when only some visits are done."""
        from gws_care.campaign.campaign import Campaign
        from gws_care.visit.visit import Visit
        from gws_care.visit.visit_dto import ValidateDoctorClinicDTO, ValidateDoctorCompanyDTO
        from gws_care.visit.campaign_visit_service import CampaignVisitService

        user = __import__("gws_care.user.user", fromlist=["User"]).User.select().first()
        account = _make_account("TwoPatAcct")
        patient1 = _make_patient(account=account)
        patient2 = _make_patient(account=account)
        campaign, _ = _make_campaign(account=account)
        CampaignService.add_patient(str(campaign.id), str(patient1.id))
        CampaignService.add_patient(str(campaign.id), str(patient2.id))
        CampaignService.validate_campaign(str(campaign.id), user)
        campaign = CampaignService.start_campaign(str(campaign.id))

        # Bring both visits to DOCTOR_CLINIC_VALIDATED
        for patient in [patient1, patient2]:
            visit = Visit.get((Visit.campaign == campaign.id) & (Visit.patient == patient.id))
            vid = str(visit.id)
            CampaignVisitService.mark_terrain_done(vid)
            CampaignVisitService.validate_lab(vid, user)
            CampaignVisitService.validate_doctor_clinic(vid, user, ValidateDoctorClinicDTO(interpretation="OK"))

        campaign = CampaignService.validate_lab_campaign(str(campaign.id), user)
        campaign = CampaignService.validate_doctor_clinic_campaign(str(campaign.id), user)

        # Validate only patient1's visit — patient2 still pending
        visit1 = Visit.get((Visit.campaign == campaign.id) & (Visit.patient == patient1.id))
        CampaignVisitService.validate_doctor_company(
            str(visit1.id), user, ValidateDoctorCompanyDTO(interpretation="Apte.", message="")
        )

        # Campaign must still be DOCTOR_CLINIC_VALIDATED
        updated = Campaign.get_by_id(campaign.id)
        self.assertEqual(updated.status, CampaignStatus.DOCTOR_CLINIC_VALIDATED)
