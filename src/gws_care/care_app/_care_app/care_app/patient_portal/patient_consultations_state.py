"""State for the My Consultations patient portal page (/my-consultations).

Shows consultations filtered to the logged-in patient only.
"""

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


class PatientConsultationRowDTO(BaseModel):
    id: str
    visit_number: str = ""
    scheduled_at: str = ""
    status: str = ""
    status_label: str = ""
    exam_count: int = 0
    account_name: str = ""


class CalendarDayDTO(BaseModel):
    date: str = ""
    day_num: int = 0
    is_current_month: bool = False
    is_today: bool = False
    visits: list[PatientConsultationRowDTO] = []


class PatientConsultationsState(RoleState):
    """State for the /my-consultations page."""

    consultations: list[PatientConsultationRowDTO] = []
    is_loading: bool = False
    error_message: str = ""

    # Filters
    filter_status: str = "ALL"
    filter_date_from: str = ""
    filter_date_to: str = ""

    # Sorting
    sort_column: str = "scheduled_at"
    sort_ascending: bool = False

    # Calendar
    view_mode: str = "list"
    calendar_year: int = 2026
    calendar_month: int = 1
    calendar_month_label: str = ""
    calendar_days: list[CalendarDayDTO] = []

    # ── Page guard ────────────────────────────────────────────────────────

    @rx.event
    async def on_load(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_patient_user, redirect_to="/dashboard")
        if redirect:
            return redirect
        from datetime import date
        today = date.today()
        self.calendar_year = today.year
        self.calendar_month = today.month
        await self._load_consultations()

    # ── Filters ──────────────────────────────────────────────────────────

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
    def set_sort(self, column: str):
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column
            self.sort_ascending = True

    @rx.event
    async def clear_filters(self):
        self.filter_status = "ALL"
        self.filter_date_from = ""
        self.filter_date_to = ""
        await self._load_consultations()

    # ── View mode + calendar navigation ──────────────────────────────────────

    @rx.event
    async def set_view_mode(self, value: str | list[str]):
        self.view_mode = value
        if value == "calendar":
            from datetime import date
            today = date.today()
            self.calendar_year = today.year
            self.calendar_month = today.month
        await self._load_consultations()

    @rx.event
    async def calendar_prev_month(self):
        if self.calendar_month == 1:
            self.calendar_month = 12
            self.calendar_year -= 1
        else:
            self.calendar_month -= 1
        await self._load_consultations()

    @rx.event
    async def calendar_next_month(self):
        if self.calendar_month == 12:
            self.calendar_month = 1
            self.calendar_year += 1
        else:
            self.calendar_month += 1
        await self._load_consultations()

    # ── Navigation ────────────────────────────────────────────────────────

    @rx.event
    def go_to_consultation(self, visit_id: str):
        return rx.redirect(f"/consultation/{visit_id}")

    # ── Data loader ────────────────────────────────────────────────────────

    @rx.var
    def filtered_consultations(self) -> list[PatientConsultationRowDTO]:
        rows = self.consultations
        if self.filter_status and self.filter_status != "ALL":
            rows = [r for r in rows if r.status == self.filter_status]
        if self.filter_date_from:
            rows = [r for r in rows if r.scheduled_at >= self.filter_date_from]
        if self.filter_date_to:
            rows = [r for r in rows if r.scheduled_at <= self.filter_date_to]
        col = self.sort_column
        return sorted(
            rows,
            key=lambda r: str(getattr(r, col) or "").lower(),
            reverse=not self.sort_ascending,
        )

    async def _load_consultations(self):
        if not await self.check_authentication():
            return
        patient_id = self._linked_patient_id
        if not patient_id:
            self.consultations = []
            return

        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.visit.consultation_service import ConsultationService
                visits = ConsultationService.list_for_patient(patient_id)
                rows = []
                for v in visits:
                    exam_count = 0
                    try:
                        from gws_care.exam.exam import Exam
                        exam_count = Exam.select().where(Exam.visit == v.id).count()
                    except Exception:
                        pass
                    cvs = v.consultation_visit_status
                    account_name = ""
                    try:
                        if v.billing_account_id:
                            account_name = v.billing_account.name
                    except Exception:
                        pass
                    rows.append(PatientConsultationRowDTO(
                        id=str(v.id),
                        visit_number=v.visit_number or "",
                        scheduled_at=v.scheduled_at.isoformat()[:10] if v.scheduled_at else "",
                        status=cvs.value if cvs else "",
                        status_label=cvs.get_label() if cvs else "",
                        exam_count=exam_count,
                        account_name=account_name,
                    ))
                self.consultations = rows
                if self.view_mode == "calendar":
                    self._build_calendar()
        except Exception as e:
            self.error_message = f"Error loading consultations: {e}"
        finally:
            self.is_loading = False

    def _build_calendar(self):
        import calendar
        from datetime import date

        by_date: dict[str, list[PatientConsultationRowDTO]] = {}
        for row in self.consultations:
            if not row.scheduled_at:
                continue
            key = row.scheduled_at[:10]
            by_date.setdefault(key, []).append(row)

        today_str = date.today().isoformat()
        first_weekday, num_days = calendar.monthrange(self.calendar_year, self.calendar_month)
        _MONTHS = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
        self.calendar_month_label = f"{_MONTHS[self.calendar_month - 1]} {self.calendar_year}"

        days: list[CalendarDayDTO] = []
        for _ in range(first_weekday):
            days.append(CalendarDayDTO())
        for d in range(1, num_days + 1):
            date_str = f"{self.calendar_year:04d}-{self.calendar_month:02d}-{d:02d}"
            days.append(CalendarDayDTO(
                date=date_str,
                day_num=d,
                is_current_month=True,
                is_today=(date_str == today_str),
                visits=by_date.get(date_str, []),
            ))
        remainder = len(days) % 7
        if remainder:
            for _ in range(7 - remainder):
                days.append(CalendarDayDTO())
        self.calendar_days = days
