"""Smoke tests for Phase 8 PDF generation.

These tests verify that the PDF generators run without exception and return
non-empty bytes for valid inputs.  They do NOT assert visual content.
"""

from datetime import date

from gws_care.account.account_dto import SaveAccountDTO
from gws_care.account.account_service import AccountService
from gws_care.campaign.campaign_dto import SaveCampaignDTO
from gws_care.campaign.campaign_service import CampaignService
from gws_care.certificate.medical_certificate import (
    MedicalCertificateService,
    SaveMedicalCertificateDTO,
)
from gws_care.patient.patient_dto import SavePatientDTO
from gws_care.patient.patient_service import PatientService
from gws_care.pdf import (
    generate_campaign_report_pdf,
    generate_certificate_pdf,
    generate_visit_results_pdf,
)
from gws_care.role.care_role import CareRole
from gws_care.role.user_care_role import UserCareRole
from gws_care.role.user_role_service import UserRoleService
from gws_care.user.care_user_sync_service import CareUserSyncService
from gws_care.user.user import User
from gws_care.campaign_visit.campaign_visit_dto import ValidateDoctorClinicDTO, ValidateDoctorCompanyDTO
from gws_care.campaign_visit.campaign_visit_service import CampaignVisitService
from gws_core import BaseTestCase

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_account(name: str = "PDF Test Acct"):
    return AccountService.create_account(SaveAccountDTO(name=name))


def _make_patient(account=None, email: str = "pdf@example.com"):
    return PatientService.create_patient(
        SavePatientDTO(
            last_name="Pdfuser",
            first_name="Test",
            date_of_birth=date(1985, 1, 1),
            gender="M",
            account_id=str(account.id) if account else None,
            email=email,
        )
    )


def _make_campaign(account):
    return CampaignService.create_campaign(
        SaveCampaignDTO(
            name="PDF Campaign",
            account_id=str(account.id),
            start_date="2025-10-01",
            end_date="2025-10-31",
        )
    )


def _get_admin_user() -> User:
    return User.select().first()


def _advance_to_visit_lab_validated(campaign, patient, user):
    """Create a visit and advance it to LAB_VALIDATED status."""
    visit = CampaignVisitService.create_visit(str(campaign.id), str(patient.id))
    CampaignVisitService.mark_terrain_done(str(visit.id))
    CampaignVisitService.mark_results_entered(str(visit.id))
    visit = CampaignVisitService.validate_lab(str(visit.id), user)
    return visit


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestCertificatePdfGeneration(BaseTestCase):
    """Smoke tests for generate_certificate_pdf."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    def setUp(self):
        UserCareRole.delete().execute()
        user = _get_admin_user()
        if user:
            UserRoleService.assign_role(str(user.id), CareRole.ADMIN)

    def test_certificate_pdf_returns_non_empty_bytes(self):
        """generate_certificate_pdf returns bytes for a valid certificate."""
        patient = _make_patient()
        user = _get_admin_user()
        cert = MedicalCertificateService.create_certificate(
            SaveMedicalCertificateDTO(
                patient_id=str(patient.id),
                issue_date=date.today().isoformat(),
                conclusion="Apte au travail.",
                is_fit_for_work=True,
            ),
            user,
        )

        pdf_bytes = generate_certificate_pdf(str(cert.id))

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 0)

    def test_certificate_pdf_is_valid_pdf_header(self):
        """The returned bytes start with the PDF magic number %%PDF."""
        patient = _make_patient(email="pdfhdr@example.com")
        user = _get_admin_user()
        cert = MedicalCertificateService.create_certificate(
            SaveMedicalCertificateDTO(
                patient_id=str(patient.id),
                issue_date=date.today().isoformat(),
                conclusion="Inapte.",
                is_fit_for_work=False,
                restrictions="Pas de port de charges.",
            ),
            user,
        )

        pdf_bytes = generate_certificate_pdf(str(cert.id))

        self.assertTrue(pdf_bytes.startswith(b"%PDF"), "PDF output should start with %%PDF")

    def test_certificate_pdf_not_fit_for_work(self):
        """PDF generation works for an inaptitude certificate."""
        patient = _make_patient(email="inapte@example.com")
        user = _get_admin_user()
        cert = MedicalCertificateService.create_certificate(
            SaveMedicalCertificateDTO(
                patient_id=str(patient.id),
                issue_date=date.today().isoformat(),
                conclusion="Inapte temporairement.",
                is_fit_for_work=False,
            ),
            user,
        )

        pdf_bytes = generate_certificate_pdf(str(cert.id))
        self.assertGreater(len(pdf_bytes), 0)

    def test_certificate_pdf_missing_id_raises(self):
        """generate_certificate_pdf raises for an unknown certificate ID."""
        with self.assertRaises(Exception):
            generate_certificate_pdf("00000000-0000-0000-0000-000000000000")


class TestCampaignReportPdfGeneration(BaseTestCase):
    """Smoke tests for generate_campaign_report_pdf."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    def setUp(self):
        UserCareRole.delete().execute()
        user = _get_admin_user()
        if user:
            UserRoleService.assign_role(str(user.id), CareRole.ADMIN)

    def test_campaign_report_pdf_empty_campaign(self):
        """Report PDF works for a campaign with no patients."""
        account = _make_account("Report Empty")
        campaign = _make_campaign(account)

        pdf_bytes = generate_campaign_report_pdf(str(campaign.id))

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 0)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_campaign_report_pdf_with_patients(self):
        """Report PDF works for a campaign with enrolled patients."""
        account = _make_account("Report With Patients")
        patient = _make_patient(account=account, email="rpt@example.com")
        campaign = _make_campaign(account)
        CampaignService.add_patient(str(campaign.id), str(patient.id))

        pdf_bytes = generate_campaign_report_pdf(str(campaign.id))

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_campaign_report_pdf_missing_id_raises(self):
        """generate_campaign_report_pdf raises for an unknown campaign ID."""
        with self.assertRaises(Exception):
            generate_campaign_report_pdf("00000000-0000-0000-0000-000000000000")


