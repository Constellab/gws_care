"""Migration 0.52.0 — wipe all test data for patient "Asma Benneji".

Removes every visit, exam (and its results/audit log), prescription,
certificate and doctor link for this patient, while keeping the Patient
record itself — resets her to a fresh, history-less state after testing.
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager

_PATIENT_FIRST_NAME = "Asma"
_PATIENT_LAST_NAME = "Benneji"


@brick_migration(
    "0.52.0",
    short_description="Wipe all visits/exams/prescriptions/certificates/doctor links for patient Asma Benneji",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration430(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        from gws_care.certificate.medical_certificate import MedicalCertificate
        from gws_care.exam.exam import Exam
        from gws_care.exam.exam_audit_entry import ExamAuditEntry
        from gws_care.exam.exam_file import ExamFile
        from gws_care.exam.exam_parameter_result import ExamParameterResult
        from gws_care.patient.patient import Patient
        from gws_care.patient.patient_doctor import PatientDoctor
        from gws_care.prescription.prescription import Prescription
        from gws_care.visit.visit import Visit

        patient = Patient.get_or_none(
            (Patient.first_name == _PATIENT_FIRST_NAME)
            & (Patient.last_name == _PATIENT_LAST_NAME)
        )
        if patient is None:
            return

        exam_ids = [e.id for e in Exam.select(Exam.id).where(Exam.patient == patient.id)]
        if exam_ids:
            ExamParameterResult.delete().where(ExamParameterResult.exam.in_(exam_ids)).execute()
            ExamAuditEntry.delete().where(ExamAuditEntry.exam.in_(exam_ids)).execute()
            ExamFile.delete().where(ExamFile.exam.in_(exam_ids)).execute()
            MedicalCertificate.delete().where(MedicalCertificate.exam.in_(exam_ids)).execute()
            Exam.delete().where(Exam.id.in_(exam_ids)).execute()

        Prescription.delete().where(Prescription.patient == patient.id).execute()
        MedicalCertificate.delete().where(MedicalCertificate.patient == patient.id).execute()
        PatientDoctor.delete().where(PatientDoctor.patient == patient.id).execute()
        Visit.delete().where(Visit.patient == patient.id).execute()
