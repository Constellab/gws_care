"""State for the /appointments page — scheduling view of consultation visits."""

import reflex as rx
from pydantic import BaseModel

from ..common.account_picker_state import AccountPickerRowDTO
from ..common.combined_picker_state import CombinedPickerState
from ..common.patient_picker_state import PatientPickerRowDTO


class AppointmentRowDTO(BaseModel):
    """One row in the appointments scheduling table."""

    id: str
    visit_number: str = ""
    patient_name: str = ""
    patient_id: str = ""
    scheduled_at: str = ""
    appointment_mode: str = ""
    doctor_name: str = ""
    doctor_id: str = ""
    status: str = ""
    status_label: str = ""


class AppointmentPatientAccount(BaseModel):
    """One account linked to the selected patient in the new-appointment dialog."""

    id: str
    name: str


class CalendarDayDTO(BaseModel):
    """One cell in the monthly calendar grid."""

    date: str = ""
    day_num: int = 0
    is_current_month: bool = False
    is_today: bool = False
    appointments: list[AppointmentRowDTO] = []


class AppointmentsListState(CombinedPickerState):
    """State for the /appointments scheduling page."""

    # ── Patient picker vars ─────────────────────────────────────────────────────
    picker_patients: list[PatientPickerRowDTO] = []
    picker_is_loading: bool = False
    picker_error: str = ""
    picker_filter_name: str = ""
    picker_filter_number: str = ""
    picker_account_id: str = ""
    picker_is_open: bool = False
    picker_selected_id: str = ""
    picker_selected_label: str = ""

    # ── Account picker vars ─────────────────────────────────────────────────────
    acct_picker_is_open: bool = False
    acct_picker_filter: str = ""
    acct_picker_accounts: list[AccountPickerRowDTO] = []
    acct_picker_is_loading: bool = False
    acct_picker_error: str = ""
    acct_picker_selected_id: str = ""
    acct_picker_selected_name: str = ""

    # ── Data ────────────────────────────────────────────────────────────────────
    appointments: list[AppointmentRowDTO] = []
    is_loading: bool = False
    error_message: str = ""

    # ── Filters ─────────────────────────────────────────────────────────────────
    filter_from: str = ""
    filter_to: str = ""
    filter_mode: str = ""
    filter_doctor: str = ""
    filter_status: str = ""
    doctor_options: list[str] = []

    # ── Sort ────────────────────────────────────────────────────────────────────
    sort_column: str = "scheduled_at"
    sort_ascending: bool = True

    # ── View mode ───────────────────────────────────────────────────────────────
    view_mode: str = "list"
    calendar_year: int = 2026
    calendar_month: int = 1
    calendar_month_label: str = ""
    calendar_days: list[CalendarDayDTO] = []

    # ── New appointment dialog ──────────────────────────────────────────────────
    show_new_appt_dialog: bool = False
    new_appt_scheduled_at: str = ""
    new_appt_mode: str = ""
    new_appt_address: str = ""
    new_appt_error: str = ""
    new_appt_is_saving: bool = False
    new_appt_patient_accounts: list[AppointmentPatientAccount] = []
    new_appt_account_id: str = ""

    # ── Patient picker events ────────────────────────────────────────────────────

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
    async def picker_select_patient(self, patient_id: str, label: str):
        """Select a patient and preload their accounts for the dialog."""
        self.picker_selected_id = patient_id
        self.picker_selected_label = label
        self.picker_is_open = False
        self.new_appt_patient_accounts = []
        self.new_appt_account_id = ""
        if not patient_id:
            return
        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_account import PatientAccount
                links = list(PatientAccount.select().where(PatientAccount.patient == patient_id))
                options = [
                    AppointmentPatientAccount(id=str(link.account_id), name=link.account.name)
                    for link in links
                ]
                self.new_appt_patient_accounts = options
                if len(options) == 1:
                    self.new_appt_account_id = options[0].id
        except Exception as e:
            self.new_appt_error = str(e)

    # ── Account picker events ───────────────────────────────────────────────────

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

    # ── Page lifecycle ──────────────────────────────────────────────────────────

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
        await self._load_appointments()

    # ── Filter / sort events ────────────────────────────────────────────────────

    @rx.event
    def set_filter_from(self, value: str):
        self.filter_from = value

    @rx.event
    def set_filter_to(self, value: str):
        self.filter_to = value

    @rx.event
    def set_filter_mode(self, value: str):
        self.filter_mode = "" if value == "ALL" else value

    @rx.event
    def set_filter_doctor(self, value: str):
        self.filter_doctor = "" if value == "ALL" else value

    @rx.event
    def set_filter_status(self, value: str):
        self.filter_status = "" if value == "ALL" else value

    @rx.event
    def set_sort(self, column: str):
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column
            self.sort_ascending = True

    @rx.event
    async def set_view_mode(self, value: str | list[str]):
        self.view_mode = value
        if value == "calendar":
            from datetime import date
            today = date.today()
            self.calendar_year = today.year
            self.calendar_month = today.month
            self._apply_calendar_date_filter()
        else:
            self.filter_from = ""
            self.filter_to = ""
        await self._load_appointments()

    @rx.event
    async def calendar_prev_month(self):
        if self.calendar_month == 1:
            self.calendar_month = 12
            self.calendar_year -= 1
        else:
            self.calendar_month -= 1
        self._apply_calendar_date_filter()
        await self._load_appointments()

    @rx.event
    async def calendar_next_month(self):
        if self.calendar_month == 12:
            self.calendar_month = 1
            self.calendar_year += 1
        else:
            self.calendar_month += 1
        self._apply_calendar_date_filter()
        await self._load_appointments()

    @rx.event
    async def clear_filters(self):
        self.filter_mode = ""
        self.filter_doctor = ""
        self.filter_status = ""
        if self.view_mode == "calendar":
            from datetime import date
            today = date.today()
            self.calendar_year = today.year
            self.calendar_month = today.month
            self._apply_calendar_date_filter()
            await self._load_appointments()
        else:
            self.filter_from = ""
            self.filter_to = ""

    # ── Navigation ──────────────────────────────────────────────────────────────

    @rx.event
    def go_to_appointment(self, appt_id: str):
        return rx.redirect(f"/appointment/{appt_id}")

    @rx.event
    def go_to_consultation(self, visit_id: str):
        return rx.redirect(f"/consultation/{visit_id}")

    @rx.event
    def go_to_patient(self, patient_id: str):
        return rx.redirect(f"/patient/{patient_id}")

    # ── New appointment dialog ──────────────────────────────────────────────────

    @rx.event
    async def open_new_appt_dialog(self):
        await self._open_picker(account_id="")
        self.new_appt_scheduled_at = ""
        self.new_appt_mode = ""
        self.new_appt_address = ""
        self.new_appt_error = ""
        self.new_appt_is_saving = False
        self.new_appt_patient_accounts = []
        self.new_appt_account_id = ""
        self.show_new_appt_dialog = True

    @rx.event
    def close_new_appt_dialog(self):
        self.show_new_appt_dialog = False

    @rx.event
    def set_new_appt_scheduled_at(self, value: str):
        self.new_appt_scheduled_at = value

    @rx.event
    def set_new_appt_mode(self, value: str):
        self.new_appt_mode = value
        self.new_appt_address = ""

    @rx.event
    def set_new_appt_address(self, value: str):
        self.new_appt_address = value

    @rx.event
    def open_new_appt_address_in_google_maps(self):
        from urllib.parse import quote
        if self.new_appt_address:
            encoded = quote(self.new_appt_address, safe="")
            return rx.call_script(
                f"window.open('https://www.google.com/maps/search/?api=1&query={encoded}', '_blank')"
            )

    @rx.event
    def set_new_appt_account_id(self, value: str):
        self.new_appt_account_id = value

    @rx.event
    async def save_new_appt(self):
        if not self.picker_selected_id:
            self.new_appt_error = "Veuillez sélectionner un patient."
            return
        if not self.new_appt_scheduled_at:
            self.new_appt_error = "Veuillez sélectionner une date et heure."
            return
        self.new_appt_error = ""
        self.new_appt_is_saving = True
        try:
            with await self.authenticate_user():
                from datetime import datetime

                from gws_care.visit.appointment_mode import AppointmentMode
                from gws_care.visit.consultation_visit_status import ConsultationVisitStatus
                from gws_care.visit.visit import Visit
                from gws_care.visit.visit_type import VisitType

                visit = Visit()
                visit.visit_type = VisitType.CONSULTATION
                visit.patient_id = self.picker_selected_id
                visit.billing_account_id = self.new_appt_account_id or None
                visit.scheduled_at = datetime.fromisoformat(self.new_appt_scheduled_at)
                visit.consultation_visit_status = ConsultationVisitStatus.SCHEDULED
                if self.new_appt_mode:
                    visit.appointment_mode = AppointmentMode(self.new_appt_mode)
                if self.new_appt_address:
                    visit.appointment_address = self.new_appt_address
                visit.save()
                visit_id = str(visit.id)
            self.show_new_appt_dialog = False
            return rx.redirect(f"/consultation/{visit_id}")
        except Exception as e:
            self.new_appt_error = str(e)
        finally:
            self.new_appt_is_saving = False

    # ── Computed var ────────────────────────────────────────────────────────────

    @rx.var
    def filtered_sorted_appointments(self) -> list[AppointmentRowDTO]:
        rows = self.appointments
        if self.filter_from:
            rows = [r for r in rows if r.scheduled_at >= self.filter_from]
        if self.filter_to:
            rows = [r for r in rows if r.scheduled_at <= self.filter_to + "T23:59:59"]
        if self.filter_mode:
            rows = [r for r in rows if r.appointment_mode == self.filter_mode]
        if self.filter_doctor:
            rows = [r for r in rows if r.doctor_name == self.filter_doctor]
        if self.filter_status:
            rows = [r for r in rows if r.status == self.filter_status]
        col = self.sort_column
        return sorted(
            rows,
            key=lambda r: (getattr(r, col) or "").lower(),
            reverse=not self.sort_ascending,
        )

    # ── Internal ────────────────────────────────────────────────────────────────

    def _apply_calendar_date_filter(self):
        import calendar
        last_day = calendar.monthrange(self.calendar_year, self.calendar_month)[1]
        self.filter_from = f"{self.calendar_year:04d}-{self.calendar_month:02d}-01"
        self.filter_to = f"{self.calendar_year:04d}-{self.calendar_month:02d}-{last_day:02d}"

    def _build_calendar(self):
        import calendar
        from datetime import date

        by_date: dict[str, list[AppointmentRowDTO]] = {}
        for appt in self.appointments:
            if not appt.scheduled_at:
                continue
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
        for _ in range(first_weekday):
            days.append(CalendarDayDTO())
        for d in range(1, num_days + 1):
            date_str = f"{self.calendar_year:04d}-{self.calendar_month:02d}-{d:02d}"
            days.append(CalendarDayDTO(
                date=date_str,
                day_num=d,
                is_current_month=True,
                is_today=(date_str == today_str),
                appointments=by_date.get(date_str, []),
            ))
        remainder = len(days) % 7
        if remainder > 0:
            for _ in range(7 - remainder):
                days.append(CalendarDayDTO())
        self.calendar_days = days

    async def _load_appointments(self):
        if not await self.check_authentication():
            return
        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.visit.campaign_visit_service import CampaignVisitService
                from gws_care.visit.visit_type import VisitType

                scoped_doctor_id = None
                if self._linked_doctor_id and not self.is_admin and self.is_doctor:
                    scoped_doctor_id = self._linked_doctor_id

                is_calendar = self.view_mode == "calendar"
                visits = CampaignVisitService.list_all(
                    visit_type=VisitType.CONSULTATION,
                    doctor_id=scoped_doctor_id,
                    date_from=self.filter_from if is_calendar else None,
                    date_to=self.filter_to if is_calendar else None,
                )
                rows: list[AppointmentRowDTO] = []
                seen_doctors: set[str] = set()
                doctor_opts: list[str] = []
                for v in visits:
                    doctor_name = v.doctor.get_full_name() if v.doctor_id else ""
                    if doctor_name and doctor_name not in seen_doctors:
                        seen_doctors.add(doctor_name)
                        doctor_opts.append(doctor_name)
                    cvs = v.consultation_visit_status
                    rows.append(AppointmentRowDTO(
                        id=str(v.id),
                        visit_number=v.visit_number or "",
                        patient_name=v.patient.get_full_name() if v.patient_id else "",
                        patient_id=str(v.patient_id) if v.patient_id else "",
                        scheduled_at=v.scheduled_at.isoformat() if v.scheduled_at else "",
                        appointment_mode=v.appointment_mode.value if v.appointment_mode else "",
                        doctor_name=doctor_name,
                        doctor_id=str(v.doctor_id) if v.doctor_id else "",
                        status=cvs.value if cvs else "",
                        status_label=cvs.get_label() if cvs else "",
                    ))
                self.appointments = rows
                self.doctor_options = sorted(doctor_opts)
                if is_calendar:
                    self._build_calendar()
        except Exception as e:
            self.error_message = f"Error loading appointments: {e}"
        finally:
            self.is_loading = False

