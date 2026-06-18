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
    form_error: str = ""

    # Slot picker (secretary booking flow)
    form_booking_date: str = ""          # YYYY-MM-DD selected by secretary
    form_available_slots: list[str] = [] # "YYYY-MM-DDTHH:MM" available slots
    form_slots_loading: bool = False

    # Exam type options loaded from referential
    exam_type_options: list[ExamTypeOption] = []
    # Doctor options: users with MEDECIN_PSC or MEDECIN_ENTREPRISE role
    doctor_options: list[DoctorOption] = []

    # Patient options for standalone mode: list of [id, label]
    patient_options: list[list[str]] = []  # [[id, "LAST First (P0001)"], ...]

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
            if self.exam_type_options and not self.form_exam_type:
                self.form_exam_type = self.exam_type_options[0].id
        except Exception as exc:
            print(f"[appointment_form] Failed to load exam type options: {exc}")
            self.exam_type_options = []

    def _load_doctor_options(self) -> None:
        """Load users with MEDECIN_PSC or MEDECIN_ENTREPRISE role."""
        try:
            from gws_care.role.care_role import CareRole
            from gws_care.role.user_care_role import UserCareRole
            from gws_care.user.user import User
            doctor_roles = [CareRole.MEDECIN_PSC.value, CareRole.MEDECIN_ENTREPRISE.value]
            rows = (
                UserCareRole.select(UserCareRole, User)
                .join(User)
                .where(UserCareRole.role.in_(doctor_roles))
            )
            seen = set()
            options = []
            for row in rows:
                uid = str(row.user.id)
                if uid not in seen:
                    seen.add(uid)
                    sp = getattr(row, "specialty", None) or ""
                    options.append(DoctorOption(
                        id=uid,
                        name=f"Dr {row.user.first_name} {row.user.last_name}",
                        specialty=sp,
                    ))
            self.doctor_options = options
        except Exception as exc:
            print(f"[appointment_form] Failed to load doctor options: {exc}")
            self.doctor_options = []

    # ── Open ──────────────────────────────────────────────────────────────────

    @rx.event
    def open_create_dialog(self, patient_id: str, patient_label: str = ""):
        """Open the dialog pre-filled with a patient."""
        from datetime import date
        self.form_patient_id = patient_id
        self.form_patient_label = patient_label
        self.form_account_id = ""
        self.form_scheduled_at = ""
        self.form_exam_type = ""
        self.form_notes = ""
        self.form_doctor_id = ""
        self.form_duration = "20"
        self.form_room = ""
        self.form_booking_date = date.today().strftime("%Y-%m-%d")
        self.form_available_slots = []
        self.form_slots_loading = False
        self._editing_appointment_id = ""
        self.is_update_mode = False
        self._load_exam_type_options()
        self._load_doctor_options()
        self.dialog_opened = True

    @rx.event
    async def open_create_dialog_standalone(self):
        """Open the dialog without a pre-selected patient (from appointments page)."""
        from datetime import date
        self.form_patient_id = ""
        self.form_patient_label = ""
        self.form_account_id = ""
        self.form_scheduled_at = ""
        self.form_exam_type = ""
        self.form_notes = ""
        self.form_doctor_id = ""
        self.form_duration = "20"
        self.form_room = ""
        self.form_booking_date = date.today().strftime("%Y-%m-%d")
        self.form_available_slots = []
        self.form_slots_loading = False
        self._editing_appointment_id = ""
        self.is_update_mode = False
        self._load_exam_type_options()
        self._load_doctor_options()
        # If the current user is a doctor, pre-select them
        try:
            _main = await self.get_state(ReflexMainState)
            with await _main.authenticate_user() as auth_user:
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_role_service import UserRoleService
                roles = UserRoleService.get_roles_for_user(str(auth_user.id))
                _doctor_roles = {CareRole.MEDECIN_PSC, CareRole.MEDECIN_ENTREPRISE}
                if any(r in _doctor_roles for r in roles):
                    self.form_doctor_id = str(auth_user.id)
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
        self._editing_appointment_id = ""
        self.is_update_mode = False
        self.form_error = ""

    async def _create(self, form_data: dict) -> AsyncGenerator:
        """Create a new appointment."""
        async with self:
            self.form_error = ""
        scheduled_at = self.form_scheduled_at
        if not scheduled_at:
            async with self:
                self.form_error = "Veuillez sélectionner un créneau disponible."
            return
        if not self.form_patient_id:
            async with self:
                self.form_error = "Veuillez sélectionner un patient."
            return
        if not self.form_doctor_id:
            async with self:
                self.form_error = "Veuillez sélectionner un médecin."
            return

        async with self:
            _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            from gws_care.appointment.appointment_dto import SaveAppointmentDTO
            from gws_care.appointment.appointment_service import AppointmentService

            dto = SaveAppointmentDTO(
                patient_id=self.form_patient_id,
                account_id=self.form_account_id or None,
                scheduled_at=scheduled_at,
                exam_type_ref_id=exam_type,
                notes=self.form_notes or None,
                assigned_doctor_id=self.form_doctor_id or None,
                duration_minutes=int(self.form_duration or 20),
                room=self.form_room or None,
            )
            AppointmentService.create_appointment(dto)

        yield rx.toast.success("Appointment created")
        from .appointment_list_state import AppointmentListState
        from ..patient_detail.patient_detail_state import PatientDetailState
        yield AppointmentListState.on_load()
        yield PatientDetailState.on_load()

    async def _update(self, form_data: dict) -> AsyncGenerator:
        """Update an existing appointment."""
        async with self:
            self.form_error = ""
        scheduled_at = self.form_scheduled_at
        exam_type = self.form_exam_type
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
                patient_id=self.form_patient_id,
                account_id=self.form_account_id or None,
                scheduled_at=scheduled_at,
                exam_type_ref_id=exam_type,
                notes=self.form_notes or None,
                assigned_doctor_id=self.form_doctor_id or None,
                duration_minutes=int(self.form_duration or 20),
                room=self.form_room or None,
            )
            AppointmentService.update_appointment(self._editing_appointment_id, dto)

        yield rx.toast.success("Appointment updated")
        from .appointment_list_state import AppointmentListState
        from ..patient_detail.patient_detail_state import PatientDetailState
        yield AppointmentListState.on_load()
        yield PatientDetailState.on_load()
