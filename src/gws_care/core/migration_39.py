"""Migration 0.48.0 — one-off cleanup of empty test visits.

Removes the placeholder consultation visits created during development while
testing the (now-removed) "+ Nouvel examen" quick-create button on the
patient detail page. Each targeted visit is re-verified to have zero exams,
prescriptions and certificates before being deleted, so a real visit can
never be wiped even if the visit_number list below is wrong.
"""

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager

# Visit numbers identified as empty test artifacts (see patient detail screenshot)
_EMPTY_TEST_VISIT_NUMBERS = [
    "VIS-3BV0OOE4",
    "VIS-YA1OQW2M",
    "VIS-JCH6YJSL",
    "VIS-0RTNDXVV",
]


@brick_migration(
    "0.48.0",
    short_description="Delete empty test visits created by the removed quick-create exam button",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration390(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        from gws_care.certificate.medical_certificate import MedicalCertificate
        from gws_care.exam.exam import Exam
        from gws_care.prescription.prescription import Prescription
        from gws_care.visit.visit import Visit

        for visit_number in _EMPTY_TEST_VISIT_NUMBERS:
            visit = Visit.get_or_none(Visit.visit_number == visit_number)
            if visit is None:
                continue
            has_exams = Exam.select().where(Exam.visit == visit.id).exists()
            has_prescriptions = Prescription.select().where(Prescription.visit == visit.id).exists()
            has_certificates = MedicalCertificate.select().where(
                MedicalCertificate.visit == visit.id
            ).exists()
            if has_exams or has_prescriptions or has_certificates:
                # Not actually empty — leave it alone
                continue
            visit.delete_instance()
