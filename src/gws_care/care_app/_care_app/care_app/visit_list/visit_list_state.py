"""State for the visit list / calendar page."""

import reflex as rx
from pydantic import BaseModel

from ..common.account_picker_state import AccountPickerRowDTO
from ..common.combined_picker_state import CombinedPickerState
from ..common.patient_picker_state import PatientPickerRowDTO


class PatientAccountOption(BaseModel):
    """One of the accounts linked to the selected patient."""

    id: str
    name: str


class VisitRowDTO(BaseModel):
    id: str
    patient_name: str
    patient_id: str
    account_name: str | None = None
    campaign_name: str = ""
    scheduled_at: str = ""  # empty for program visits without a scheduled date
    campaign_visit_status: str
    status_label: str = ""
    visit_number: str = ""
    visit_type: str = ""  # "campaign" or "consultation"


class AccountOptionDTO(BaseModel):
    """Lightweight account option for filter dropdown."""

    id: str
    name: str


class CalendarDayDTO(BaseModel):
    """One cell in the monthly calendar grid."""

    date: str = ""          # "YYYY-MM-DD"; empty for padding cells
    day_num: int = 0        # 0 for padding cells
    is_current_month: bool = False
    is_today: bool = False
    visits: list[VisitRowDTO] = []


class VisitListState(CombinedPickerState):
    """State for the /visits page."""

    # ── Patient picker vars (declared here for independent state storage) ─────
    picker_patients: list[PatientPickerRowDTO] = []
    picker_is_loading: bool = False
    picker_error: str = ""
    picker_filter_name: str = ""
    picker_filter_number: str = ""
    picker_account_id: str = ""
    picker_is_open: bool = False
    picker_selected_id: str = ""
    picker_selected_label: str = ""

    # ── Account picker vars (declared here for independent state storage) ─────
    acct_picker_is_open: bool = False
    acct_picker_filter: str = ""
    acct_picker_accounts: list[AccountPickerRowDTO] = []
    acct_picker_is_loading: bool = False
    acct_picker_error: str = ""
    acct_picker_selected_id: str = ""
    acct_picker_selected_name: str = ""

    # ── Patient picker events ─────────────────────────────────────────────────────

    @rx.event
    async def open_patient_picker(self):
        await self._open_patient_picker()

    @rx.event
    def close_patient_picker(self):
        self.picker_is_open = False

    @rx.event
    async def picker_clear_selection(self):
        self.picker_selected_id = ""
        self.picker_selected_label = ""

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

    # ── Account picker events ─────────────────────────────────────────────────────

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

    visits: list[VisitRowDTO] = []
    companies: list[AccountOptionDTO] = []
    is_loading: bool = False
    is_loading_more: bool = False
    has_more: bool = False
    error_message: str = ""
    search: str = ""
    filter_status: str = "ALL"
    filter_visit_type: str = "ALL"  # ALL / campaign / consultation
    filter_account_id: str = ""
    filter_date_from: str = ""
    filter_date_to: str = ""
    sort_column: str = "scheduled_at"
    sort_ascending: bool = True

    _page_offset: int = 0
    _current_page_size: int = 50

    # View mode: "list" or "calendar"
    view_mode: str = "list"
    calendar_year: int = 2026
    calendar_month: int = 1
    calendar_month_label: str = ""
    calendar_days: list[CalendarDayDTO] = []

    # ── New CampaignVisit dialog ──────────────────────────────────────────────────────
    show_new_visit_dialog: bool = False
    new_visit_type: str = ""  # "" = not yet selected, "campaign" or "consultation"
    new_visit_type_locked: bool = False  # True when type is forced by page context
    new_visit_scheduled_at: str = ""
    new_visit_error: str = ""
    new_visit_is_saving: bool = False
    new_visit_patient_accounts: list[PatientAccountOption] = []
    new_visit_account_id: str = ""
    new_visit_account_name: str = ""
    # ── No-account alert ──────────────────────────────────────────────────────────
    show_no_account_alert: bool = False
    no_account_patient_id: str = ""

    @rx.event
    async def on_load(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_operator, self.is_doctor)
        if redirect:
            return redirect
        from datetime import date
        today = date.today()
        self.calendar_year = today.year
        self.calendar_month = today.month
        await self._load_companies()
        await self._load_visits()

    @rx.event
    async def on_load_consultations(self):
        """on_load for /consultations — pre-filters to consultation type."""
        await self._load_roles()
        redirect = await self._require_any_of(self.is_operator, self.is_doctor)
        if redirect:
            return redirect
        from datetime import date
        today = date.today()
        self.calendar_year = today.year
        self.calendar_month = today.month
        self.filter_visit_type = "consultation"
        await self._load_companies()
        await self._load_visits()

    @rx.event
    async def on_load_campaign_visits(self):
        """on_load for /campaign-visits — pre-filters to campaign type."""
        await self._load_roles()
        redirect = await self._require_any_of(self.is_operator, self.is_doctor)
        if redirect:
            return redirect
        from datetime import date
        today = date.today()
        self.calendar_year = today.year
        self.calendar_month = today.month
        self.filter_visit_type = "campaign"
        await self._load_companies()
        await self._load_visits()

    async def _on_account_picked(self, account_id: str) -> None:
        self.filter_account_id = account_id
        await self._load_visits()

    @rx.event
    async def set_search(self, value: str):
        self.search = value
        await self._load_visits()

    @rx.event
    async def set_view_mode(self, value: str | list[str]):
        """Switch between list and calendar view."""
        self.view_mode = value
        if value == "calendar":
            from datetime import date
            today = date.today()
            self.calendar_year = today.year
            self.calendar_month = today.month
            self._apply_calendar_date_filter()
        else:
            self.filter_date_from = ""
            self.filter_date_to = ""
        await self._load_visits()

    @rx.event
    async def calendar_prev_month(self):
        """Navigate to the previous month."""
        if self.calendar_month == 1:
            self.calendar_month = 12
            self.calendar_year -= 1
        else:
            self.calendar_month -= 1
        self._apply_calendar_date_filter()
        await self._load_visits()

    @rx.event
    async def calendar_next_month(self):
        """Navigate to the next month."""
        if self.calendar_month == 12:
            self.calendar_month = 1
            self.calendar_year += 1
        else:
            self.calendar_month += 1
        self._apply_calendar_date_filter()
        await self._load_visits()

    @rx.event
    async def set_filter_visit_type(self, value: str):
        self.filter_visit_type = value
        await self._load_visits()

    @rx.event
    async def set_filter_status(self, value: str):
        self.filter_status = value
        await self._load_visits()

    @rx.event
    async def set_filter_account(self, value: str):
        self.filter_account_id = value if value != "ALL" else ""
        await self._load_visits()

    @rx.event
    async def set_filter_date_from(self, value: str):
        self.filter_date_from = value
        await self._load_visits()

    @rx.event
    async def set_filter_date_to(self, value: str):
        self.filter_date_to = value
        await self._load_visits()

    @rx.event
    async def clear_filters(self):
        """Reset all filters and reload."""
        self.search = ""
        self.filter_status = "ALL"
        self.filter_visit_type = "ALL"
        self.filter_account_id = ""
        if self.view_mode == "calendar":
            from datetime import date
            today = date.today()
            self.calendar_year = today.year
            self.calendar_month = today.month
            self._apply_calendar_date_filter()
        else:
            self.filter_date_from = ""
            self.filter_date_to = ""
        await self._load_visits()

    @rx.event
    async def set_sort(self, column: str):
        """Sort by column; toggle direction if already sorted by the same column."""
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column
            self.sort_ascending = True
        await self._load_visits()

    @rx.event
    def go_to_visit(self, visit_id: str):
        return rx.redirect(f"/visit/{visit_id}")

    @rx.event
    def go_to_consultation(self, visit_id: str):
        return rx.redirect(f"/consultation/{visit_id}")

    @rx.event
    def go_to_patient(self, patient_id: str):
        return rx.redirect(f"/patient/{patient_id}")

    @rx.event
    async def load_more_visits(self):
        """Append the next page of visits to the current list."""
        self.is_loading_more = True
        await self._load_visits(reset=False)

    # ── New CampaignVisit dialog events ───────────────────────────────────────────────

    @rx.event
    async def open_new_visit_dialog(self):
        await self._open_picker(account_id="")
        if self.filter_visit_type in ("consultation", "campaign"):
            self.new_visit_type = self.filter_visit_type
            self.new_visit_type_locked = True
        else:
            self.new_visit_type = ""
            self.new_visit_type_locked = False
        self.new_visit_scheduled_at = ""
        self.new_visit_error = ""
        self.new_visit_is_saving = False
        self.new_visit_patient_accounts = []
        self.new_visit_account_id = ""
        self.new_visit_account_name = ""
        self.show_new_visit_dialog = True

    @rx.event
    def set_new_visit_type(self, value: str):
        self.new_visit_type = value

    @rx.event
    def close_new_visit_dialog(self):
        self.show_new_visit_dialog = False

    @rx.event
    def set_new_visit_scheduled_at(self, value: str):
        self.new_visit_scheduled_at = value

    @rx.event
    def set_new_visit_account_id(self, value: str):
        """Called from the account select in the dialog."""
        self.new_visit_account_id = value
        matched = next((a for a in self.new_visit_patient_accounts if a.id == value), None)
        self.new_visit_account_name = matched.name if matched else ""

    @rx.event
    def close_no_account_alert(self):
        self.show_no_account_alert = False

    @rx.event
    async def picker_select_patient(self, patient_id: str, label: str):
        """Override to also load the patient's accounts after selection."""
        self.picker_selected_id = patient_id
        self.picker_selected_label = label
        self.picker_is_open = False
        # Reset account selection
        self.new_visit_patient_accounts = []
        self.new_visit_account_id = ""
        self.new_visit_account_name = ""
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
                self.new_visit_patient_accounts = options
                # Auto-select when only one account
                if len(options) == 1:
                    self.new_visit_account_id = options[0].id
                    self.new_visit_account_name = options[0].name
        except Exception as e:
            self.new_visit_error = str(e)

    @rx.event
    async def save_new_visit(self):
        if not self.new_visit_type:
            self.new_visit_error = "Veuillez sélectionner le type de visite."
            return
        if not self.picker_selected_id:
            self.new_visit_error = "Veuillez sélectionner un patient."
            return
        self.new_visit_error = ""
        self.new_visit_is_saving = True
        try:
            if self.new_visit_type == "campaign":
                if not self.new_visit_scheduled_at:
                    self.new_visit_error = "Veuillez sélectionner une date et heure."
                    return
                with await self.authenticate_user():
                    from gws_care.visit.campaign_visit_service import CampaignVisitService
                    _visit, program = CampaignVisitService.create_visit_with_default_campaign(
                        patient_id=self.picker_selected_id,
                        scheduled_at_str=self.new_visit_scheduled_at,
                        billing_account_id=self.new_visit_account_id,
                    )
                self.show_new_visit_dialog = False
                return rx.redirect(f"/campaign/{program.id}")
            else:  # consultation
                with await self.authenticate_user():
                    from datetime import datetime

                    from gws_care.visit.campaign_visit_status import CampaignVisitStatus
                    from gws_care.visit.visit import Visit
                    from gws_care.visit.visit_type import VisitType
                    visit = Visit()
                    visit.visit_type = VisitType.CONSULTATION
                    visit.patient_id = self.picker_selected_id
                    visit.billing_account_id = self.new_visit_account_id or None
                    visit.scheduled_at = (
                        datetime.fromisoformat(self.new_visit_scheduled_at)
                        if self.new_visit_scheduled_at else None
                    )
                    visit.campaign_visit_status = CampaignVisitStatus.PENDING
                    visit.save()
                    visit_id = str(visit.id)
                self.show_new_visit_dialog = False
                return rx.redirect(f"/consultation/{visit_id}")
        except Exception as e:
            self.new_visit_error = str(e)
        finally:
            self.new_visit_is_saving = False

    def _apply_calendar_date_filter(self):
        """Set filter_date_from/to to cover the current calendar month."""
        import calendar
        last_day = calendar.monthrange(self.calendar_year, self.calendar_month)[1]
        self.filter_date_from = f"{self.calendar_year:04d}-{self.calendar_month:02d}-01"
        self.filter_date_to = f"{self.calendar_year:04d}-{self.calendar_month:02d}-{last_day:02d}"

    def _build_calendar(self):
        """Build calendar_days grid from currently loaded visits."""
        import calendar
        from datetime import date

        by_date: dict[str, list[VisitRowDTO]] = {}
        for visit in self.visits:
            if not visit.scheduled_at:
                continue
            day_key = visit.scheduled_at[:10]
            if day_key not in by_date:
                by_date[day_key] = []
            by_date[day_key].append(visit)

        today_str = date.today().isoformat()
        first_weekday, num_days = calendar.monthrange(self.calendar_year, self.calendar_month)
        _MONTHS = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
        self.calendar_month_label = f"{_MONTHS[self.calendar_month - 1]} {self.calendar_year}"

        days: list[CalendarDayDTO] = []
        # Leading padding (week starts on Monday)
        for _ in range(first_weekday):
            days.append(CalendarDayDTO())
        # Days of the month
        for d in range(1, num_days + 1):
            date_str = f"{self.calendar_year:04d}-{self.calendar_month:02d}-{d:02d}"
            days.append(CalendarDayDTO(
                date=date_str,
                day_num=d,
                is_current_month=True,
                is_today=(date_str == today_str),
                visits=by_date.get(date_str, []),
            ))
        # Trailing padding to fill the last row
        remainder = len(days) % 7
        if remainder > 0:
            for _ in range(7 - remainder):
                days.append(CalendarDayDTO())
        self.calendar_days = days

    async def _load_companies(self):
        """Internal: load active accounts for the filter dropdown."""
        try:
            with await self.authenticate_user():
                from gws_care.account.account_service import AccountService
                comps = AccountService.list_accounts()
                self.companies = [
                    AccountOptionDTO(id=str(c.id), name=c.name) for c in comps
                ]
        except Exception:
            self.companies = []

    async def _load_visits(self, reset: bool = True):
        if not await self.check_authentication():
            return

        # In calendar mode always load all (no pagination)
        is_calendar = self.view_mode == "calendar"
        page_limit = None if is_calendar else self._current_page_size

        if reset:
            self._page_offset = 0
            self.is_loading = True
            if not is_calendar:
                from gws_care.core.care_app_config_service import CareAppConfigService
                self._current_page_size = CareAppConfigService.get_page_size()
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.visit.campaign_visit_service import CampaignVisitService
                from gws_care.visit.campaign_visit_status import CampaignVisitStatus
                from gws_care.visit.visit_type import VisitType

                status_filter = (
                    CampaignVisitStatus(self.filter_status)
                    if self.filter_status and self.filter_status != "ALL"
                    else None
                )
                vt_filter = None
                if self.filter_visit_type == "campaign":
                    vt_filter = VisitType.CAMPAIGN
                elif self.filter_visit_type == "consultation":
                    vt_filter = VisitType.CONSULTATION
                # Scope to the doctor's own visits when a DOCTOR-role user is linked
                # to a MedicalDoctor record. Admins and unlinked doctors see all.
                scoped_doctor_id = None
                if self._linked_doctor_id and not self.is_admin and self.is_doctor:
                    scoped_doctor_id = self._linked_doctor_id

                visits = CampaignVisitService.list_all(
                    visit_type=vt_filter,
                    status=status_filter,
                    search=self.search,
                    account_id=self.filter_account_id or None,
                    date_from=self.filter_date_from or None,
                    date_to=self.filter_date_to or None,
                    doctor_id=scoped_doctor_id,
                    limit=(self._current_page_size + 1) if page_limit else None,
                    offset=self._page_offset if not is_calendar else 0,
                )
                if page_limit:
                    has_more = len(visits) > self._current_page_size
                    visits = visits[:self._current_page_size]
                else:
                    has_more = False
                visit_rows = []
                for v in visits:
                    campaign_name = ""
                    if v.campaign_id:
                        try:
                            campaign_name = v.campaign.name
                        except Exception:
                            campaign_name = ""
                    from gws_care.visit.visit_type import VisitType as _VT
                    if v.visit_type == _VT.CONSULTATION and v.consultation_visit_status:
                        row_status = v.consultation_visit_status.value
                        row_label = v.consultation_visit_status.get_label()
                    else:
                        row_status = v.campaign_visit_status.value
                        row_label = v.campaign_visit_status.get_label()
                    visit_rows.append(VisitRowDTO(
                        id=str(v.id),
                        patient_id=str(v.patient_id),
                        patient_name=v.patient.get_full_name() if v.patient_id else "",
                        account_name=v.billing_account.name if v.billing_account_id else None,
                        campaign_name=campaign_name,
                        scheduled_at=v.scheduled_at.isoformat() if v.scheduled_at else "",
                        campaign_visit_status=row_status,
                        status_label=row_label,
                        visit_number=v.visit_number or "",
                        visit_type=v.visit_type.value if v.visit_type else "",
                    ))
                sort_col = self.sort_column
                all_rows = visit_rows if reset else self.visits + visit_rows
                self.visits = sorted(
                    all_rows,
                    key=lambda row: (getattr(row, sort_col) or "").lower(),
                    reverse=not self.sort_ascending,
                )
                self.has_more = has_more
                if not is_calendar:
                    self._page_offset += self._current_page_size
                if self.view_mode == "calendar":
                    self._build_calendar()
        except Exception as e:
            self.error_message = f"Error loading visits: {e}"
        finally:
            self.is_loading = False
            self.is_loading_more = False
