"""State for the appointment list page."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class AppointmentRowDTO(BaseModel):
    id: str
    patient_name: str
    patient_id: str
    account_name: str | None = None
    scheduled_at: str
    exam_type_label: str
    status: str


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
    appointments: list[AppointmentRowDTO] = []


class AppointmentListState(ReflexMainState):
    """State for the /appointments page."""

    appointments: list[AppointmentRowDTO] = []
    companies: list[AccountOptionDTO] = []
    is_loading: bool = False
    error_message: str = ""
    search: str = ""
    filter_status: str = "ALL"  # "ALL" = no filter
    filter_account_id: str = ""
    filter_date_from: str = ""
    filter_date_to: str = ""

    # View mode: "list" or "calendar"
    view_mode: str = "list"
    calendar_year: int = 2026
    calendar_month: int = 1
    calendar_month_label: str = ""
    calendar_days: list[CalendarDayDTO] = []

    @rx.event
    async def on_load(self):
        from datetime import date
        today = date.today()
        self.calendar_year = today.year
        self.calendar_month = today.month
        await self._load_companies()
        await self._load_appointments()

    @rx.event
    async def set_search(self, value: str):
        self.search = value
        await self._load_appointments()

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
        await self._load_appointments()

    @rx.event
    async def calendar_prev_month(self):
        """Navigate to the previous month."""
        if self.calendar_month == 1:
            self.calendar_month = 12
            self.calendar_year -= 1
        else:
            self.calendar_month -= 1
        self._apply_calendar_date_filter()
        await self._load_appointments()

    @rx.event
    async def calendar_next_month(self):
        """Navigate to the next month."""
        if self.calendar_month == 12:
            self.calendar_month = 1
            self.calendar_year += 1
        else:
            self.calendar_month += 1
        self._apply_calendar_date_filter()
        await self._load_appointments()

    @rx.event
    async def set_filter_status(self, value: str):
        self.filter_status = value
        await self._load_appointments()

    @rx.event
    async def set_filter_account(self, value: str):
        self.filter_account_id = value if value != "ALL" else ""
        await self._load_appointments()

    @rx.event
    async def set_filter_date_from(self, value: str):
        self.filter_date_from = value
        await self._load_appointments()

    @rx.event
    async def set_filter_date_to(self, value: str):
        self.filter_date_to = value
        await self._load_appointments()

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
        await self._load_appointments()

    @rx.event
    async def cancel_appointment(self, appointment_id: str):
        """Cancel an appointment from the list."""
        try:
            with await self.authenticate_user():
                from gws_care.appointment.appointment_service import AppointmentService
                AppointmentService.cancel_appointment(appointment_id)
            await self._load_appointments()
        except Exception as e:
            self.error_message = f"Error: {e}"

    @rx.event
    async def start_appointment(self, appointment_id: str):
        """Mark appointment as In Progress."""
        try:
            with await self.authenticate_user():
                from gws_care.appointment.appointment_service import AppointmentService
                AppointmentService.start_appointment(appointment_id)
            await self._load_appointments()
        except Exception as e:
            self.error_message = f"Error: {e}"

    @rx.event
    async def complete_appointment(self, appointment_id: str):
        """Mark appointment as Done."""
        try:
            with await self.authenticate_user():
                from gws_care.appointment.appointment_service import AppointmentService
                AppointmentService.complete_appointment(appointment_id)
            await self._load_appointments()
        except Exception as e:
            self.error_message = f"Error: {e}"

    @rx.event
    def go_to_patient(self, patient_id: str):
        return rx.redirect(f"/patient/{patient_id}")

    def _apply_calendar_date_filter(self):
        """Set filter_date_from/to to cover the current calendar month."""
        import calendar
        last_day = calendar.monthrange(self.calendar_year, self.calendar_month)[1]
        self.filter_date_from = f"{self.calendar_year:04d}-{self.calendar_month:02d}-01"
        self.filter_date_to = f"{self.calendar_year:04d}-{self.calendar_month:02d}-{last_day:02d}"

    def _build_calendar(self):
        """Build calendar_days grid from currently loaded appointments."""
        import calendar
        from datetime import date

        by_date: dict[str, list[AppointmentRowDTO]] = {}
        for appt in self.appointments:
            day_key = appt.scheduled_at[:10]
            if day_key not in by_date:
                by_date[day_key] = []
            by_date[day_key].append(appt)

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
                appointments=by_date.get(date_str, []),
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

    async def _load_appointments(self):
        if not await self.check_authentication():
            return

        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.appointment.appointment_service import AppointmentService
                from gws_care.appointment.appointment_status import AppointmentStatus

                status_filter = (
                    AppointmentStatus(self.filter_status)
                    if self.filter_status and self.filter_status != "ALL"
                    else None
                )
                appts = AppointmentService.list_all(
                    status=status_filter,
                    search=self.search,
                    account_id=self.filter_account_id or None,
                    date_from=self.filter_date_from or None,
                    date_to=self.filter_date_to or None,
                )
                self.appointments = [
                    AppointmentRowDTO(
                        id=str(a.id),
                        patient_id=str(a.patient_id),
                        patient_name=f"{a.patient.first_name} {a.patient.last_name}",
                        account_name=a.billing_account.name if a.billing_account_id else None,
                        scheduled_at=a.scheduled_at.isoformat(),
                        exam_type_label=a.exam_type.get_label(),
                        status=a.status.value,
                    )
                    for a in appts
                ]
                if self.view_mode == "calendar":
                    self._build_calendar()
        except Exception as e:
            self.error_message = f"Error loading appointments: {e}"
        finally:
            self.is_loading = False
