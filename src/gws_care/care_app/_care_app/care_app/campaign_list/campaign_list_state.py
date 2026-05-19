"""Campaigns list page — all campaigns with search/filter."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class CampaignListRowDTO(BaseModel):
    id: str
    name: str
    account_name: str
    status: str
    status_label: str
    status_color: str
    start_date: str
    end_date: str
    location: str
    patient_count: int
    psc_doctor_name: str


class AccountFilterDTO(BaseModel):
    id: str
    name: str


class ExamTypeOption(BaseModel):
    id: str
    name: str
    category_label: str


class CampaignListState(ReflexMainState):
    campaigns: list[CampaignListRowDTO] = []
    is_loading: bool = False
    error: str = ""
    search: str = ""
    filter_status: str = ""
    filter_account_id: str = ""
    account_options: list[AccountFilterDTO] = []

    # ── Confirm archivage campagne ───────────────────────────────────────
    confirm_archive_open: bool = False
    confirm_archive_id: str = ""
    confirm_archive_name: str = ""

    # ── Nouvelle campagne dialog ──────────────────────────────────────────
    show_create_dialog: bool = False
    create_name: str = ""
    create_account_id: str = ""
    create_start_date: str = ""
    create_end_date: str = ""
    create_location: str = ""
    create_notes: str = ""
    create_error: str = ""
    is_creating: bool = False
    exam_type_options: list[ExamTypeOption] = []
    create_selected_exams: list[ExamTypeOption] = []
    create_add_exam_select: str = ""  # valeur du dropdown, remise à vide après chaque ajout

    @rx.event
    async def on_load(self):
        await self._load()

    @rx.event
    def set_search(self, v: str):
        self.search = v

    @rx.event
    def set_filter_status(self, v: str):
        self.filter_status = v

    @rx.event
    def set_filter_account(self, v: str):
        self.filter_account_id = v

    @rx.event
    def go_to_campaign(self, campaign_id: str):
        return rx.redirect(f"/campaign/{campaign_id}")

    # ── Dialog open / close ───────────────────────────────────────────────
    @rx.event
    async def go_to_create(self):
        self.create_name = ""
        self.create_account_id = ""
        self.create_start_date = ""
        self.create_end_date = ""
        self.create_location = ""
        self.create_notes = ""
        self.create_error = ""
        self.create_selected_exams = []
        self.create_add_exam_select = ""
        self.show_create_dialog = True
        # Charger le référentiel d'examens actifs
        try:
            with await self.authenticate_user():
                from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
                refs = (
                    ExamTypeRef.select()
                    .where(ExamTypeRef.is_active == True)
                    .order_by(ExamTypeRef.category, ExamTypeRef.name)
                )
                self.exam_type_options = [
                    ExamTypeOption(
                        id=str(r.id),
                        name=r.name,
                        category_label=r.get_category_label(),
                    )
                    for r in refs
                ]
        except Exception:
            self.exam_type_options = []

    @rx.event
    def close_create_dialog(self):
        self.show_create_dialog = False
        self.create_error = ""

    @rx.event
    def add_exam_to_campaign(self, exam_id: str):
        """Ajoute un type d'examen depuis la liste déroulante (ignore les doublons)."""
        self.create_add_exam_select = ""  # remet le dropdown sur le placeholder
        if not exam_id:
            return
        if any(e.id == exam_id for e in self.create_selected_exams):
            return
        opt = next((o for o in self.exam_type_options if o.id == exam_id), None)
        if opt:
            self.create_selected_exams = self.create_selected_exams + [opt]

    @rx.event
    def remove_exam_from_campaign(self, exam_id: str):
        """Retire un type d'examen de la sélection."""
        self.create_selected_exams = [
            e for e in self.create_selected_exams if e.id != exam_id
        ]

    @rx.event
    def set_create_name(self, v: str): self.create_name = v
    @rx.event
    def set_create_account_id(self, v: str): self.create_account_id = v
    @rx.event
    def set_create_start_date(self, v: str): self.create_start_date = v
    @rx.event
    def set_create_end_date(self, v: str): self.create_end_date = v
    @rx.event
    def set_create_location(self, v: str): self.create_location = v
    @rx.event
    def set_create_notes(self, v: str): self.create_notes = v

    @rx.event
    async def submit_create(self):
        self.create_error = ""
        if not self.create_name.strip():
            self.create_error = "Le nom est obligatoire."
            return
        if not self.create_account_id:
            self.create_error = "Le compte de facturation est obligatoire."
            return
        self.is_creating = True
        try:
            with await self.authenticate_user():
                from datetime import date as date_type
                from gws_care.campaign.campaign_service import CampaignService

                def _parse_date(s: str) -> date_type | None:
                    try:
                        return date_type.fromisoformat(s) if s else None
                    except ValueError:
                        return None

                campaign = CampaignService.create_campaign(
                    account_id=self.create_account_id,
                    name=self.create_name.strip(),
                    start_date=_parse_date(self.create_start_date),
                    end_date=_parse_date(self.create_end_date),
                    location=self.create_location.strip() or None,
                    notes=self.create_notes.strip() or None,
                )
                # Lier les types d'examens sélectionnés depuis le référentiel
                if self.create_selected_exams:
                    from gws_care.campaign.campaign_exam import CampaignExam
                    from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
                    for exam in self.create_selected_exams:
                        try:
                            exam_ref = ExamTypeRef.get_by_id_and_check(exam.id)
                            ce = CampaignExam()
                            ce.campaign = campaign
                            ce.exam_type_ref = exam_ref
                            ce.save()
                        except Exception:
                            pass
                self.show_create_dialog = False
                return rx.redirect(f"/campaign/{campaign.id}")
        except Exception as e:
            self.create_error = str(e)
        finally:
            self.is_creating = False

    # ── Confirm archivage ────────────────────────────────────────────────
    @rx.event
    def open_confirm_archive(self, campaign_id: str, campaign_name: str):
        self.confirm_archive_id = campaign_id
        self.confirm_archive_name = campaign_name
        self.confirm_archive_open = True

    @rx.event
    def dismiss_confirm_archive(self):
        self.confirm_archive_open = False
        self.confirm_archive_id = ""
        self.confirm_archive_name = ""

    @rx.event
    async def confirmed_archive(self):
        campaign_id = self.confirm_archive_id
        self.confirm_archive_open = False
        self.confirm_archive_id = ""
        self.confirm_archive_name = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.archive(campaign_id)
            await self._load()
        except Exception as e:
            self.error = str(e)

    async def _load(self):
        if not await self.check_authentication():
            return
        self.is_loading = True
        try:
            with await self.authenticate_user():
                from gws_care.account.account import Account
                from gws_care.campaign.campaign_patient import CampaignPatient
                from gws_care.campaign.campaign_service import CampaignService
                from gws_care.campaign.campaign_status import CampaignStatus
                campaigns = CampaignService.list_all_campaigns(
                    status=self.filter_status if self.filter_status not in ("", "ALL") else None
                )
                rows = []
                for c in campaigns:
                    if self.filter_account_id and self.filter_account_id != "ALL" and str(c.account_id) != self.filter_account_id:
                        continue
                    if self.search and self.search.lower() not in c.name.lower():
                        continue
                    try:
                        status_e = CampaignStatus(c.status)
                    except ValueError:
                        status_e = CampaignStatus.DRAFT
                    count = CampaignService.patient_count(str(c.id))
                    psc_name = ""
                    if c.psc_doctor_id:
                        try:
                            psc_name = f"{c.psc_doctor.first_name} {c.psc_doctor.last_name}"
                        except Exception:
                            pass
                    rows.append(CampaignListRowDTO(
                        id=str(c.id),
                        name=c.name,
                        account_name=c.account.name if c.account_id else "",
                        status=c.status,
                        status_label=status_e.get_label(),
                        status_color=status_e.get_color(),
                        start_date=c.start_date.isoformat() if c.start_date else "",
                        end_date=c.end_date.isoformat() if c.end_date else "",
                        location=c.location or "",
                        patient_count=count,
                        psc_doctor_name=psc_name,
                    ))
                self.campaigns = rows
                # load account options
                accounts = Account.select().where(Account.is_active == True).order_by(Account.name)
                self.account_options = [
                    AccountFilterDTO(id=str(a.id), name=a.name) for a in accounts
                ]
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_loading = False
