"""Migration 0.50.0 — delete the last leftover cancelled test visit.

Migration 0.49.0 targeted this visit by visit_number, transcribed from a
screenshot where 'O' (letter) and '0' (digit) are visually ambiguous — the
exact-string match silently found nothing. This time the visit is identified
by its scheduled_at timestamp and cancelled status instead, which are
unambiguous from the screenshot.
"""

from datetime import datetime

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager

_SCHEDULED_AT = datetime(2026, 6, 30, 12, 36)


@brick_migration(
    "0.50.0",
    short_description="Delete leftover cancelled test visit (identified by scheduled_at)",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration410(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        from gws_care.certificate.medical_certificate import MedicalCertificate
        from gws_care.exam.exam import Exam
        from gws_care.exam.exam_audit_entry import ExamAuditEntry
        from gws_care.exam.exam_parameter_result import ExamParameterResult
        from gws_care.prescription.prescription import Prescription
        from gws_care.visit.consultation_visit_status import ConsultationVisitStatus
        from gws_care.visit.visit import Visit
        from gws_care.visit.visit_type import VisitType

        visits = list(
            Visit.select().where(
                (Visit.visit_type == VisitType.CONSULTATION)
                & (Visit.consultation_visit_status == ConsultationVisitStatus.CANCELLED)
                & (Visit.scheduled_at >= _SCHEDULED_AT)
                & (Visit.scheduled_at < _SCHEDULED_AT.replace(second=59))
            )
        )

        for visit in visits:
            exam_ids = [e.id for e in Exam.select(Exam.id).where(Exam.visit == visit.id)]
            if exam_ids:
                ExamParameterResult.delete().where(ExamParameterResult.exam.in_(exam_ids)).execute()
                ExamAuditEntry.delete().where(ExamAuditEntry.exam.in_(exam_ids)).execute()
                Exam.delete().where(Exam.id.in_(exam_ids)).execute()
            Prescription.delete().where(Prescription.visit == visit.id).execute()
            MedicalCertificate.delete().where(MedicalCertificate.visit == visit.id).execute()
            visit.delete_instance()
