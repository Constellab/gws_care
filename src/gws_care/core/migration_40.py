"""Migration 0.49.0 — delete the last leftover test visit (VIS-3BV0OOE4).

Migration 0.48.0 skipped this visit because it had at least one exam,
prescription or certificate attached from manual testing. The user confirmed
this specific visit is still test debris, so this migration removes it along
with any attached exams/prescriptions/certificates.
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager

_VISIT_NUMBER = "VIS-3BV0OOE4"


@brick_migration(
    "0.49.0",
    short_description="Delete leftover test visit VIS-3BV0OOE4 and its children",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration400(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        from gws_care.certificate.medical_certificate import MedicalCertificate
        from gws_care.exam.exam import Exam
        from gws_care.exam.exam_audit_entry import ExamAuditEntry
        from gws_care.exam.exam_parameter_result import ExamParameterResult
        from gws_care.prescription.prescription import Prescription
        from gws_care.visit.visit import Visit

        visit = Visit.get_or_none(Visit.visit_number == _VISIT_NUMBER)
        if visit is None:
            return

        exam_ids = [e.id for e in Exam.select(Exam.id).where(Exam.visit == visit.id)]
        if exam_ids:
            ExamParameterResult.delete().where(ExamParameterResult.exam.in_(exam_ids)).execute()
            ExamAuditEntry.delete().where(ExamAuditEntry.exam.in_(exam_ids)).execute()
            Exam.delete().where(Exam.id.in_(exam_ids)).execute()
        Prescription.delete().where(Prescription.visit == visit.id).execute()
        MedicalCertificate.delete().where(MedicalCertificate.visit == visit.id).execute()
        visit.delete_instance()
