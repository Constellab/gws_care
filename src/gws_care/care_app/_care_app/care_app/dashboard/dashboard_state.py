"""Dashboard V2 state — global KPIs for the PSC operations dashboard."""

from pydantic import BaseModel

import reflex as rx
from gws_reflex_main import ReflexMainState

from ..common.nav_role_state import NavRoleState


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
    is_preview_mode: bool = False

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
    async def refresh_role_context(self):
        """Re-evaluate role context — called when preview mode is toggled while on this page."""
        await self._load_role_context()

    @rx.event
    async def set_filter_account(self, value: str):
        self.filter_account_id = value if value != "ALL" else ""
        await self._load_stats()

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _roles_to_context(roles: list[str]) -> str:
        """Map a list of role strings to a dashboard context key."""
        if not roles:
            return "unknown"
        if any(r in roles for r in ("SUPER_ADMIN_PSC", "ADMIN_PSC", "DIRECTEUR_PSC")):
            return "admin"
        if any(r in roles for r in ("OPERATEUR_TERRAIN", "OPERATEUR_LABO")):
            return "operator"
        if "MEDECIN_PSC" in roles:
            return "doctor_psc"
        if "MEDECIN_ENTREPRISE" in roles:
            return "doctor_enterprise"
        if "RH_ENTREPRISE" in roles:
            return "rh"
        return "unknown"

    async def _load_role_context(self):
        """Detect the current user's role context for adaptive display.

        When preview mode is active (admin is previewing another user's view),
        derive the context from the previewed roles instead of the DB.
        """
        try:
            # -- Preview mode: reflect the roles being simulated ----------------
            nav_state = await self.get_state(NavRoleState)
            if nav_state.preview_roles:
                self.user_role_context = self._roles_to_context(list(nav_state.preview_roles))
                self.user_display_name = f"Aperçu : {nav_state.preview_user_name}"
                self.is_preview_mode = True
                return

            # -- Normal mode: read actual roles from DB -------------------------
            self.is_preview_mode = False
            with await self.authenticate_user() as auth_user:
                from gws_care.role.user_role_service import UserRoleService
                from gws_care.user.user import User
                roles = [r.value for r in UserRoleService.get_roles_for_user(str(auth_user.id))]
                self.user_role_context = self._roles_to_context(roles)
                try:
                    u = User.get_by_id(str(auth_user.id))
                    self.user_display_name = f"{u.first_name} {u.last_name}".strip() or u.email
                except Exception as exc:
                    print(f"[dashboard] Erreur chargement nom utilisateur: {exc}")
                    self.user_display_name = auth_user.email or ""
        except Exception as exc:
            print(f"[dashboard] Erreur chargement contexte utilisateur: {exc}")
            self.user_role_context = "unknown"
            self.is_preview_mode = False

    async def _load_accounts(self):
        try:
            with await self.authenticate_user():
                from gws_care.account.account_service import AccountService
                self.accounts = [
                    AccountOption(id=str(a.id), name=a.name)
                    for a in AccountService.list_accounts()
                ]
        except Exception as exc:
            print(f"[dashboard] Erreur chargement comptes: {exc}")
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

                # ── Core counts (3 simple scalar queries) ─────────────────────
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

                self.total_patients = patient_q.count()
                self.total_appointments = appt_q.count()
                self.total_certificates = cert_q.count()

                # ── Campaign counts via one GROUP BY (replaces 4 separate COUNTs) ──
                camp_status_map: dict[str, int] = {}
                for row in (
                    camp_q.select(Campaign.status, fn.COUNT(Campaign.id).alias("cnt"))
                    .group_by(Campaign.status)
                    .namedtuples()
                ):
                    camp_status_map[row.status] = row.cnt
                self.total_campaigns = sum(camp_status_map.values())
                self.dossiers_awaiting_psc = camp_status_map.get(CampaignStatus.LABO_VALIDE.value, 0)
                self.dossiers_available_medecin_entreprise = camp_status_map.get(
                    CampaignStatus.PUBLIE_MEDECIN_ENTREPRISE.value, 0
                )
                self.dossiers_published_patient = camp_status_map.get(CampaignStatus.PUBLIE_PATIENT.value, 0)

                # ── Presence stats via one GROUP BY (replaces 3 separate COUNTs) ─
                cp_q = CampaignPatient.select()
                if cid:
                    cp_q = CampaignPatient.select().join(Campaign).where(Campaign.account == cid)
                cp_presence_map: dict[str, int] = {}
                for row in (
                    cp_q.select(CampaignPatient.presence_status, fn.COUNT(CampaignPatient.id).alias("cnt"))
                    .group_by(CampaignPatient.presence_status)
                    .namedtuples()
                ):
                    cp_presence_map[row.presence_status] = row.cnt
                self.total_convocations_sent = sum(cp_presence_map.values())
                self.total_present = cp_presence_map.get("PRESENT", 0)
                self.total_absent = cp_presence_map.get("ABSENT", 0)
                if self.total_convocations_sent > 0:
                    self.participation_rate = round(
                        self.total_present * 100 / self.total_convocations_sent
                    )
                else:
                    self.participation_rate = 0

                # ── Exam counts via one GROUP BY (replaces 2 separate COUNTs) ────
                exam_status_map: dict[str, int] = {}
                for row in (
                    exam_q.select(Exam.status, fn.COUNT(Exam.id).alias("cnt"))
                    .group_by(Exam.status)
                    .namedtuples()
                ):
                    exam_status_map[row.status] = row.cnt
                self.exams_done = exam_status_map.get("interpreted", 0)
                self.exams_to_enter = exam_status_map.get("draft", 0)
                self.exams_labo_validated = self.exams_done  # alias

                # ── Notification counts via one GROUP BY (replaces 2 COUNTs) ─────
                notif_status_map: dict[str, int] = {}
                for row in (
                    NotificationLog.select(NotificationLog.status, fn.COUNT(NotificationLog.id).alias("cnt"))
                    .group_by(NotificationLog.status)
                    .namedtuples()
                ):
                    notif_status_map[row.status] = row.cnt
                self.notifications_sent = notif_status_map.get(NotificationStatus.SENT.value, 0)
                self.notifications_failed = notif_status_map.get(NotificationStatus.FAILED.value, 0)

                # ── Role-specific pending counts via one GROUP BY (replaces 3 COUNTs) ──
                medical_status_map: dict[str, int] = {}
                for row in (
                    CampaignPatient.select(CampaignPatient.medical_status, fn.COUNT(CampaignPatient.id).alias("cnt"))
                    .group_by(CampaignPatient.medical_status)
                    .namedtuples()
                ):
                    medical_status_map[row.medical_status] = row.cnt
                self.my_pending_interpretations = medical_status_map.get("LAB_VALIDATED", 0)
                self.my_pending_validation = medical_status_map.get("PSC_INTERPRETED", 0)
                self.my_enterprise_pending = medical_status_map.get("PSC_VALIDATED", 0)

                # ── Campaigns by status (chart) ───────────────────────────────
                self.campaigns_by_status = [
                    CampaignStatusStat(
                        status=status,
                        label=CampaignStatus(status).get_label(),
                        color=CampaignStatus(status).get_color(),
                        count=count,
                    )
                    for status, count in camp_status_map.items()
                    if status in {s.value for s in CampaignStatus}
                ]

                # ── Recent campaigns — pre-aggregate patient counts (fix N+1) ──
                recent_list = list(camp_q.order_by(Campaign.last_modified_at.desc()).limit(20))
                recent_ids = [c.id for c in recent_list]
                cp_counts_map: dict[str, int] = {}
                if recent_ids:
                    for row in (
                        CampaignPatient.select(
                            CampaignPatient.campaign_id,
                            fn.COUNT(CampaignPatient.id).alias("cnt"),
                        )
                        .where(CampaignPatient.campaign.in_(recent_ids))
                        .group_by(CampaignPatient.campaign_id)
                        .namedtuples()
                    ):
                        cp_counts_map[str(row.campaign_id)] = row.cnt
                # Pre-load account names (avoids N+1)
                from gws_care.account.account import Account
                recent_account_ids = [c.account_id for c in recent_list if c.account_id]
                recent_account_names: dict[str, str] = {}
                if recent_account_ids:
                    for ac in Account.select(Account.id, Account.name).where(Account.id.in_(recent_account_ids)):
                        recent_account_names[str(ac.id)] = ac.name

                rows = []
                for c in recent_list:
                    status_enum = CampaignStatus(c.status)
                    rows.append(
                        RecentCampaignRow(
                            id=str(c.id),
                            name=c.name,
                            account_name=recent_account_names.get(str(c.account_id), "") if c.account_id else "",
                            status=c.status,
                            status_label=status_enum.get_label(),
                            status_color=status_enum.get_color(),
                            patient_count=cp_counts_map.get(str(c.id), 0),
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

