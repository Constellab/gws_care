"""Unit tests for CampaignVisitService."""

from datetime import date

from gws_care.account.account_dto import SaveAccountDTO
from gws_care.account.account_service import AccountService
from gws_care.campaign.campaign_dto import SaveCampaignDTO
from gws_care.campaign.campaign_service import CampaignService
from gws_care.patient.patient_dto import SavePatientDTO
from gws_care.patient.patient_service import PatientService
from gws_care.role.care_role import CareRole
from gws_care.role.user_care_role import UserCareRole
from gws_care.role.user_role_service import UserRoleService
from gws_care.user.care_user_sync_service import CareUserSyncService
from gws_care.user.user import User
from gws_care.visit.visit import Visit
from gws_care.visit.visit_dto import ValidateDoctorClinicDTO, ValidateDoctorCompanyDTO
from gws_care.visit.campaign_visit_service import CampaignVisitService
from gws_care.visit.campaign_visit_status import CampaignVisitStatus
from gws_core import BadRequestException, BaseTestCase, NotFoundException

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_account(name: str | None = None) -> "Account":
    import uuid
    if name is None:
        name = f"CampaignVisit Test Acct {uuid.uuid4().hex[:8]}"
    return AccountService.create_account(SaveAccountDTO(name=name))


def _make_patient(account=None) -> "Patient":
    return PatientService.create_patient(
        SavePatientDTO(
            last_name="Smith",
            first_name="John",
            date_of_birth=date(1990, 3, 10),
            gender="M",
            account_id=str(account.id) if account else None,
        )
    )


def _make_campaign_with_patient():
    """Returns (campaign, patient, user) with visit already auto-created by add_patient."""
    account = _make_account()
    patient = _make_patient(account=account)
    campaign = CampaignService.create_campaign(
        SaveCampaignDTO(
            name="CampaignVisit Cam",
            account_id=str(account.id),
            start_date="2025-07-01",
            end_date="2025-07-31",
        )
    )
    CampaignService.add_patient(str(campaign.id), str(patient.id))
    user = User.select().first()
    return campaign, patient, user


