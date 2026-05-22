"""State for the consultation list page (/consultations)."""

from datetime import date

import reflex as rx
from pydantic import BaseModel

from ..common.account_picker_state import AccountPickerRowDTO
from ..common.combined_picker_state import CombinedPickerState
from ..common.patient_picker_state import PatientPickerRowDTO


class ConsultationRowDTO(BaseModel):
    id: str
    visit_number: str
    patient_name: str
    patient_id: str
    account_name: str | None = None
    scheduled_at: str = ""
    status: str
    status_label: str = ""
    exam_count: int = 0


class AccountOptionDTO(BaseModel):
    id: str
    name: str


class PatientAccountOption(BaseModel):
    id: str
    name: str


class ConsultationListState(CombinedPickerState):
    """State for the /consultations page."""

    # ── Patient picker vars ────────────────────────────────────────────────
    picker_patients: list[PatientPickerRowDTO] = []
    picker_is_loading: bool = False
    picker_error: str = ""
    picker_filter_name: str = ""
    picker_filter_number: str = ""
    picker_account_id: str = ""
    picker_is_open: bool = False
    picker_selected_id: str = ""
    picker_selected_label: str = ""

    # ── Account picker vars ────────────────────────────────────────────────
    acct_picker_is_open: bool = False
    acct_picker_filter: str = ""
    acct_picker_accounts: list[AccountPickerRowDTO] = []
    acct_picker_is_loading: bool = False
    acct_picker_error: str = ""
    acct_picker_selected_id: str = ""
    acct_picker_selected_name: str = ""

    # ── Patient picker events ──────────────────────────────────────────────

    @rx.event
    async def open_patient_picker(self):
        await self._open_patient_picker()

    @rx.event
    def close_patient_picker(self):
        self.picker_is_open = False

    @rx.event
    async def picker_set_filter_name(self, value: str):
        await self._picker_set_filter_name(value)

    @rx.event
    async def picker_set_filter_number(self, value: str):
        await self._picker_set_filter_number(value)

    @rx.event
    async def picker_clear_filters(self):
        await self._picker_clear_filters()

    @rx.event
    def picker_select_patient(self, patient_id: str, label: str):
        self.picker_selected_id = patient_id
        self.picker_selected_label = label
        self.picker_is_open = False

    # ── Account picker events ──────────────────────────────────────────────

    @rx.event
    async def open_account_picker(self):
        await self._open_account_picker()

    @rx.event
    def close_account_picker(self):
        self.acct_picker_is_open = False

    @rx.event
    async def acct_picker_set_filter(self, value: str):
        await self._acct_picker_set_filter(value)

    @rx.event
    async def acct_picker_confirm(self, account_id: str, name: str):
        await self._acct_picker_confirm(account_id, name)

    @rx.event
    async def acct_picker_clear(self):
        await self._acct_picker_clear()

    # ── Page state ─────────────────────────────────────────────────────────

    consultations: list[ConsultationRowDTO] = []
    accounts: list[AccountOptionDTO] = []
    is_loading: bool = False
    error_message: str = ""
    search: str = ""
    filter_status: str = "ALL"
    filter_account_id: str = ""
    filter_date_from: str = ""
    filter_date_to: str = ""

    # ── New consultation dialog ────────────────────────────────────────────
    show_new_dialog: bool = False
    new_scheduled_at: str = ""
    new_error: str = ""
    new_is_saving: bool = False
    new_patient_accounts: list[PatientAccountOption] = []
    new_account_id: str = ""
    new_account_name: str = ""

    @rx.event
    async def on_load(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_operator, self.is_doctor)
        if redirect:
            return redirect
        await self._load_accounts()
        await self._load_consultations()

    async def _on_account_picked(self, account_id: str) -> None:
        self.filter_account_id = account_id
        await self._load_consultations()

    @rx.event
    async def set_search(self, value: str):
        self.search = value
        await self._load_consultations()

    @rx.event
    async def set_filter_status(self, value: str):
        self.filter_status = value
        await self._load_consultations()

    @rx.event
    async def set_filter_date_from(self, value: str):
        self.filter_date_from = value
        await self._load_consultations()

    @rx.event
    async def set_filter_date_to(self, value: str):
        self.filter_date_to = value
        await self._load_consultations()

    @rx.event
    async def clear_filters(self):
        self.search = ""
        self.filter_status = "ALL"
        self.filter_account_id = ""
        self.filter_date_from = ""
        self.filter_date_to = ""
        await self._load_consultations()

    @rx.event
    def go_to_consultation(self, visit_id: str):
        return rx.redirect(f"/consultation/{visit_id}")

    @rx.event
    def go_to_patient(self, patient_id: str):
        return rx.redirect(f"/patient/{patient_id}")

    # ── New consultation dialog events ────────────────────────────────────

    @rx.event
    async def open_new_dialog(self):
        await self._open_picker(account_id="")
        self.new_scheduled_at = date.today().isoformat()
        self.new_error = ""
        self.new_is_saving = False
        self.new_patient_accounts = []
        self.new_account_id = ""
        self.new_account_name = ""
        self.show_new_dialog = True

    @rx.event
    def close_new_dialog(self):
        self.show_new_dialog = False

    @rx.event
    def set_new_scheduled_at(self, value: str):
        self.new_scheduled_at = value

    @rx.event
    def set_new_account_id(self, value: str):
        self.new_account_id = value
        matched = next((a for a in self.new_patient_accounts if a.id == value), None)
        self.new_account_name = matched.name if matched else ""

    @rx.event
    async def picker_select_patient(self, patient_id: str, label: str):
        """Override to also load the patient's accounts after selection."""
        self.picker_selected_id = patient_id
        self.picker_selected_label = label
        self.picker_is_open = False
        self.new_patient_accounts = []
        self.new_account_id = ""
        self.new_account_name = ""
        if not patient_id:
            return
        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_account import PatientAccount
                links = list(
                    PatientAccount.select().where(PatientAccount.patient == patient_id)
                )
                options = [
                    PatientAccountOption(id=str(link.account_id), name=link.account.name)
                    for link in links
                ]
                self.new_patient_accounts = options
                if len(options) == 1:
                    self.new_account_id = options[0].id
                    self.new_account_name = options[0].name
        except Exception as e:
            self.new_error = str(e)

    @rx.event
    async def save_new_consultation(self):
        if not self.picker_selected_id:
            self.new_error = "Veuillez sélectionner un patient."
            return
        if not self.new_scheduled_at:
            self.new_error = "Veuillez indiquer une date."
            return
        self.new_error = ""
        self.new_is_saving = True
        try:
            with await self.authenticate_user():
                from gws_care.visit.consultation_service import ConsultationService

                visit = ConsultationService.create_consultation(
                    patient_id=self.picker_selected_id,
                    scheduled_at_str=self.new_scheduled_at or None,
                    billing_account_id=self.new_account_id or None,
                )
                visit_id = str(visit.id)

            self.show_new_dialog = False
            return rx.redirect(f"/consultation/{visit_id}")
        except Exception as e:
            self.new_error = str(e)
        finally:
            self.new_is_saving = False

    # ── Internal ──────────────────────────────────────────────────────────

    async def _load_accounts(self):
        try:
            with await self.authenticate_user():
                from gws_care.account.account_service import AccountService
                accts = AccountService.list_accounts()
                self.accounts = [AccountOptionDTO(id=str(a.id), name=a.name) for a in accts]
        except Exception:
            self.accounts = []

    async def _load_consultations(self):
        if not await self.check_authentication():
            return
        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.visit.consultation_service import ConsultationService
                from gws_care.visit.consultation_visit_status import ConsultationVisitStatus
                from gws_care.visit.visit_type import VisitType

                status_filter = (
                    ConsultationVisitStatus(self.filter_status)
                    if self.filter_status and self.filter_status != "ALL"
                    else None
                )
                visits = ConsultationService.list_all(
                    status=status_filter,
                    search=self.search,
                    account_id=self.filter_account_id or None,
                    date_from=self.filter_date_from or None,
                    date_to=self.filter_date_to or None,
                )
                rows = []
                for v in visits:
                    exam_count = 0
                    try:
                        from gws_care.exam.exam import Exam
                        exam_count = Exam.select().where(Exam.visit == v.id).count()
                    except Exception:
                        pass
                    cvs = v.consultation_visit_status
                    rows.append(ConsultationRowDTO(
                        id=str(v.id),
                        visit_number=v.visit_number or "",
                        patient_name=v.patient.get_full_name() if v.patient_id else "",
                        patient_id=str(v.patient_id),
                        account_name=v.billing_account.name if v.billing_account_id else None,
                        scheduled_at=v.scheduled_at.isoformat() if v.scheduled_at else "",
                        status=cvs.value if cvs else "",
                        status_label=cvs.get_label() if cvs else "",
                        exam_count=exam_count,
                    ))
                self.consultations = rows
        except Exception as e:
            self.error_message = f"Erreur lors du chargement : {e}"
        finally:
            self.is_loading = False
