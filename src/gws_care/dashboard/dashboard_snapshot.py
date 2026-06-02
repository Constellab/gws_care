"""DashboardSnapshot — pre-aggregated KPI cache for the dashboard.

Updated periodically (every N minutes) by a background task, so the
dashboard never scans full tables at request time.

The snapshot covers global PSC stats. Per-role derived views are computed
from the same snapshot without additional DB queries.
"""

from __future__ import annotations

from datetime import datetime

from peewee import DateTimeField, IntegerField

from gws_care.core.care_db_manager import CareDbManager
from gws_core import Model


class DashboardSnapshot(Model):
    """One row = one snapshot of the entire dashboard state.

    Only the most-recent row is used. Older rows are kept for trending.
    The service keeps at most 2 000 rows before pruning.
    """

    computed_at: datetime = DateTimeField(null=False, default=datetime.now, index=True)

    # Campaign KPIs
    total_campaigns: int = IntegerField(default=0)
    active_campaigns: int = IntegerField(default=0)

    # Patient / participation KPIs
    total_patients: int = IntegerField(default=0)
    total_convocations_sent: int = IntegerField(default=0)
    total_present: int = IntegerField(default=0)
    total_absent: int = IntegerField(default=0)
    participation_rate: int = IntegerField(default=0)  # 0-100

    # Exam pipeline KPIs
    exams_done: int = IntegerField(default=0)
    exams_to_enter: int = IntegerField(default=0)       # DRAFT exams
    exams_labo_validated: int = IntegerField(default=0)

    # Medical workflow
    dossiers_awaiting_psc: int = IntegerField(default=0)
    dossiers_available_medecin_entreprise: int = IntegerField(default=0)
    dossiers_published_patient: int = IntegerField(default=0)

    # Notifications
    notifications_sent: int = IntegerField(default=0)
    notifications_failed: int = IntegerField(default=0)

    # Certificates
    total_certificates: int = IntegerField(default=0)

    class Meta:
        table_name = "gws_care_dashboard_snapshot"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()


class DashboardSnapshotService:
    """Compute and retrieve dashboard snapshots."""

    _MAX_ROWS = 2000

    @classmethod
    def get_latest(cls) -> DashboardSnapshot | None:
        return (
            DashboardSnapshot.select()
            .order_by(DashboardSnapshot.computed_at.desc())
            .first()
        )

    @classmethod
    def compute_and_save(cls) -> DashboardSnapshot:
        """Run all aggregate queries and persist a new snapshot row.

        This method is intended to be called from a background task,
        NOT from a user-facing request handler.
        """
        from peewee import fn
        from gws_care.campaign.campaign import Campaign
        from gws_care.campaign.campaign_patient import CampaignPatient, MedicalRecordStatus, PresenceStatus
        from gws_care.campaign.campaign_status import CampaignStatus
        from gws_care.exam.exam import Exam
        from gws_care.exam.exam_type import ExamStatus
        from gws_care.notification.notification_models import NotificationLog
        from gws_care.certificate.medical_certificate import MedicalCertificate
        from gws_care.patient.patient import Patient

        total_campaigns = Campaign.select().count()
        active_campaigns = Campaign.select().where(
            Campaign.status.not_in([CampaignStatus.ARCHIVED.value, CampaignStatus.CANCELLED.value])
        ).count() if hasattr(Campaign, 'status') else 0

        total_patients = Patient.select().count()
        total_convocations = CampaignPatient.select().count()
        total_present = CampaignPatient.select().where(
            CampaignPatient.presence_status == PresenceStatus.PRESENT.value
        ).count()
        total_absent = CampaignPatient.select().where(
            CampaignPatient.presence_status == PresenceStatus.ABSENT.value
        ).count()
        participation_rate = (
            round(100 * total_present / total_convocations)
            if total_convocations > 0
            else 0
        )

        exams_done = Exam.select().where(
            Exam.status.not_in([ExamStatus.DRAFT.value])
        ).count()
        exams_to_enter = Exam.select().where(
            Exam.status == ExamStatus.DRAFT.value
        ).count()
        exams_labo_validated = Exam.select().where(
            Exam.status == ExamStatus.LAB_VALIDATED.value
        ).count()

        dossiers_psc = CampaignPatient.select().where(
            CampaignPatient.medical_status == MedicalRecordStatus.LAB_VALIDATED.value
        ).count()
        dossiers_ent = CampaignPatient.select().where(
            CampaignPatient.medical_status == MedicalRecordStatus.PSC_VALIDATED.value
        ).count()
        dossiers_published = CampaignPatient.select().where(
            CampaignPatient.medical_status == MedicalRecordStatus.PUBLISHED.value
        ).count() if hasattr(MedicalRecordStatus, 'PUBLISHED') else 0

        try:
            notif_sent = NotificationLog.select().where(
                NotificationLog.status == "SENT"
            ).count()
            notif_failed = NotificationLog.select().where(
                NotificationLog.status == "FAILED"
            ).count()
        except Exception as exc:
            print(f"[dashboard_snapshot] notification counts: {exc}")
            notif_sent = notif_failed = 0

        try:
            total_certs = MedicalCertificate.select().count()
        except Exception as exc:
            print(f"[dashboard_snapshot] certificate count: {exc}")
            total_certs = 0

        snapshot = DashboardSnapshot.create(
            computed_at=datetime.now(),
            total_campaigns=total_campaigns,
            active_campaigns=active_campaigns,
            total_patients=total_patients,
            total_convocations_sent=total_convocations,
            total_present=total_present,
            total_absent=total_absent,
            participation_rate=participation_rate,
            exams_done=exams_done,
            exams_to_enter=exams_to_enter,
            exams_labo_validated=exams_labo_validated,
            dossiers_awaiting_psc=dossiers_psc,
            dossiers_available_medecin_entreprise=dossiers_ent,
            dossiers_published_patient=dossiers_published,
            notifications_sent=notif_sent,
            notifications_failed=notif_failed,
            total_certificates=total_certs,
        )

        # Prune old snapshots
        cls._prune()
        return snapshot

    @classmethod
    def _prune(cls) -> None:
        """Keep only the most-recent _MAX_ROWS snapshots."""
        total = DashboardSnapshot.select().count()
        if total > cls._MAX_ROWS:
            cutoff_id = (
                DashboardSnapshot.select(DashboardSnapshot.id)
                .order_by(DashboardSnapshot.computed_at.desc())
                .offset(cls._MAX_ROWS)
                .limit(1)
                .scalar()
            )
            if cutoff_id:
                DashboardSnapshot.delete().where(DashboardSnapshot.id <= cutoff_id).execute()
