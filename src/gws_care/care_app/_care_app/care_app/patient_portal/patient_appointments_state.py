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
    doctor_id: str = ""
    appointment_mode: str = ""
    appointment_mode_label: str = ""


class CalendarDayDTO(BaseModel):
    date: str = ""
    day_num: int = 0
    is_current_month: bool = False
    is_today: bool = False
    visits: list[AppointmentRowDTO] = []


class DoctorOptionDTO(BaseModel):
    id: str           # MedicalDoctor.id (used for booking DTO and DoctorScheduleService slot queries)
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

    # ── Filters (list view only) ──────────────────────────────────────────────
    filter_from: str = ""
    filter_to: str = ""
    filter_status: str = ""

    # ── Sort ──────────────────────────────────────────────────────────────────
    sort_column: str = "scheduled_at"
    sort_ascending: bool = True

    # ── Booking dialog (Doctolib-style step wizard) ───────────────────────────
    show_booking_dialog: bool = False
    booking_step: int = 1              # 1=specialty, 2=doctor, 3=date+slot
    booking_specialty: str = ""        # selected specialty filter
    booking_doctor_id: str = ""        # MedicalDoctor.id (for DTO and slot queries)
    booking_doctor_name: str = ""
    booking_scheduled_at: str = ""     # chosen slot "YYYY-MM-DDTHH:MM"
    booking_date: str = ""             # chosen date "YYYY-MM-DD"
    booking_available_slots: list[str] = []
    booking_slots_loading: bool = False
    booking_mode: str = "at_home"
    booking_address: str = ""
    booking_notes: str = ""
    booking_error: str = ""
    booking_is_saving: bool = False

    # Doctor options for the picker
    doctor_options: list[DoctorOptionDTO] = []
    booking_available_specialties: list[str] = []
    filtered_booking_doctors: list[DoctorOptionDTO] = []
    booking_specialty_search: str = ""  # search input for specialty step

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

    # ── Filter / sort events ──────────────────────────────────────────────────

    @rx.event
    def set_filter_from(self, value: str):
        self.filter_from = value

    @rx.event
    def set_filter_to(self, value: str):
        self.filter_to = value

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
    def clear_filters(self):
        self.filter_from = ""
        self.filter_to = ""
        self.filter_status = ""

    # ── Computed var ──────────────────────────────────────────────────────────

    @rx.var
    def filtered_sorted_appointments(self) -> list[AppointmentRowDTO]:
        rows = self.appointments
        if self.filter_from:
            rows = [r for r in rows if r.scheduled_at >= self.filter_from]
        if self.filter_to:
            rows = [r for r in rows if r.scheduled_at <= self.filter_to + "T23:59:59"]
        if self.filter_status:
            rows = [r for r in rows if r.status == self.filter_status]
        col = self.sort_column
        return sorted(rows, key=lambda r: (getattr(r, col) or "").lower(), reverse=not self.sort_ascending)

    # ── Navigation ────────────────────────────────────────────────────────────

    @rx.event
    def go_to_appointment(self, appt_id: str):
        return rx.redirect(f"/appointment/{appt_id}")

    @rx.event
    def go_to_consultation(self, visit_id: str):
        return rx.redirect(f"/consultation/{visit_id}")

    # ── Booking dialog ────────────────────────────────────────────────────────

    @rx.var
    def filtered_booking_specialties(self) -> list[str]:
        """Specialties filtered by the search input."""
        if not self.booking_specialty_search:
            return self.booking_available_specialties
        q = self.booking_specialty_search.lower()
        return [s for s in self.booking_available_specialties if q in s.lower()]

    @rx.event
    def set_booking_specialty_search(self, value: str):
        self.booking_specialty_search = value

    @rx.event
    async def open_booking_dialog(self):
        self.booking_step = 1
        self.booking_specialty = ""
        self.booking_specialty_search = ""
        self.booking_scheduled_at = ""
        self.booking_doctor_id = ""
        self.booking_doctor_name = ""
        self.booking_date = ""
        self.booking_available_slots = []
        self.booking_slots_loading = False
        self.booking_mode = "at_home"
        self.booking_address = ""
        self.booking_notes = ""
        self.booking_error = ""
        self.booking_is_saving = False
        self.filtered_booking_doctors = list(self.doctor_options)
        self.show_booking_dialog = True

    @rx.event
    def close_booking_dialog(self):
        self.show_booking_dialog = False

    @rx.event
    def select_patient_booking_specialty(self, specialty: str):
        """Step 1 → 2: patient chose a specialty."""
        self.booking_specialty = "" if specialty == "_all_" else specialty
        self.booking_specialty_search = ""
        if self.booking_specialty:
            self.filtered_booking_doctors = [
                d for d in self.doctor_options if d.specialization == self.booking_specialty
            ]
        else:
            self.filtered_booking_doctors = list(self.doctor_options)
        self.booking_doctor_id = ""
        self.booking_doctor_name = ""
        self.booking_scheduled_at = ""
        self.booking_available_slots = []
        self.booking_date = ""
        self.booking_step = 2

    @rx.event
    async def select_patient_booking_doctor(self, doctor_id: str, doctor_name: str):
        """Step 2 → 3: patient clicked a doctor card; pre-load today's slots."""
        self.booking_doctor_id = doctor_id
        self.booking_doctor_name = doctor_name
        self.booking_scheduled_at = ""
        self.booking_available_slots = []
        from datetime import date
        self.booking_date = date.today().strftime("%Y-%m-%d")
        self.booking_step = 3
        # Load slots for today immediately
        await self._load_slots_for_date(self.booking_date)

    async def _load_slots_for_date(self, date_str: str):
        """Internal helper — loads available slots for booking_doctor_id + date_str."""
        if not self.booking_doctor_id or not date_str:
            return
        self.booking_slots_loading = True
        try:
            with await self.authenticate_user():
                from datetime import date as date_type
                from gws_care.scheduling.doctor_schedule import DoctorScheduleService
                d = date_type.fromisoformat(date_str)
                slots = DoctorScheduleService.available_slots(self.booking_doctor_id, d)
                self.booking_available_slots = [s.strftime("%Y-%m-%dT%H:%M") for s in slots]
                if self.booking_available_slots:
                    self.booking_scheduled_at = self.booking_available_slots[0]
        except Exception as exc:
            print(f"[patient_appointments] Failed to load slots: {exc}")
        finally:
            self.booking_slots_loading = False

    @rx.event
    def booking_go_back(self, step: int):
        self.booking_step = step
        if step <= 1:
            self.booking_specialty = ""
            self.filtered_booking_doctors = list(self.doctor_options)
            self.booking_doctor_id = ""
            self.booking_doctor_name = ""
        if step <= 2:
            self.booking_doctor_id = ""
            self.booking_doctor_name = ""
        self.booking_scheduled_at = ""
        self.booking_available_slots = []
        self.booking_date = ""

    @rx.event
    async def set_booking_date_and_load_slots(self, value: str):
        self.booking_date = value
        self.booking_scheduled_at = ""
        self.booking_available_slots = []
        await self._load_slots_for_date(value)

    @rx.event
    def select_booking_slot(self, slot: str):
        self.booking_scheduled_at = slot

    @rx.event
    def set_booking_mode(self, value: str):
        self.booking_mode = value

    @rx.event
    def set_booking_address(self, value: str):
        self.booking_address = value

    @rx.event
    def open_booking_address_in_google_maps(self):
        from urllib.parse import quote
        if self.booking_address:
            encoded = quote(self.booking_address, safe="")
            return rx.call_script(
                f"window.open('https://www.google.com/maps/search/?api=1&query={encoded}', '_blank')"
            )

    @rx.event
    def set_booking_notes(self, value: str):
        self.booking_notes = value

    @rx.event
    async def submit_booking(self):
        if not self.booking_scheduled_at:
            self.booking_error = "Veuillez sélectionner un créneau disponible."
            return
        if not self.booking_doctor_id:
            self.booking_error = "Veuillez sélectionner un médecin."
            return
        patient_id = self._linked_patient_id
        if not patient_id:
            self.booking_error = "Identité patient introuvable. Contactez votre administrateur."
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
                    appointment_address=self.booking_address or None,
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
                    .where((MedicalDoctor.is_active == True) & (MedicalDoctor.is_archived == False))
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
                self.filtered_booking_doctors = list(self.doctor_options)
                specs = sorted({d.specialization for d in self.doctor_options if d.specialization})
                self.booking_available_specialties = specs
        except Exception:
            self.doctor_options = []
            self.filtered_booking_doctors = []
            self.booking_available_specialties = []

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
                        doctor_id=str(v.doctor_id) if v.doctor_id else "",
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
