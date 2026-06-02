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
    campaign_name: str = ""  # non-empty for rows inferred from campaign enrollments
    linked_exam_id: str = ""  # non-empty when an exam was created for this appointment


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
    sort_column: str = "scheduled_at"
    sort_ascending: bool = True

    # When navigating from a patient page — pre-filter to show only that patient's appointments
    patient_context_id: str = ""
    patient_context_name: str = ""

    # View mode: "list" or "calendar"
    view_mode: str = "list"
    calendar_year: int = 2026
    calendar_month: int = 1
    calendar_month_label: str = ""
    calendar_days: list[CalendarDayDTO] = []

    # ── Pagination (list mode only; calendar is date-bounded) ────────────
    page: int = 1
    page_size: int = 50
    total_count: int = 0

    @rx.var
    def total_pages(self) -> int:
        return max(1, (self.total_count + self.page_size - 1) // self.page_size)

    @rx.var
    def has_prev_page(self) -> bool:
        return self.page > 1

    @rx.var
    def has_next_page(self) -> bool:
        return self.page < self.total_pages

    @rx.event
    def set_patient_context(self, patient_id: str, patient_name: str):
        """Pre-filter appointments for a specific patient (called from patient detail navigation)."""
        self.patient_context_id = patient_id
        self.patient_context_name = patient_name

    @rx.event
    async def clear_patient_context(self):
        """Remove the patient pre-filter and reload all appointments."""
        self.patient_context_id = ""
        self.patient_context_name = ""
        await self._load_appointments()

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
        self.page = 1
        await self._load_appointments()

    @rx.event
    async def set_view_mode(self, value: str | list[str]):
        """Switch between list and calendar view."""
        self.view_mode = value if isinstance(value, str) else value[0]
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
        self.page = 1
        await self._load_appointments()

    @rx.event
    async def set_filter_account(self, value: str):
        self.filter_account_id = value if value != "ALL" else ""
        self.page = 1
        await self._load_appointments()

    @rx.event
    async def set_filter_date_from(self, value: str):
        self.filter_date_from = value
        self.page = 1
        await self._load_appointments()

    @rx.event
    async def set_filter_date_to(self, value: str):
        self.filter_date_to = value
        self.page = 1
        await self._load_appointments()

    @rx.event
    async def prev_page(self):
        if self.has_prev_page:
            self.page -= 1
            await self._load_appointments()

    @rx.event
    async def next_page(self):
        if self.has_next_page:
            self.page += 1
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
    async def set_sort(self, column: str):
        """Sort by column; toggle direction if already sorted by the same column."""
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column
            self.sort_ascending = True
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
    async def go_to_or_create_exam(self, appointment_id: str):
        """Navigate to the exam linked to this appointment, creating it if none exists."""
        try:
            with await self.authenticate_user():
                from datetime import date
                from gws_care.appointment.appointment import Appointment
                from gws_care.exam.exam import Exam as ExamModel
                from gws_care.exam.exam_type import ExamStatus

                # Check if an exam already exists for this appointment
                tag = f"APPT:{appointment_id}"
                existing = ExamModel.get_or_none(ExamModel.reason_for_visit == tag)
                if existing:
                    return rx.redirect(f"/exam/{existing.id}")

                # Create a new exam pre-filled from appointment data
                appt = Appointment.get_by_id(appointment_id)
                ex = ExamModel()
                ex.patient_id = appt.patient_id
                ex.billing_account_id = appt.billing_account_id
                ex.exam_date = appt.scheduled_at.date() if appt.scheduled_at else date.today()
                ex.exam_type = appt.exam_type
                ex.exam_type_ref_id = appt.exam_type_ref_id
                ex.reason_for_visit = tag
                ex.status = ExamStatus.DRAFT
                ex.save()
                return rx.redirect(f"/exam/{ex.id}")
        except Exception as e:
            self.error_message = f"Erreur création fiche: {e}"

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

    @staticmethod
    def _preload_acct_names(appts: list) -> dict[str, str]:
        """Batch-load billing account names to avoid N+1 (1 SELECT for all)."""
        ids = {str(a.billing_account_id) for a in appts if a.billing_account_id}
        if not ids:
            return {}
        from gws_care.account.account import Account
        return {
            str(a.id): a.name
            for a in Account.select(Account.id, Account.name).where(Account.id.in_(ids))
        }

    @staticmethod
    def _get_exam_link_map(appt_ids: list[str]) -> dict[str, str]:
        """Batch-query exam records linked via reason_for_visit='APPT:{id}'.

        Returns {appointment_id: exam_id}.
        """
        if not appt_ids:
            return {}
        from gws_care.exam.exam import Exam as ExamModel
        tags = [f"APPT:{aid}" for aid in appt_ids]
        result: dict[str, str] = {}
        for ex in ExamModel.select(ExamModel.id, ExamModel.reason_for_visit).where(
            ExamModel.reason_for_visit.in_(tags)
        ):
            if ex.reason_for_visit and ex.reason_for_visit.startswith("APPT:"):
                result[ex.reason_for_visit[5:]] = str(ex.id)
        return result

    async def _load_companies(self):
        """Internal: load active accounts for the filter dropdown."""
        try:
            with await self.authenticate_user():
                from gws_care.account.account_service import AccountService
                comps = AccountService.list_accounts()
                self.companies = [
                    AccountOptionDTO(id=str(c.id), name=c.name) for c in comps
                ]
        except Exception as exc:
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
                common_kwargs = dict(
                    status=status_filter,
                    search=self.search,
                    account_id=self.filter_account_id or None,
                    date_from=self.filter_date_from or None,
                    date_to=self.filter_date_to or None,
                )

                if self.view_mode == "calendar":
                    # Calendar mode: bounded by date range — no pagination needed
                    appts = AppointmentService.list_all(**common_kwargs)
                    acct_map = self._preload_acct_names(appts)
                    exam_map = self._get_exam_link_map([str(a.id) for a in appts if a.id])
                    appt_rows = [
                        AppointmentRowDTO(
                            id=str(a.id),
                            patient_id=str(a.patient_id),
                            patient_name=f"{a.patient.first_name} {a.patient.last_name}",
                            account_name=acct_map.get(str(a.billing_account_id)) if a.billing_account_id else None,
                            scheduled_at=a.scheduled_at.isoformat(),
                            exam_type_label=a.exam_type.get_label(),
                            status=a.status.value,
                            linked_exam_id=exam_map.get(str(a.id), ""),
                        )
                        for a in appts
                    ]
                    self.appointments = appt_rows
                    self._build_calendar()
                elif self.patient_context_id:
                    # Per-patient view: show all appointments for this patient (bounded set)
                    appts = AppointmentService.list_for_patient(self.patient_context_id)
                    acct_map = self._preload_acct_names(appts)
                    exam_map = self._get_exam_link_map([str(a.id) for a in appts if a.id])
                    appt_rows = [
                        AppointmentRowDTO(
                            id=str(a.id),
                            patient_id=str(a.patient_id),
                            patient_name=f"{a.patient.first_name} {a.patient.last_name}",
                            account_name=acct_map.get(str(a.billing_account_id)) if a.billing_account_id else None,
                            scheduled_at=a.scheduled_at.isoformat(),
                            exam_type_label=a.exam_type.get_label(),
                            status=a.status.value,
                            linked_exam_id=exam_map.get(str(a.id), ""),
                        )
                        for a in appts
                    ]
                    # Also show campaign-inferred appointments for this specific patient
                    from gws_care.campaign.campaign import Campaign as CampaignModel
                    from gws_care.campaign.campaign_exam import CampaignExam
                    from gws_care.campaign.campaign_patient import CampaignPatient
                    from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
                    cp_rows = list(
                        CampaignPatient.select(CampaignPatient, CampaignModel)
                        .join(CampaignModel)
                        .where(CampaignPatient.patient == self.patient_context_id)
                    )
                    all_cp_campaign_ids = [str(cp.campaign_id) for cp in cp_rows]
                    ce_by_campaign: dict[str, list] = {}
                    if all_cp_campaign_ids:
                        for ce in (
                            CampaignExam.select(CampaignExam, ExamTypeRef)
                            .join(ExamTypeRef)
                            .where(CampaignExam.campaign.in_(all_cp_campaign_ids))
                        ):
                            ce_by_campaign.setdefault(str(ce.campaign_id), []).append(ce)
                    for cp in cp_rows:
                        campaign_obj = cp.campaign
                        campaign_start = (
                            campaign_obj.start_date.isoformat() if campaign_obj.start_date else ""
                        )
                        for ce in ce_by_campaign.get(str(cp.campaign_id), []):
                            appt_rows.append(AppointmentRowDTO(
                                id="",
                                patient_id=self.patient_context_id,
                                patient_name=self.patient_context_name,
                                scheduled_at=campaign_start + "T00:00:00" if campaign_start else "",
                                exam_type_label=ce.exam_type_ref.name,
                                status="campaign",
                                campaign_name=campaign_obj.name,
                            ))
                    sort_col = self.sort_column
                    self.appointments = sorted(
                        appt_rows,
                        key=lambda row: (getattr(row, sort_col) or "").lower(),
                        reverse=not self.sort_ascending,
                    )
                    self.total_count = len(self.appointments)
                else:
                    # Global list mode — paginated SQL
                    self.total_count = AppointmentService.count_all(**common_kwargs)
                    self.page = max(1, min(self.page, self.total_pages))
                    appts = AppointmentService.list_all_paginated(
                        **common_kwargs,
                        limit=self.page_size,
                        offset=(self.page - 1) * self.page_size,
                    )
                    acct_map = self._preload_acct_names(appts)
                    exam_map = self._get_exam_link_map([str(a.id) for a in appts if a.id])
                    self.appointments = [
                        AppointmentRowDTO(
                            id=str(a.id),
                            patient_id=str(a.patient_id),
                            patient_name=f"{a.patient.first_name} {a.patient.last_name}",
                            account_name=acct_map.get(str(a.billing_account_id)) if a.billing_account_id else None,
                            scheduled_at=a.scheduled_at.isoformat(),
                            exam_type_label=a.exam_type.get_label(),
                            status=a.status.value,
                            linked_exam_id=exam_map.get(str(a.id), ""),
                        )
                        for a in appts
                    ]
        except Exception as e:
            self.error_message = f"Error loading appointments: {e}"
        finally:
            self.is_loading = False
