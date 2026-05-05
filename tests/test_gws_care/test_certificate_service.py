"""Unit tests for MedicalCertificateService."""

from datetime import date, timedelta

from gws_care.certificate.medical_certificate import (
    MedicalCertificateService,
    SaveMedicalCertificateDTO,
)
from gws_care.exam.exam_dto import SaveExamDTO
from gws_care.exam.exam_service import ExamService
from gws_care.exam.exam_type import ExamType
from gws_care.patient.patient_dto import SavePatientDTO
from gws_care.patient.patient_service import PatientService
from gws_care.user.care_user_sync_service import CareUserSyncService
from gws_care.user.user import User
from gws_core import BaseTestCase

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_patient():
    return PatientService.create_patient(
        SavePatientDTO(last_name="Cert", first_name="Patient", date_of_birth=date(1980, 5, 10), gender="M")
    )


def _make_exam(patient_id: str):
    return ExamService.create_exam(
        SaveExamDTO(patient_id=patient_id, exam_date=date.today(), exam_type=ExamType.CLINICAL)
    )


def _get_doctor() -> User:
    return User.select().where(User.is_active == True).get()


def _make_cert_dto(patient_id: str, **kwargs) -> SaveMedicalCertificateDTO:
    defaults = {
        "patient_id": patient_id,
        "issue_date": date.today(),
        "conclusion": "Fit for work",
        "is_fit_for_work": True,
    }
    defaults.update(kwargs)
    return SaveMedicalCertificateDTO(**defaults)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestMedicalCertificateService(BaseTestCase):
    """Tests for MedicalCertificateService: create and list."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        CareUserSyncService().sync_all_users()

    # ── create_certificate ────────────────────────────────────────────────────

    def test_create_certificate_happy_path(self):
        """Certificate is created with all fields persisted."""
        patient = _make_patient()
        doctor = _get_doctor()

        cert = MedicalCertificateService.create_certificate(
            _make_cert_dto(
                str(patient.id),
                conclusion="Fit for all activities",
                is_fit_for_work=True,
                restrictions="None",
            ),
            issued_by=doctor,
        )

        self.assertIsNotNone(cert.id)
        self.assertEqual(str(cert.patient_id), str(patient.id))
        self.assertEqual(cert.conclusion, "Fit for all activities")
        self.assertTrue(cert.is_fit_for_work)
        self.assertEqual(cert.restrictions, "None")
        self.assertEqual(str(cert.issued_by_id), str(doctor.id))

    def test_create_certificate_not_fit_for_work(self):
        """is_fit_for_work=False is persisted correctly."""
        patient = _make_patient()
        doctor = _get_doctor()

        cert = MedicalCertificateService.create_certificate(
            _make_cert_dto(
                str(patient.id),
                conclusion="Temporary medical leave",
                is_fit_for_work=False,
                restrictions="No heavy lifting for 4 weeks",
            ),
            issued_by=doctor,
        )

        self.assertFalse(cert.is_fit_for_work)
        self.assertEqual(cert.restrictions, "No heavy lifting for 4 weeks")

    def test_create_certificate_with_linked_exam(self):
        """exam_id is persisted when certificate is linked to an exam session."""
        patient = _make_patient()
        exam = _make_exam(str(patient.id))
        doctor = _get_doctor()

        cert = MedicalCertificateService.create_certificate(
            _make_cert_dto(str(patient.id), exam_id=str(exam.id)),
            issued_by=doctor,
        )

        self.assertEqual(str(cert.exam_id), str(exam.id))

    def test_create_certificate_without_exam(self):
        """exam_id=None is accepted (standalone certificate)."""
        patient = _make_patient()
        doctor = _get_doctor()

        cert = MedicalCertificateService.create_certificate(
            _make_cert_dto(str(patient.id), exam_id=None),
            issued_by=doctor,
        )

        self.assertIsNone(cert.exam_id)

    def test_create_certificate_without_restrictions(self):
        """restrictions=None is accepted."""
        patient = _make_patient()
        doctor = _get_doctor()

        cert = MedicalCertificateService.create_certificate(
            _make_cert_dto(str(patient.id), restrictions=None),
            issued_by=doctor,
        )

        self.assertIsNone(cert.restrictions)

    def test_create_certificate_issue_date_persisted(self):
        """Specific issue_date is stored correctly."""
        patient = _make_patient()
        doctor = _get_doctor()
        target_date = date.today() - timedelta(days=7)

        cert = MedicalCertificateService.create_certificate(
            _make_cert_dto(str(patient.id), issue_date=target_date),
            issued_by=doctor,
        )

        self.assertEqual(cert.issue_date, target_date)

    # ── list_for_patient ──────────────────────────────────────────────────────

    def test_list_for_patient_returns_all_certs(self):
        """list_for_patient returns all certificates for a patient."""
        patient = _make_patient()
        doctor = _get_doctor()
        MedicalCertificateService.create_certificate(_make_cert_dto(str(patient.id)), issued_by=doctor)
        MedicalCertificateService.create_certificate(_make_cert_dto(str(patient.id)), issued_by=doctor)

        results = MedicalCertificateService.list_for_patient(str(patient.id))
        self.assertEqual(len(results), 2)

    def test_list_for_patient_ordered_newest_first(self):
        """Certificates are ordered by issue_date descending."""
        patient = _make_patient()
        doctor = _get_doctor()
        old_date = date.today() - timedelta(days=30)
        new_date = date.today()

        cert_old = MedicalCertificateService.create_certificate(
            _make_cert_dto(str(patient.id), issue_date=old_date), issued_by=doctor
        )
        cert_new = MedicalCertificateService.create_certificate(
            _make_cert_dto(str(patient.id), issue_date=new_date), issued_by=doctor
        )

        results = MedicalCertificateService.list_for_patient(str(patient.id))
        self.assertEqual(str(results[0].id), str(cert_new.id))
        self.assertEqual(str(results[1].id), str(cert_old.id))

    def test_list_for_patient_isolation(self):
        """Certificates of another patient are not included."""
        p1 = _make_patient()
        p2 = _make_patient()
        doctor = _get_doctor()

        MedicalCertificateService.create_certificate(_make_cert_dto(str(p1.id)), issued_by=doctor)
        MedicalCertificateService.create_certificate(_make_cert_dto(str(p2.id)), issued_by=doctor)

        results = MedicalCertificateService.list_for_patient(str(p1.id))
        for cert in results:
            self.assertEqual(str(cert.patient_id), str(p1.id))

    def test_list_for_patient_empty(self):
        """list_for_patient returns empty list when no certificates exist."""
        patient = _make_patient()
        results = MedicalCertificateService.list_for_patient(str(patient.id))
        self.assertEqual(results, [])
