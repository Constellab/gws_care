"""State for the appointment create / edit form dialog."""

from typing import AsyncGenerator

import reflex as rx
from gws_reflex_base import FormDialogState
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class ExamTypeOption(BaseModel):
    id: str
    name: str
    category_label: str


class DoctorOption(BaseModel):
    id: str
    name: str
    specialty: str = ""
    doctor_record_id: str = ""   # MedicalDoctor.id (for campaign assignment reference)


class AppointmentFormState(FormDialogState, rx.State):
    """Manages the create / update appointment dialog."""

    # Form fields
    form_patient_id: str = ""
    form_patient_label: str = ""   # display only (read-only when opened from patient detail)
    form_account_id: str = ""
    form_scheduled_at: str = ""    # YYYY-MM-DDTHH:MM  (set from slot selection)
    form_exam_type: str = ""       # ExamTypeRef.id (optional)
    form_notes: str = ""
    form_doctor_id: str = ""       # assigned_doctor_id
    form_duration: str = "20"      # minutes
    form_room: str = ""            # room/cabinet
    form_appointment_mode: str = "visio"   # AppointmentMode value
    form_error: str = ""

    # Slot picker (secretary booking flow)
    form_booking_date: str = ""          # YYYY-MM-DD selected by secretary
    form_available_slots: list[str] = [] # "YYYY-MM-DDTHH:MM" available slots
    form_slots_loading: bool = False

    # Exam type options loaded from referential
    exam_type_options: list[ExamTypeOption] = []
    # Doctor options loaded from MedicalDoctor (enriched with specialty)
    doctor_options: list[DoctorOption] = []
    # Specialty filter for the doctor picker
    specialty_filter: str = ""
    specialty_options: list[str] = []
    specialty_search: str = ""       # search input for specialty step

    # Patient options for standalone mode: list of [id, label]
    patient_options: list[list[str]] = []  # [[id, "LAST First (P0001)"], ...]

    # Step wizard: 1=specialty, 2=doctor, 3=date+slot
    booking_step: int = 1
    selected_doctor_name: str = ""  # display name of picked doctor
    form_doctor_days_str: str = ""  # human-readable available days
    form_slots_error: str = ""      # visible error from slot loading

    # Set when editing an existing appointment
    _editing_appointment_id: str = ""

    # ── Setters ───────────────────────────────────────────────────────────────

    @rx.event
    def set_form_account_id(self, value: str):
        self.form_account_id = value

    @rx.event
    def set_form_scheduled_at(self, value: str):
        self.form_scheduled_at = value

    @rx.event
    def set_form_exam_type(self, value: str):
        self.form_exam_type = "" if value == "_none_" else value

    @rx.event
    def set_form_notes(self, value: str):
        self.form_notes = value

    @rx.event
    def set_form_patient_id(self, value: str):
        self.form_patient_id = value

    @rx.var
    def filtered_specialty_options(self) -> list[str]:
        """Specialty options filtered by the search input."""
        if not self.specialty_search:
            return self.specialty_options
        q = self.specialty_search.lower()
        return [s for s in self.specialty_options if q in s.lower()]

    @rx.event
    def set_specialty_search(self, value: str):
        self.specialty_search = value

    @rx.event
    def set_specialty_filter(self, value: str):
        """Filter the doctor options list by specialty."""
        self.specialty_filter = value if value != "_all_" else ""
        self._load_doctor_options()
        # Reset doctor selection if current doctor no longer in filtered list
        if self.form_doctor_id and not any(
            d.id == self.form_doctor_id for d in self.doctor_options
        ):
            self.form_doctor_id = ""
            self.form_scheduled_at = ""
            self.form_available_slots = []

    @rx.event
    def select_booking_specialty(self, specialty: str):
        """Step 1 → 2: user picked a specialty (or 'all')."""
        self.specialty_filter = "" if specialty == "_all_" else specialty
        self.specialty_search = ""
        self._load_doctor_options()
        self.form_doctor_id = ""
        self.selected_doctor_name = ""
        self.form_scheduled_at = ""
        self.form_available_slots = []
        self.form_booking_date = ""
        self.booking_step = 2

    @rx.event
    async def select_booking_doctor_card(self, doctor_id: str, doctor_name: str):
        """Step 2 → 3: find next available date for this doctor, then load its slots."""
        self.form_doctor_id = doctor_id
        self.selected_doctor_name = doctor_name
        self.form_scheduled_at = ""
        self.form_available_slots = []
        self.form_doctor_days_str = ""
        self.form_slots_error = ""
        self.booking_step = 3
        # Find which days of the week this doctor declared availability, then
        # pre-select the nearest upcoming date that falls on one of those days.
        try:
            _main = await self.get_state(ReflexMainState)
            with await _main.authenticate_user():
                from datetime import date, timedelta
                from gws_care.scheduling.doctor_schedule import DoctorScheduleService
                _DAY_NAMES = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
                blocks = DoctorScheduleService.list_for_doctor(doctor_id)
                available_weekdays = sorted({b.day_of_week for b in blocks})
                self.form_doctor_days_str = (
                    ", ".join(_DAY_NAMES[d] for d in available_weekdays)
                    if available_weekdays else ""
                )
                today = date.today()
                next_date = today
                if available_weekdays:
                    for offset in range(14):
                        candidate = today + timedelta(days=offset)
                        if candidate.weekday() in available_weekdays:
                            next_date = candidate
                            break
                self.form_booking_date = next_date.strftime("%Y-%m-%d")
        except Exception as exc:
            from datetime import date
            self.form_booking_date = date.today().strftime("%Y-%m-%d")
            print(f"[select_booking_doctor_card] schedule lookup error: {exc}")
        await self._load_available_slots()

    @rx.event
    def go_back_to_step(self, step: int):
        """Navigate back to a previous step."""
        self.booking_step = step
        if step <= 1:
            self.specialty_filter = ""
            self.form_doctor_id = ""
            self.selected_doctor_name = ""
            self._load_doctor_options()
        if step <= 2:
            self.form_doctor_id = ""
            self.selected_doctor_name = ""
            self.form_doctor_days_str = ""
        self.form_scheduled_at = ""
        self.form_available_slots = []
        self.form_booking_date = ""
        self.form_slots_error = ""

    @rx.event
    def set_form_doctor_id(self, value: str):
        self.form_doctor_id = "" if value == "_none_" else value
        # Reset slot selection when doctor changes
        self.form_scheduled_at = ""
        self.form_available_slots = []

    @rx.event
    async def set_form_booking_date(self, value: str):
        self.form_booking_date = value
        self.form_scheduled_at = ""
        await self._load_available_slots()

    @rx.event
    async def set_form_doctor_and_reload(self, value: str):
        self.form_doctor_id = "" if value == "_none_" else value
        self.form_scheduled_at = ""
        self.form_available_slots = []
        if self.form_doctor_id and self.form_booking_date:
            await self._load_available_slots()

    @rx.event
    def set_form_slot(self, slot: str):
        """Select a time slot — sets form_scheduled_at."""
        self.form_scheduled_at = slot

    async def _load_available_slots(self):
        """Load available slots for current doctor + date."""
        if not self.form_doctor_id or not self.form_booking_date:
            self.form_available_slots = []
            return
        self.form_slots_loading = True
        self.form_slots_error = ""
        try:
            _main = await self.get_state(ReflexMainState)
            with await _main.authenticate_user():
                from datetime import date
                from gws_care.scheduling.doctor_schedule import DoctorScheduleService
                d = date.fromisoformat(self.form_booking_date)
                slots = DoctorScheduleService.available_slots(self.form_doctor_id, d)
                self.form_available_slots = [s.strftime("%Y-%m-%dT%H:%M") for s in slots]
                # auto-select first slot
                if self.form_available_slots and not self.form_scheduled_at:
                    self.form_scheduled_at = self.form_available_slots[0]
        except Exception as exc:
            self.form_slots_error = f"Erreur chargement créneaux : {exc}"
            print(f"[appointment_form] Failed to load slots: {exc}")
            self.form_available_slots = []
        finally:
            self.form_slots_loading = False

    @rx.event
    def set_form_duration(self, value: str):
        self.form_duration = value

    @rx.event
    def set_form_room(self, value: str):
        self.form_room = value

    @rx.event
    def set_form_appointment_mode(self, value: str):
        self.form_appointment_mode = value

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _load_exam_type_options(self) -> None:
        """Load exam type options from the active referential."""
        try:
            from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
            refs = (
                ExamTypeRef.select()
                .where(ExamTypeRef.is_active == True)
                .order_by(ExamTypeRef.category, ExamTypeRef.name)
            )
            self.exam_type_options = [
                ExamTypeOption(id=str(r.id), name=r.name, category_label=r.get_category_label())
                for r in refs
            ]
        except Exception as exc:
            print(f"[appointment_form] Failed to load exam type options: {exc}")
            self.exam_type_options = []

    def _load_doctor_options(self) -> None:
        """Load active, non-archived MedicalDoctor records for the doctor picker.

        Uses MedicalDoctor.id as the option id so that DoctorScheduleService.available_slots
        can be called directly with the selected doctor id.
        """
        try:
            from gws_care.doctor.medical_doctor import MedicalDoctor

            all_options: list[DoctorOption] = []
            for md in (
                MedicalDoctor.select()
                .where((MedicalDoctor.is_active == True) & (MedicalDoctor.is_archived == False))
                .order_by(MedicalDoctor.last_name, MedicalDoctor.first_name)
            ):
                all_options.append(DoctorOption(
                    id=str(md.id),
                    name=md.get_full_name(),
                    specialty=md.specialization or "",
                    doctor_record_id=str(md.id),
                ))

            specs = sorted({o.specialty for o in all_options if o.specialty})
            self.specialty_options = specs

            if self.specialty_filter:
                self.doctor_options = [o for o in all_options if o.specialty == self.specialty_filter]
            else:
                self.doctor_options = all_options
        except Exception as exc:
            print(f"[appointment_form] Failed to load doctor options: {exc}")
            self.doctor_options = []
            self.specialty_options = []

    # ── Open ──────────────────────────────────────────────────────────────────

    @rx.event
    def open_create_dialog(self, patient_id: str, patient_label: str = "", account_id: str = ""):
        """Open the dialog pre-filled with a patient."""
        self.form_patient_id = patient_id
        self.form_patient_label = patient_label
        self.form_account_id = account_id
        self.form_scheduled_at = ""
        self.form_exam_type = ""
        self.form_notes = ""
        self.form_doctor_id = ""
        self.form_duration = "20"
        self.form_room = ""
        self.form_appointment_mode = "visio"
        self.form_booking_date = ""
        self.form_available_slots = []
        self.form_slots_loading = False
        self.specialty_filter = ""
        self.specialty_search = ""
        self.booking_step = 1
        self.selected_doctor_name = ""
        self._editing_appointment_id = ""
        self.is_update_mode = False
        self._load_exam_type_options()
        self._load_doctor_options()
        self.dialog_opened = True

    @rx.event
    async def open_create_dialog_standalone(self):
        """Open the dialog without a pre-selected patient (from appointments page)."""
        self.form_patient_id = ""
        self.form_patient_label = ""
        self.form_account_id = ""
        self.form_scheduled_at = ""
        self.form_exam_type = ""
        self.form_notes = ""
        self.form_doctor_id = ""
        self.form_duration = "20"
        self.form_room = ""
        self.form_appointment_mode = "visio"
        self.form_booking_date = ""
        self.form_available_slots = []
        self.form_slots_loading = False
        self.specialty_filter = ""
        self.booking_step = 1
        self.selected_doctor_name = ""
        self._editing_appointment_id = ""
        self.is_update_mode = False
        self._load_exam_type_options()
        self._load_doctor_options()
        # If the current user is a doctor with a MedicalDoctor record, pre-select them
        try:
            _main = await self.get_state(ReflexMainState)
            with await _main.authenticate_user() as auth_user:
                from gws_care.doctor.medical_doctor import MedicalDoctor
                md = MedicalDoctor.get_or_none(
                    (MedicalDoctor.user == auth_user.id)
                    & (MedicalDoctor.is_active == True)
                    & (MedicalDoctor.is_archived == False)
                )
                if md:
                    self.form_doctor_id = str(md.id)
        except Exception:
            pass
        # Load patient options for the selector
        try:
            from gws_care.patient.patient_service import PatientService
            patients = PatientService.search_patients()
            self.patient_options = [
                [str(p.id), f"{p.last_name} {p.first_name} ({p.patient_number})"]
                for p in patients
            ]
        except Exception as exc:
            print(f"[appointment_form] Failed to load patient options: {exc}")
            self.patient_options = []
        self.dialog_opened = True

    @rx.event(background=True)
    async def confirm_booking(self):
        """Submit the booking form — usable from button on_click without form_data."""
        async with self:
            self.is_loading = True
        try:
            if self.is_update_mode:
                async for event in self._update({}):
                    yield event
            else:
                async for event in self._create({}):
                    yield event
        except Exception as exc:
            yield rx.toast.error(str(exc))
        finally:
            async with self:
                self.is_loading = False
        async with self:
            await self.close_dialog()

    @rx.event
    def open_edit_dialog(self, appointment_id: str):
        """Open the dialog for editing an existing appointment."""
        self._editing_appointment_id = appointment_id
        # Fields will be filled by a background load; open dialog immediately
        self.is_update_mode = True
        self.dialog_opened = True

    # ── FormDialogState implementation ───────────────────────────────────────

    async def _clear_form_state(self) -> None:
        self.form_patient_id = ""
        self.form_patient_label = ""
        self.form_account_id = ""
        self.form_scheduled_at = ""
        self.form_exam_type = ""
        self.form_notes = ""
        self.form_doctor_id = ""
        self.form_duration = "20"
        self.form_room = ""
        self.form_booking_date = ""
        self.form_available_slots = []
        self.form_slots_loading = False
        self.patient_options = []
        self.exam_type_options = []
        self.doctor_options = []
        self.specialty_filter = ""
        self.specialty_search = ""
        self.specialty_options = []
        self.booking_step = 1
        self.selected_doctor_name = ""
        self.form_doctor_days_str = ""
        self.form_slots_error = ""
        self._editing_appointment_id = ""
        self.is_update_mode = False
        self.form_appointment_mode = "visio"
        self.form_error = ""

    async def _create(self, form_data: dict) -> AsyncGenerator:
        """Create a new consultation visit from the admin booking wizard."""
        async with self:
            self.form_error = ""
            # Snapshot every field under the lock — reading self.xxx outside
            # async with self: in a background event can return a stale value
            # from before the user's last edit (e.g. an earlier auto-selected
            # slot instead of the date/time they actually picked).
            scheduled_at = self.form_scheduled_at
            patient_id = self.form_patient_id
            doctor_id = self.form_doctor_id
            notes = self.form_notes
            account_id = self.form_account_id
            appt_mode = self.form_appointment_mode

        if not scheduled_at:
            async with self:
                self.form_error = "Veuillez sélectionner un créneau disponible."
            return
        if not patient_id:
            async with self:
                self.form_error = "Veuillez sélectionner un patient."
            return
        if not doctor_id:
            async with self:
                self.form_error = "Veuillez sélectionner un médecin."
            return

        async with self:
            _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            from gws_care.visit.consultation_service import ConsultationService
            from gws_care.visit.visit_dto import BookAppointmentDTO
            dto = BookAppointmentDTO(
                scheduled_at=scheduled_at,
                doctor_id=doctor_id or None,
                appointment_mode=appt_mode or "visio",
                appointment_address=None,
                patient_notes=notes or None,
                billing_account_id=account_id or None,
            )
            ConsultationService.create_from_patient_booking(dto, patient_id)

        yield rx.toast.success("Rendez-vous créé")
        from ..patient_detail.patient_detail_state import PatientDetailState
        from ..appointments_list.appointments_list_state import AppointmentsListState
        yield PatientDetailState.on_load()
        yield AppointmentsListState.on_load()

    async def _update(self, form_data: dict) -> AsyncGenerator:
        """Update an existing appointment."""
        async with self:
            self.form_error = ""
            # Snapshot every field under the lock — see _create() for why.
            scheduled_at = self.form_scheduled_at
            exam_type = self.form_exam_type
            patient_id = self.form_patient_id
            account_id = self.form_account_id
            notes = self.form_notes
            doctor_id = self.form_doctor_id
            duration = self.form_duration
            room = self.form_room
            editing_appointment_id = self._editing_appointment_id

        if not scheduled_at:
            async with self:
                self.form_error = "Scheduled date/time is required."
            return
        if not exam_type:
            async with self:
                self.form_error = "Exam type is required."
            return

        async with self:
            _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            from gws_care.appointment.appointment_dto import SaveAppointmentDTO
            from gws_care.appointment.appointment_service import AppointmentService

            dto = SaveAppointmentDTO(
                patient_id=patient_id,
                account_id=account_id or None,
                scheduled_at=scheduled_at,
                exam_type_ref_id=exam_type or None,
                notes=notes or None,
                assigned_doctor_id=doctor_id or None,
                duration_minutes=int(duration or 20),
                room=room or None,
            )
            AppointmentService.update_appointment(editing_appointment_id, dto)

        yield rx.toast.success("Rendez-vous mis à jour")
        from .appointment_list_state import AppointmentListState
        from ..patient_detail.patient_detail_state import PatientDetailState
        from ..appointments_list.appointments_list_state import AppointmentsListState
        yield AppointmentListState.on_load()
        yield PatientDetailState.on_load()
        yield AppointmentsListState.on_load()
