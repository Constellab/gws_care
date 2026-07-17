"""DB migration v0.68.14 — Remove test campaign "PRG-TUH1Q8KK" and test
private consultation "VIS-FD0E9GKK".

One-off cleanup of two unrelated test records:
  - Campaign PRG-TUH1Q8KK, with its cascade-linked visits, exam configs,
    doctor assignments, and campaign-linked Exam records (matched by the
    "CAMP:{campaign_id}|" reason_for_visit marker, rather than a hardcoded
    exam ID list). Same explicit-delete-order pattern as
    migration_65.py/67.py/68.py/69.py/71.py/72.py/73.py/74.py/76.py/77.py.
  - Private consultation Visit VIS-FD0E9GKK (campaign_id is null for these),
    with its linked Exam/Prescription/MedicalCertificate records explicitly
    deleted rather than left as orphaned SET NULL rows.

Looked up by campaign_number / visit_number rather than a hardcoded id,
since the ids weren't available when this migration was written — a no-op
on any install where these don't exist.
"""

from gws_care.core.care_db_manager import CareDbManager
from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

_CAMPAIGN_NUMBERS = [
    "PRG-TUH1Q8KK",
]

_VISIT_NUMBERS = [
    "VIS-FD0E9GKK",
]


@brick_migration(
    "0.68.14",
    short_description="Remove test campaign PRG-TUH1Q8KK and test consultation VIS-FD0E9GKK",
    db_manager=CareDbManager.get_instance(),
    authenticate_sys_user=False,
)
class Migration780(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        cls._remove_campaign()
        cls._remove_private_consultation()

    @classmethod
    def _remove_campaign(cls) -> None:
        from gws_care.campaign.campaign import Campaign
        from gws_care.campaign.campaign_doctor import CampaignDoctor
        from gws_care.campaign.campaign_exam import CampaignExam
        from gws_care.campaign.campaign_exam_doctor import CampaignExamDoctor
        from gws_care.campaign.campaign_patient import CampaignPatient
        from gws_care.exam.exam import Exam
        from gws_care.visit.visit import Visit
        from gws_care.workflow.campaign_validation_workflow import CampaignValidationWorkflow
        from gws_care.workflow.campaign_visit_validation_workflow import CampaignVisitValidationWorkflow

        campaigns = list(Campaign.select().where(Campaign.campaign_number.in_(_CAMPAIGN_NUMBERS)))
        if not campaigns:
            return
        campaign_ids = [c.id for c in campaigns]

        # Exams created against this campaign are linked via a text marker
        # ("CAMP:{campaign_id}|...") in reason_for_visit, not a real FK — so
        # they must be matched this way rather than by a fixed id list.
        for campaign_id in campaign_ids:
            Exam.delete().where(Exam.reason_for_visit % f"CAMP:{campaign_id}|%").execute()

        exam_ids = [
            e.id for e in CampaignExam.select(CampaignExam.id).where(CampaignExam.campaign.in_(campaign_ids))
        ]
        if exam_ids:
            CampaignExamDoctor.delete().where(CampaignExamDoctor.campaign_exam.in_(exam_ids)).execute()
        CampaignExam.delete().where(CampaignExam.campaign.in_(campaign_ids)).execute()
        CampaignDoctor.delete().where(CampaignDoctor.campaign.in_(campaign_ids)).execute()
        CampaignValidationWorkflow.delete().where(CampaignValidationWorkflow.campaign.in_(campaign_ids)).execute()

        visit_ids = [v.id for v in Visit.select(Visit.id).where(Visit.campaign.in_(campaign_ids))]
        if visit_ids:
            CampaignVisitValidationWorkflow.delete().where(
                CampaignVisitValidationWorkflow.visit.in_(visit_ids)
            ).execute()
        Visit.delete().where(Visit.campaign.in_(campaign_ids)).execute()

        CampaignPatient.delete().where(CampaignPatient.campaign.in_(campaign_ids)).execute()

        Campaign.delete().where(Campaign.id.in_(campaign_ids)).execute()

    @classmethod
    def _remove_private_consultation(cls) -> None:
        from gws_care.certificate.medical_certificate import MedicalCertificate
        from gws_care.exam.exam import Exam
        from gws_care.prescription.prescription import Prescription
        from gws_care.visit.visit import Visit

        visits = list(Visit.select().where(Visit.visit_number.in_(_VISIT_NUMBERS)))
        if not visits:
            return
        visit_ids = [v.id for v in visits]

        Exam.delete().where(Exam.visit.in_(visit_ids)).execute()
        Prescription.delete().where(Prescription.visit.in_(visit_ids)).execute()
        MedicalCertificate.delete().where(MedicalCertificate.visit.in_(visit_ids)).execute()

        Visit.delete().where(Visit.id.in_(visit_ids)).execute()