def _get_visit(campaign, patient) -> Visit:
    """Retrieve the visit auto-created by add_patient."""
    return Visit.get((Visit.campaign == campaign.id) & (Visit.patient == patient.id))


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestCampaignVisitService(BaseTestCase):
    """Tests for CampaignVisitService: creation and full validation lifecycle."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    def setUp(self):
        # Ensure the test user has ADMIN role so permission guards don't block
        # the business-logic assertions being tested here.
        UserCareRole.delete().execute()
        user = User.select().first()
        if user:
            UserRoleService.assign_role(str(user.id), CareRole.ADMIN)

    # ── create ───────────────────────────────────────────────────────────────

    def test_create_visit_happy_path(self):
        """CampaignVisit is auto-created with PENDING status when patient is added to campaign."""
        campaign, patient, _ = _make_campaign_with_patient()
        visit = _get_visit(campaign, patient)

        self.assertIsNotNone(visit.id)
        self.assertTrue(visit.visit_number.startswith("VIS-"))
        self.assertEqual(visit.campaign_visit_status, CampaignVisitStatus.PENDING)
        self.assertEqual(str(visit.campaign_id), str(campaign.id))
        self.assertEqual(str(visit.patient_id), str(patient.id))

    def test_create_visit_duplicate_raises(self):
        """A second visit for the same (campaign, patient) raises."""
        campaign, patient, _ = _make_campaign_with_patient()
        # Visit already created by add_patient; creating again must raise
        with self.assertRaises(BadRequestException):
            CampaignVisitService.create_visit(str(campaign.id), str(patient.id))

    def test_create_visit_patient_not_in_campaign_raises(self):
        """Creating a visit for a patient not enrolled in the campaign raises."""
        campaign, _, _ = _make_campaign_with_patient()
        account2 = _make_account("OtherAcct")
        other_patient = _make_patient(account=None)  # no account, not enrolled

        with self.assertRaises((BadRequestException, NotFoundException)):
            CampaignVisitService.create_visit(str(campaign.id), str(other_patient.id))

    def test_create_visit_unknown_campaign_raises(self):
        with self.assertRaises(NotFoundException):
            CampaignVisitService.create_visit("00000000-0000-0000-0000-000000000000", "some-patient-id")

    # ── get / list ────────────────────────────────────────────────────────────

    def test_get_visit_not_found_raises(self):
        with self.assertRaises(NotFoundException):
            CampaignVisitService.get_visit("00000000-0000-0000-0000-000000000000")

    def test_list_for_campaign(self):
        campaign, patient, _ = _make_campaign_with_patient()
        visits = CampaignVisitService.list_for_campaign(str(campaign.id))
        self.assertEqual(len(visits), 1)

    def test_list_for_patient(self):
        campaign, patient, _ = _make_campaign_with_patient()
        visits = CampaignVisitService.list_for_patient(str(patient.id))
        self.assertGreaterEqual(len(visits), 1)

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def test_full_lifecycle(self):
        """CampaignVisit progresses through PENDING → VISIT_DONE → LAB_DONE
        → DOCTOR_CLINIC_VALIDATED → DOCTOR_COMPANY_VALIDATED."""
        campaign, patient, user = _make_campaign_with_patient()
        visit = _get_visit(campaign, patient)
        vid = str(visit.id)

        # PENDING → VISIT_DONE
        visit = CampaignVisitService.mark_terrain_done(vid)
        self.assertEqual(visit.campaign_visit_status, CampaignVisitStatus.VISIT_DONE)

        # VISIT_DONE → LAB_DONE
        visit = CampaignVisitService.validate_lab(vid, user)
        self.assertEqual(visit.campaign_visit_status, CampaignVisitStatus.LAB_DONE)
        self.assertIsNotNone(visit.lab_validated_by_id)
        self.assertIsNotNone(visit.lab_validated_at)

        # LAB_DONE → DOCTOR_CLINIC_VALIDATED
        visit = CampaignVisitService.validate_doctor_clinic(
            vid, user, ValidateDoctorClinicDTO(interpretation="All normal.")
        )
        self.assertEqual(visit.campaign_visit_status, CampaignVisitStatus.DOCTOR_CLINIC_VALIDATED)
        self.assertEqual(visit.doctor_clinic_interpretation, "All normal.")

        # DOCTOR_CLINIC_VALIDATED → DOCTOR_COMPANY_VALIDATED
        visit = CampaignVisitService.validate_doctor_company(
            vid,
            user,
            ValidateDoctorCompanyDTO(interpretation="Aptitude confirmée.", message="Résultats satisfaisants."),
        )
        self.assertEqual(visit.campaign_visit_status, CampaignVisitStatus.DOCTOR_COMPANY_VALIDATED)
        self.assertEqual(visit.doctor_company_interpretation, "Aptitude confirmée.")
        self.assertEqual(visit.doctor_company_message, "Résultats satisfaisants.")

    def test_mark_terrain_done_wrong_status_raises(self):
        campaign, patient, _ = _make_campaign_with_patient()
        visit = _get_visit(campaign, patient)
        CampaignVisitService.mark_terrain_done(str(visit.id))  # now VISIT_DONE
        with self.assertRaises(BadRequestException):
            CampaignVisitService.mark_terrain_done(str(visit.id))  # not PENDING anymore

    def test_validate_lab_wrong_status_raises(self):
        campaign, patient, user = _make_campaign_with_patient()
        visit = _get_visit(campaign, patient)
        with self.assertRaises(BadRequestException):
            CampaignVisitService.validate_lab(str(visit.id), user)  # must be VISIT_DONE first

    def test_validate_doctor_clinic_wrong_status_raises(self):
        campaign, patient, user = _make_campaign_with_patient()
        visit = _get_visit(campaign, patient)
        with self.assertRaises(BadRequestException):
            CampaignVisitService.validate_doctor_clinic(
                str(visit.id), user, ValidateDoctorClinicDTO()
            )  # must be LAB_DONE first

    def test_validate_doctor_company_wrong_status_raises(self):
        campaign, patient, user = _make_campaign_with_patient()
        visit = _get_visit(campaign, patient)
        with self.assertRaises(BadRequestException):
            CampaignVisitService.validate_doctor_company(
                str(visit.id), user, ValidateDoctorCompanyDTO()
            )  # must be DOCTOR_CLINIC_VALIDATED first

    # ── to_row_dto ────────────────────────────────────────────────────────────

    def test_to_row_dto(self):
        campaign, patient, _ = _make_campaign_with_patient()
        visit = _get_visit(campaign, patient)
        row = CampaignVisitService.to_row_dto(visit)
        self.assertEqual(row.visit_number, visit.visit_number)
        self.assertEqual(row.campaign_visit_status, CampaignVisitStatus.PENDING.value)
        self.assertIsNotNone(row.patient_name)


# ── Phase 9 — Data integrity & metadata tests ─────────────────────────────────

class TestVisitValidationMetadata(BaseTestCase):
    """Phase 9: verify that validation metadata (timestamps, who validated) is
    correctly stored at each step of the workflow."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    def setUp(self):
        UserCareRole.delete().execute()
        user = User.select().first()
        if user:
            UserRoleService.assign_role(str(user.id), CareRole.ADMIN)

    def test_lab_validation_stores_user_and_timestamp(self):
        """validate_lab stores lab_validated_by and lab_validated_at."""
        campaign, patient, user = _make_campaign_with_patient()
        visit = _get_visit(campaign, patient)
        vid = str(visit.id)
        CampaignVisitService.mark_terrain_done(vid)
        visit = CampaignVisitService.validate_lab(vid, user)

        self.assertIsNotNone(visit.lab_validated_by_id)
        self.assertIsNotNone(visit.lab_validated_at)
        self.assertEqual(str(visit.lab_validated_by_id), str(user.id))

    def test_clinic_validation_stores_interpretation_and_metadata(self):
        """validate_doctor_clinic stores interpretation, validator and timestamp."""
        campaign, patient, user = _make_campaign_with_patient()
        visit = _get_visit(campaign, patient)
        vid = str(visit.id)
        CampaignVisitService.mark_terrain_done(vid)
        CampaignVisitService.validate_lab(vid, user)
        visit = CampaignVisitService.validate_doctor_clinic(
            vid, user, ValidateDoctorClinicDTO(interpretation="Bilan normal.")
        )

        self.assertEqual(visit.doctor_clinic_interpretation, "Bilan normal.")
        self.assertIsNotNone(visit.doctor_clinic_validated_by_id)
        self.assertIsNotNone(visit.doctor_clinic_validated_at)

    def test_company_validation_stores_message_and_interpretation(self):
        """validate_doctor_company stores both interpretation and patient message."""
        campaign, patient, user = _make_campaign_with_patient()
        visit = _get_visit(campaign, patient)
        vid = str(visit.id)
        CampaignVisitService.mark_terrain_done(vid)
        CampaignVisitService.validate_lab(vid, user)
        CampaignVisitService.validate_doctor_clinic(
            vid, user, ValidateDoctorClinicDTO(interpretation="OK.")
        )
        visit = CampaignVisitService.validate_doctor_company(
            vid,
            user,
            ValidateDoctorCompanyDTO(interpretation="Apte.", message="Aucune restriction."),
        )

        self.assertEqual(visit.doctor_company_interpretation, "Apte.")
        self.assertEqual(visit.doctor_company_message, "Aucune restriction.")
        self.assertIsNotNone(visit.doctor_company_validated_at)

    def test_clinic_validation_with_empty_interpretation(self):
        """validate_doctor_clinic accepts empty interpretation (optional field)."""
        campaign, patient, user = _make_campaign_with_patient()
        visit = _get_visit(campaign, patient)
        vid = str(visit.id)
        CampaignVisitService.mark_terrain_done(vid)
        CampaignVisitService.validate_lab(vid, user)
        visit = CampaignVisitService.validate_doctor_clinic(
            vid, user, ValidateDoctorClinicDTO(interpretation="")
        )

        self.assertEqual(visit.campaign_visit_status, CampaignVisitStatus.DOCTOR_CLINIC_VALIDATED)

    def test_cannot_skip_visit_done_step(self):
        """Cannot go from PENDING directly to LAB_DONE."""
        campaign, patient, user = _make_campaign_with_patient()
        visit = _get_visit(campaign, patient)
        with self.assertRaises(BadRequestException):
            CampaignVisitService.validate_lab(str(visit.id), user)

    def test_cannot_skip_lab_done_step(self):
        """Cannot go from VISIT_DONE directly to DOCTOR_CLINIC_VALIDATED."""
        campaign, patient, user = _make_campaign_with_patient()
        visit = _get_visit(campaign, patient)
        CampaignVisitService.mark_terrain_done(str(visit.id))
        with self.assertRaises(BadRequestException):
            CampaignVisitService.validate_doctor_clinic(str(visit.id), user, ValidateDoctorClinicDTO())

    def test_cannot_skip_clinic_validated_step(self):
        """Cannot go from LAB_DONE directly to DOCTOR_COMPANY_VALIDATED."""
        campaign, patient, user = _make_campaign_with_patient()
        visit = _get_visit(campaign, patient)
        CampaignVisitService.mark_terrain_done(str(visit.id))
        CampaignVisitService.validate_lab(str(visit.id), user)
        with self.assertRaises(BadRequestException):
            CampaignVisitService.validate_doctor_company(str(visit.id), user, ValidateDoctorCompanyDTO())

    def test_visit_number_is_unique_across_different_patients(self):
        """Each visit gets a unique visit_number even within the same campaign."""
        account = _make_account("UniqueNum Acct")
        campaign = CampaignService.create_campaign(
            SaveCampaignDTO(
                name="UniqueNum Camp",
                account_id=str(account.id),
                start_date="2025-11-01",
                end_date="2025-11-30",
            )
        )
        patient_a = _make_patient(account=account)
        patient_b = _make_patient(account=account)
        CampaignService.add_patient(str(campaign.id), str(patient_a.id))
        CampaignService.add_patient(str(campaign.id), str(patient_b.id))

        visit_a = _get_visit(campaign, patient_a)
        visit_b = _get_visit(campaign, patient_b)

        self.assertNotEqual(visit_a.visit_number, visit_b.visit_number)

    def test_visit_number_format(self):
        """CampaignVisit number starts with the VIS- prefix."""
        campaign, patient, _ = _make_campaign_with_patient()
        visit = _get_visit(campaign, patient)
        self.assertTrue(
            visit.visit_number.startswith("VIS-"),
            f"Expected 'VIS-…', got '{visit.visit_number}'"
        )

    def test_list_for_campaign_returns_only_that_campaign_visits(self):
        """list_for_campaign is isolated to the requested campaign."""
        account = _make_account("Iso Acct")
        campaign_a = CampaignService.create_campaign(
            SaveCampaignDTO(
                name="Camp A",
                account_id=str(account.id),
                start_date="2025-08-01",
                end_date="2025-08-31",
            )
        )
        campaign_b = CampaignService.create_campaign(
            SaveCampaignDTO(
                name="Camp B",
                account_id=str(account.id),
                start_date="2025-09-01",
                end_date="2025-09-30",
            )
        )
        patient_a = _make_patient(account=account)
        patient_b = _make_patient(account=account)
        CampaignService.add_patient(str(campaign_a.id), str(patient_a.id))
        CampaignService.add_patient(str(campaign_b.id), str(patient_b.id))

        visits_b = CampaignVisitService.list_for_campaign(str(campaign_b.id))
        visits_a = CampaignVisitService.list_for_campaign(str(campaign_a.id))

        self.assertEqual(len(visits_a), 1)
        self.assertEqual(len(visits_b), 1)
        self.assertEqual(str(visits_a[0].campaign_id), str(campaign_a.id))
        self.assertEqual(str(visits_b[0].campaign_id), str(campaign_b.id))