class TestVisitResultsPdfGeneration(BaseTestCase):
    """Smoke tests for generate_visit_results_pdf."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    def setUp(self):
        UserCareRole.delete().execute()
        user = _get_admin_user()
        if user:
            UserRoleService.assign_role(str(user.id), CareRole.ADMIN)

    def test_visit_results_pdf_pending_visit(self):
        """Results PDF works even for a PENDING visit (no results yet)."""
        account = _make_account("PDF Vis Empty")
        patient = _make_patient(account=account, email="visempty@example.com")
        campaign = _make_campaign(account)
        CampaignService.add_patient(str(campaign.id), str(patient.id))
        visit = CampaignVisitService.create_visit(str(campaign.id), str(patient.id))

        pdf_bytes = generate_visit_results_pdf(str(visit.id))

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 0)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_visit_results_pdf_lab_validated_visit(self):
        """Results PDF works for a LAB_VALIDATED visit."""
        account = _make_account("PDF Vis Lab")
        patient = _make_patient(account=account, email="vislab@example.com")
        campaign = _make_campaign(account)
        CampaignService.add_patient(str(campaign.id), str(patient.id))
        user = _get_admin_user()
        visit = _advance_to_visit_lab_validated(campaign, patient, user)

        pdf_bytes = generate_visit_results_pdf(str(visit.id))

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_visit_results_pdf_fully_validated_with_interpretations(self):
        """Results PDF works for a fully validated visit with interpretations."""
        account = _make_account("PDF Vis Full")
        patient = _make_patient(account=account, email="visfull@example.com")
        campaign = _make_campaign(account)
        CampaignService.add_patient(str(campaign.id), str(patient.id))
        user = _get_admin_user()
        visit = _advance_to_visit_lab_validated(campaign, patient, user)
        visit = CampaignVisitService.validate_doctor_clinic(
            str(visit.id), user, ValidateDoctorClinicDTO(interpretation="RAS Clinic.")
        )
        CampaignVisitService.validate_doctor_company(
            str(visit.id),
            user,
            ValidateDoctorCompanyDTO(interpretation="Apte.", message="Bons résultats."),
        )

        pdf_bytes = generate_visit_results_pdf(str(visit.id))

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_visit_results_pdf_missing_id_raises(self):
        """generate_visit_results_pdf raises for an unknown visit ID."""
        with self.assertRaises(Exception):
            generate_visit_results_pdf("00000000-0000-0000-0000-000000000000")
