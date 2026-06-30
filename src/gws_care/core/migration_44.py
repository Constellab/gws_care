"""Migration 0.53.0 — wipe all test data for patient "Asma Benneji" (again).

Same cleanup as migration 0.52.0, re-run because more test data (visits,
exams, doctor links) was created since. Also removes any individual
campaign auto-created just for her booking (is_individual=True), without
touching shared/organizational campaigns that include other patients.
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager

_PATIENT_FIRST_NAME = "Asma"
_PATIENT_LAST_NAME = "Benneji"


@brick_migration(
    "0.53.0",
    short_description="Wipe all visits/exams/prescriptions/certificates/doctor links/individual campaigns for patient Asma Benneji",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration440(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        from gws_care.campaign.campaign import Campaign
        from gws_care.campaign.campaign_patient import CampaignPatient
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

        campaign_ids = {
            str(v.campaign_id) for v in
            Visit.select(Visit.campaign).where(
                (Visit.patient == patient.id) & (Visit.campaign.is_null(False))
            ).distinct()
        }
        Visit.delete().where(Visit.patient == patient.id).execute()
        CampaignPatient.delete().where(CampaignPatient.patient == patient.id).execute()

        if campaign_ids:
            individual_campaign_ids = [
                c.id for c in Campaign.select(Campaign.id).where(
                    (Campaign.id.in_(campaign_ids)) & (Campaign.is_individual == True)
                )
            ]
            if individual_campaign_ids:
                Campaign.delete().where(Campaign.id.in_(individual_campaign_ids)).execute()
