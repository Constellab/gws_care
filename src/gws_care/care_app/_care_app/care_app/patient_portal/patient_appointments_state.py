"""State for the /my-appointments patient portal page.

Displays the patient's consultation visits (appointments) in list or calendar
view, and provides the "Plan Appointment" booking dialog.
"""

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


class AppointmentRowDTO(BaseModel):
    id: str
    visit_number: str = ""
    scheduled_at: str = ""   # ISO datetime string
    status: str = ""
    status_label: str = ""
    doctor_name: str = ""
    appointment_mode: str = ""
    appointment_mode_label: str = ""


class CalendarDayDTO(BaseModel):
    date: str = ""
    day_num: int = 0
    is_current_month: bool = False
    is_today: bool = False
    visits: list[AppointmentRowDTO] = []


class DoctorOptionDTO(BaseModel):
    id: str
    name: str
    specialization: str = ""


class PatientAppointmentsState(RoleState):
    """State for /my-appointments."""

    appointments: list[AppointmentRowDTO] = []
    is_loading: bool = False
    error_message: str = ""

    # View toggle
    view_mode: str = "list"
    calendar_year: int = 2026
    calendar_month: int = 1
    calendar_month_label: str = ""
    calendar_days: list[CalendarDayDTO] = []

    # ── Booking dialog ────────────────────────────────────────────────────────
    show_booking_dialog: bool = False
    booking_scheduled_at: str = ""
    booking_doctor_id: str = ""
    booking_mode: str = "onsite"
    booking_notes: str = ""
    booking_error: str = ""
    booking_is_saving: bool = False

    # Doctor options for the picker
    doctor_options: list[DoctorOptionDTO] = []

    # ── Page guard ────────────────────────────────────────────────────────────

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
        await self._load_appointments()
        await self._load_doctors()

    # ── View toggle ───────────────────────────────────────────────────────────

    @rx.event
    async def set_view_mode(self, value: str | list[str]):
        self.view_mode = value
        if value == "calendar":
            from datetime import date
            today = date.today()
            self.calendar_year = today.year
            self.calendar_month = today.month
            self._build_calendar()
        await self._load_appointments()

    @rx.event
    async def calendar_prev_month(self):
        if self.calendar_month == 1:
            self.calendar_month = 12
            self.calendar_year -= 1
        else:
            self.calendar_month -= 1
        await self._load_appointments()

    @rx.event
    async def calendar_next_month(self):
        if self.calendar_month == 12:
            self.calendar_month = 1
            self.calendar_year += 1
        else:
            self.calendar_month += 1
        await self._load_appointments()

    # ── Navigation ────────────────────────────────────────────────────────────

    @rx.event
    def go_to_consultation(self, visit_id: str):
        return rx.redirect(f"/consultation/{visit_id}")

    # ── Booking dialog ────────────────────────────────────────────────────────

    @rx.event
    async def open_booking_dialog(self):
        self.booking_scheduled_at = ""
        self.booking_doctor_id = ""
        self.booking_mode = "onsite"
        self.booking_notes = ""
        self.booking_error = ""
        self.booking_is_saving = False
        self.show_booking_dialog = True

    @rx.event
    def close_booking_dialog(self):
        self.show_booking_dialog = False

    @rx.event
    def set_booking_scheduled_at(self, value: str):
        self.booking_scheduled_at = value

    @rx.event
    def set_booking_doctor_id(self, value: str):
        self.booking_doctor_id = "" if value == "none" else value

    @rx.event
    def set_booking_mode(self, value: str):
        self.booking_mode = value

    @rx.event
    def set_booking_notes(self, value: str):
        self.booking_notes = value

    @rx.var
    def booking_min_datetime(self) -> str:
        """ISO datetime string for today (used as min on the date picker)."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%dT%H:%M")

    @rx.event
    async def submit_booking(self):
        if not self.booking_scheduled_at:
            self.booking_error = "Please select a date and time."
            return
        from datetime import datetime
        try:
            if datetime.fromisoformat(self.booking_scheduled_at) <= datetime.now():
                self.booking_error = "The appointment date must be in the future."
                return
        except ValueError:
            self.booking_error = "Invalid date format."
            return
        patient_id = self._linked_patient_id
        if not patient_id:
            self.booking_error = "Patient identity not found. Please contact your administrator."
            return
        self.booking_error = ""
        self.booking_is_saving = True
        try:
            with await self.authenticate_user():
                from gws_care.visit.consultation_service import ConsultationService
                from gws_care.visit.visit_dto import BookAppointmentDTO
                dto = BookAppointmentDTO(
                    scheduled_at=self.booking_scheduled_at,
                    doctor_id=self.booking_doctor_id or None,
                    appointment_mode=self.booking_mode,
                    patient_notes=self.booking_notes or None,
                )
                ConsultationService.create_from_patient_booking(dto, patient_id)
            self.show_booking_dialog = False
            await self._load_appointments()
        except Exception as e:
            self.booking_error = str(e)
        finally:
            self.booking_is_saving = False

    # ── Data loaders ─────────────────────────────────────────────────────────

    async def _load_doctors(self):
        try:
            with await self.authenticate_user():
                from gws_care.doctor.medical_doctor import MedicalDoctor
                doctors = list(
                    MedicalDoctor.select()
                    .where(MedicalDoctor.is_active == True)
                    .order_by(MedicalDoctor.last_name)
                )
                self.doctor_options = [
                    DoctorOptionDTO(
                        id=str(d.id),
                        name=d.get_full_name(),
                        specialization=d.specialization or "",
                    )
                    for d in doctors
                ]
        except Exception:
            self.doctor_options = []

    async def _load_appointments(self):
        if not await self.check_authentication():
            return
        patient_id = self._linked_patient_id
        if not patient_id:
            self.appointments = []
            return
        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.visit.consultation_service import ConsultationService
                from gws_care.visit.appointment_mode import AppointmentMode
                visits = ConsultationService.list_for_patient(patient_id)
                rows = []
                for v in visits:
                    cvs = v.consultation_visit_status
                    doctor_name = ""
                    if v.doctor_id:
                        try:
                            doctor_name = v.doctor.get_full_name()
                        except Exception:
                            pass
                    mode = v.appointment_mode
                    mode_label = mode.get_label() if mode else ""
                    rows.append(AppointmentRowDTO(
                        id=str(v.id),
                        visit_number=v.visit_number or "",
                        scheduled_at=v.scheduled_at.isoformat() if v.scheduled_at else "",
                        status=cvs.value if cvs else "",
                        status_label=cvs.get_label() if cvs else "",
                        doctor_name=doctor_name,
                        appointment_mode=mode.value if mode else "",
                        appointment_mode_label=mode_label,
                    ))
                self.appointments = rows
                if self.view_mode == "calendar":
                    self._build_calendar()
        except Exception as e:
            self.error_message = f"Error loading appointments: {e}"
        finally:
            self.is_loading = False

    def _build_calendar(self):
        import calendar
        from datetime import date

        by_date: dict[str, list[AppointmentRowDTO]] = {}
        for appt in self.appointments:
            if not appt.scheduled_at:
                continue
            day_key = appt.scheduled_at[:10]
            by_date.setdefault(day_key, []).append(appt)

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
        if remainder > 0:
            for _ in range(7 - remainder):
                days.append(CalendarDayDTO())
        self.calendar_days = days
