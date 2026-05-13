"""State for the visit list / calendar page."""

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


class VisitRowDTO(BaseModel):
    id: str
    patient_name: str
    patient_id: str
    account_name: str | None = None
    campaign_name: str = ""
    scheduled_at: str = ""  # empty for program visits without a scheduled date
    status: str
    status_label: str = ""
    visit_number: str = ""


class AccountOptionDTO(BaseModel):
    """Lightweight account option for filter dropdown."""

    id: str
    name: str


class PatientOptionDTO(BaseModel):
    """Lightweight patient option for the new-visit dialog."""

    id: str
    label: str  # "Last, First (N° dossier)"


class CalendarDayDTO(BaseModel):
    """One cell in the monthly calendar grid."""

    date: str = ""          # "YYYY-MM-DD"; empty for padding cells
    day_num: int = 0        # 0 for padding cells
    is_current_month: bool = False
    is_today: bool = False
    visits: list[VisitRowDTO] = []


class VisitListState(RoleState):
    """State for the /visits page."""

    visits: list[VisitRowDTO] = []
    companies: list[AccountOptionDTO] = []
    is_loading: bool = False
    error_message: str = ""
    search: str = ""
    filter_status: str = "ALL"
    filter_account_id: str = ""
    filter_date_from: str = ""
    filter_date_to: str = ""
    sort_column: str = "scheduled_at"
    sort_ascending: bool = True

    # View mode: "list" or "calendar"
    view_mode: str = "list"
    calendar_year: int = 2026
    calendar_month: int = 1
    calendar_month_label: str = ""
    calendar_days: list[CalendarDayDTO] = []

    # ── New Visit dialog ──────────────────────────────────────────────────────
    show_new_visit_dialog: bool = False
    new_visit_patient_search: str = ""
    new_visit_patient_results: list[PatientOptionDTO] = []
    new_visit_patient_id: str = ""
    new_visit_patient_label: str = ""
    new_visit_scheduled_at: str = ""
    new_visit_account_id: str = ""
    new_visit_error: str = ""
    new_visit_is_saving: bool = False

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
    def go_to_patient(self, patient_id: str):
        return rx.redirect(f"/patient/{patient_id}")

    # ── New Visit dialog events ───────────────────────────────────────────────

    @rx.event
    async def open_new_visit_dialog(self):
        self.new_visit_patient_search = ""
        self.new_visit_patient_results = []
        self.new_visit_patient_id = ""
        self.new_visit_patient_label = ""
        self.new_visit_scheduled_at = ""
        self.new_visit_account_id = ""
        self.new_visit_error = ""
        self.new_visit_is_saving = False
        self.show_new_visit_dialog = True

    @rx.event
    def close_new_visit_dialog(self):
        self.show_new_visit_dialog = False

    @rx.event
    async def search_new_visit_patient(self, query: str):
        self.new_visit_patient_search = query
        self.new_visit_patient_results = []
        self.new_visit_patient_id = ""
        self.new_visit_patient_label = ""
        if len(query.strip()) < 2:
            return
        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_service import PatientService
                patients = PatientService.search_patients(search=query.strip(), limit=10)
                self.new_visit_patient_results = [
                    PatientOptionDTO(
                        id=str(p.id),
                        label=f"{p.last_name} {p.first_name} ({p.patient_number})",
                    )
                    for p in patients
                ]
        except Exception:
            self.new_visit_patient_results = []

    @rx.event
    def select_new_visit_patient(self, patient_id: str, label: str):
        self.new_visit_patient_id = patient_id
        self.new_visit_patient_label = label
        self.new_visit_patient_search = label
        self.new_visit_patient_results = []

    @rx.event
    def set_new_visit_scheduled_at(self, value: str):
        self.new_visit_scheduled_at = value

    @rx.event
    def set_new_visit_account_id(self, value: str):
        self.new_visit_account_id = "" if value == "none" else value

    @rx.event
    async def save_new_visit(self):
        if not self.new_visit_patient_id:
            self.new_visit_error = "Please select a patient."
            return
        if not self.new_visit_scheduled_at:
            self.new_visit_error = "Please select a date and time."
            return
        self.new_visit_error = ""
        self.new_visit_is_saving = True
        try:
            with await self.authenticate_user():
                from gws_care.visit.visit_service import VisitService
                _visit, program = VisitService.create_visit_with_default_program(
                    patient_id=self.new_visit_patient_id,
                    scheduled_at_str=self.new_visit_scheduled_at,
                    billing_account_id=self.new_visit_account_id or None,
                )
            self.show_new_visit_dialog = False
            return rx.redirect(f"/program/{program.id}")
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

    async def _load_visits(self):
        if not await self.check_authentication():
            return

        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.visit.visit_service import VisitService
                from gws_care.visit.visit_status import VisitStatus

                status_filter = (
                    VisitStatus(self.filter_status)
                    if self.filter_status and self.filter_status != "ALL"
                    else None
                )
                visits = VisitService.list_all(
                    status=status_filter,
                    search=self.search,
                    account_id=self.filter_account_id or None,
                    date_from=self.filter_date_from or None,
                    date_to=self.filter_date_to or None,
                )
                visit_rows = []
                for v in visits:
                    campaign_name = ""
                    if v.program_id:
                        try:
                            campaign_name = v.program.name
                        except Exception:
                            campaign_name = ""
                    visit_rows.append(VisitRowDTO(
                        id=str(v.id),
                        patient_id=str(v.patient_id),
                        patient_name=v.patient.get_full_name() if v.patient_id else "",
                        account_name=v.billing_account.name if v.billing_account_id else None,
                        campaign_name=campaign_name,
                        scheduled_at=v.scheduled_at.isoformat() if v.scheduled_at else "",
                        status=v.status.value,
                        status_label=v.status.get_label(),
                        visit_number=v.visit_number or "",
                    ))
                sort_col = self.sort_column
                self.visits = sorted(
                    visit_rows,
                    key=lambda row: (getattr(row, sort_col) or "").lower(),
                    reverse=not self.sort_ascending,
                )
                if self.view_mode == "calendar":
                    self._build_calendar()
        except Exception as e:
            self.error_message = f"Error loading visits: {e}"
        finally:
            self.is_loading = False
