"""Dashboard V2 state — global KPIs for the PSC operations dashboard."""

from pydantic import BaseModel

import reflex as rx
from gws_reflex_main import ReflexMainState


# ── DTOs ─────────────────────────────────────────────────────────────────────

class CampaignStatusStat(BaseModel):
    """Count per campaign status."""
    status: str
    label: str
    color: str
    count: int


class AccountOption(BaseModel):
    """Dropdown option for account filter."""
    id: str
    name: str


class RecentCampaignRow(BaseModel):
    """One row in the recent-campaigns table."""
    id: str
    name: str
    account_name: str
    status: str
    status_label: str
    status_color: str
    patient_count: int
    start_date: str
    end_date: str


# ── State ─────────────────────────────────────────────────────────────────────

class DashboardState(ReflexMainState):
    """Reactive state for the V2 PSC global dashboard."""

    # ── Role context (for adaptive display) ──────────────────────────────────
    # "admin" | "operator" | "doctor_psc" | "doctor_enterprise" | "rh" | "unknown"
    user_role_context: str = "unknown"
    user_display_name: str = ""

    # ── KPI counters ─────────────────────────────────────────────────────────
    total_campaigns: int = 0
    total_patients: int = 0
    total_appointments: int = 0
    total_convocations_sent: int = 0
    total_present: int = 0
    total_absent: int = 0
    participation_rate: int = 0      # integer percentage 0-100

    exams_done: int = 0
    exams_to_enter: int = 0
    exams_labo_validated: int = 0

    dossiers_awaiting_psc: int = 0
    dossiers_available_medecin_entreprise: int = 0
    dossiers_published_patient: int = 0

    # Role-specific counters
    my_pending_interpretations: int = 0   # médecin PSC: dossiers LAB_VALIDATED
    my_pending_validation: int = 0        # médecin PSC: dossiers PSC_INTERPRETED
    my_enterprise_pending: int = 0        # médecin entreprise: dossiers PSC_VALIDATED

    notifications_sent: int = 0
    notifications_failed: int = 0

    total_certificates: int = 0

    # ── Charts ────────────────────────────────────────────────────────────────
    campaigns_by_status: list[CampaignStatusStat] = []
    recent_campaigns: list[RecentCampaignRow] = []

    # ── Filters ──────────────────────────────────────────────────────────────
    accounts: list[AccountOption] = []
    filter_account_id: str = ""

    # ── UI state ─────────────────────────────────────────────────────────────
    is_loading: bool = False
    error_message: str = ""
    last_updated: str = ""

    # ── Lifecycle ────────────────────────────────────────────────────────────

    @rx.event
    async def on_load(self):
        await self._load_role_context()
        await self._load_accounts()
        await self._load_stats()

    @rx.event
    async def refresh(self):
        """Manual refresh triggered by the user."""
        await self._load_stats()

    @rx.event
    async def set_filter_account(self, value: str):
        self.filter_account_id = value if value != "ALL" else ""
        await self._load_stats()

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _load_role_context(self):
        """Detect the current user's role context for adaptive display."""
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.role.user_role_service import UserRoleService
                from gws_care.user.user import User
                roles = [r.value for r in UserRoleService.get_roles_for_user(str(auth_user.id))]
                if not roles:
                    self.user_role_context = "unknown"
                elif any(r in roles for r in ("SUPER_ADMIN_PSC", "ADMIN_PSC", "DIRECTEUR_PSC")):
                    self.user_role_context = "admin"
                elif any(r in roles for r in ("OPERATEUR_TERRAIN", "OPERATEUR_LABO")):
                    self.user_role_context = "operator"
                elif "MEDECIN_PSC" in roles:
                    self.user_role_context = "doctor_psc"
                elif "MEDECIN_ENTREPRISE" in roles:
                    self.user_role_context = "doctor_enterprise"
                elif "RH_ENTREPRISE" in roles:
                    self.user_role_context = "rh"
                else:
                    self.user_role_context = "unknown"
                try:
                    u = User.get_by_id(str(auth_user.id))
                    self.user_display_name = f"{u.first_name} {u.last_name}".strip() or u.email
                except Exception:
                    self.user_display_name = auth_user.email or ""
        except Exception:
            self.user_role_context = "unknown"

    async def _load_accounts(self):
        try:
            with await self.authenticate_user():
                from gws_care.account.account_service import AccountService
                self.accounts = [
                    AccountOption(id=str(a.id), name=a.name)
                    for a in AccountService.list_accounts()
                ]
        except Exception:
            self.accounts = []

    async def _load_stats(self):
        if not await self.check_authentication():
            return

        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from peewee import fn

                from gws_care.appointment.appointment import Appointment
                from gws_care.campaign.campaign import Campaign
                from gws_care.campaign.campaign_patient import CampaignPatient
                from gws_care.campaign.campaign_status import CampaignStatus
                from gws_care.certificate.medical_certificate import MedicalCertificate
                from gws_care.exam.exam import Exam
                from gws_care.notification.notification_models import NotificationLog
                from gws_care.notification.notification_enums import NotificationStatus
                from gws_care.patient.patient import Patient

                cid = self.filter_account_id or None

                # ── Core counts ───────────────────────────────────────────────
                camp_q = Campaign.select()
                patient_q = Patient.select()
                appt_q = Appointment.select()
                exam_q = Exam.select()
                cert_q = MedicalCertificate.select()

                if cid:
                    camp_q = camp_q.where(Campaign.account == cid)
                    patient_q = patient_q.where(Patient.billing_account == cid)
                    appt_q = appt_q.where(Appointment.billing_account == cid)
                    exam_q = exam_q.where(Exam.billing_account == cid)

                self.total_campaigns = camp_q.count()
                self.total_patients = patient_q.count()
                self.total_appointments = appt_q.count()
                self.total_certificates = cert_q.count()

                # ── Presence stats from CampaignPatient ───────────────────────
                cp_q = CampaignPatient.select()
                if cid:
                    cp_q = (
                        CampaignPatient.select()
                        .join(Campaign)
                        .where(Campaign.account == cid)
                    )
                self.total_convocations_sent = cp_q.count()
                present_q = cp_q.where(CampaignPatient.presence_status == "PRESENT")
                absent_q = cp_q.where(CampaignPatient.presence_status == "ABSENT")
                self.total_present = present_q.count() if self.total_convocations_sent else 0
                self.total_absent = absent_q.count() if self.total_convocations_sent else 0
                if self.total_convocations_sent > 0:
                    self.participation_rate = round(
                        self.total_present * 100 / self.total_convocations_sent
                    )
                else:
                    self.participation_rate = 0

                # ── Exam status breakdown ─────────────────────────────────────
                self.exams_done = exam_q.where(Exam.status == "interpreted").count()
                self.exams_to_enter = exam_q.where(Exam.status == "draft").count()
                self.exams_labo_validated = self.exams_done  # alias

                # ── Campaign status breakdown (for dossiers awaiting) ─────────
                self.dossiers_awaiting_psc = camp_q.where(
                    Campaign.status == CampaignStatus.LABO_VALIDE
                ).count()
                self.dossiers_available_medecin_entreprise = camp_q.where(
                    Campaign.status == CampaignStatus.PUBLIE_MEDECIN_ENTREPRISE
                ).count()
                self.dossiers_published_patient = camp_q.where(
                    Campaign.status == CampaignStatus.PUBLIE_PATIENT
                ).count()

                # ── Notifications ─────────────────────────────────────────────
                notif_q = NotificationLog.select()
                self.notifications_sent = notif_q.where(
                    NotificationLog.status == NotificationStatus.SENT
                ).count()
                self.notifications_failed = notif_q.where(
                    NotificationLog.status == NotificationStatus.FAILED
                ).count()

                # ── Role-specific pending counts ──────────────────────────────
                cp_all = CampaignPatient.select()
                self.my_pending_interpretations = cp_all.where(
                    CampaignPatient.medical_status == "LAB_VALIDATED"
                ).count()
                self.my_pending_validation = cp_all.where(
                    CampaignPatient.medical_status == "PSC_INTERPRETED"
                ).count()
                self.my_enterprise_pending = cp_all.where(
                    CampaignPatient.medical_status == "PSC_VALIDATED"
                ).count()

                # ── Campaigns by status ───────────────────────────────────────
                status_rows = (
                    camp_q.select(Campaign.status, fn.COUNT(Campaign.id).alias("cnt"))
                    .group_by(Campaign.status)
                )
                self.campaigns_by_status = [
                    CampaignStatusStat(
                        status=row.status,
                        label=CampaignStatus(row.status).get_label(),
                        color=CampaignStatus(row.status).get_color(),
                        count=row.cnt,
                    )
                    for row in status_rows
                ]

                # ── Recent campaigns (last 10) ────────────────────────────────
                recent_q = (
                    camp_q.order_by(Campaign.last_modified_at.desc()).limit(10)
                )
                rows = []
                for c in recent_q:
                    cp_count = CampaignPatient.select().where(CampaignPatient.campaign == c).count()
                    status_enum = CampaignStatus(c.status)
                    rows.append(
                        RecentCampaignRow(
                            id=str(c.id),
                            name=c.name,
                            account_name=c.account.name if c.account_id else "",
                            status=c.status,
                            status_label=status_enum.get_label(),
                            status_color=status_enum.get_color(),
                            patient_count=cp_count,
                            start_date=str(c.start_date) if c.start_date else "-",
                            end_date=str(c.end_date) if c.end_date else "-",
                        )
                    )
                self.recent_campaigns = rows

        except Exception as e:
            self.error_message = f"Erreur lors du chargement du dashboard : {e}"
        else:
            from datetime import datetime
            self.last_updated = datetime.now().strftime("%H:%M:%S")
        finally:
            self.is_loading = False

