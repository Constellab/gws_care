"""State for the appointment create / edit form dialog."""

from datetime import datetime, timedelta
from typing import AsyncGenerator

import reflex as rx
from gws_reflex_base import FormDialogState
from gws_reflex_main import ReflexMainState


class AppointmentFormState(FormDialogState, rx.State):
    """Manages the create / update appointment dialog."""

    # Form fields
    form_patient_id: str = ""
    form_patient_label: str = ""   # display only (read-only when opened from patient detail)
    form_account_id: str = ""
    form_scheduled_at: str = ""    # YYYY-MM-DDTHH:MM
    form_exam_type: str = "biology"
    form_notes: str = ""

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
        self.form_exam_type = value

    @rx.event
    def set_form_notes(self, value: str):
        self.form_notes = value

    @rx.event
    def set_form_patient_id(self, value: str):
        self.form_patient_id = value

    # ── Open ──────────────────────────────────────────────────────────────────

    @rx.event
    def open_create_dialog(self, patient_id: str, patient_label: str = ""):
        """Open the dialog pre-filled with a patient."""
        default_dt = (datetime.now() + timedelta(days=1)).replace(
            second=0, microsecond=0, minute=0
        )
        self.form_patient_id = patient_id
        self.form_patient_label = patient_label
        self.form_account_id = ""
        self.form_scheduled_at = default_dt.strftime("%Y-%m-%dT%H:%M")
        self.form_exam_type = "biology"
        self.form_notes = ""
        self._editing_appointment_id = ""
        self.is_update_mode = False
        self.dialog_opened = True

    @rx.event
    def open_create_dialog_standalone(self):
        """Open the dialog without a pre-selected patient (from appointments page)."""
        default_dt = (datetime.now() + timedelta(days=1)).replace(
            second=0, microsecond=0, minute=0
        )
        self.form_patient_id = ""
        self.form_patient_label = ""
        self.form_account_id = ""
        self.form_scheduled_at = default_dt.strftime("%Y-%m-%dT%H:%M")
        self.form_exam_type = "biology"
        self.form_notes = ""
        self._editing_appointment_id = ""
        self.is_update_mode = False
        # Load patient options for the selector
        try:
            from gws_care.patient.patient_service import PatientService
            patients = PatientService.search_patients()
            self.patient_options = [
                [str(p.id), f"{p.last_name} {p.first_name} ({p.patient_number})"]
                for p in patients
            ]
        except Exception:
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
        self.form_exam_type = "biology"
        self.form_notes = ""
        self.patient_options = []
        self._editing_appointment_id = ""
        self.is_update_mode = False

    async def _create(self, form_data: dict) -> AsyncGenerator:
        """Create a new appointment."""
        scheduled_at = self.form_scheduled_at
        exam_type = self.form_exam_type
        if not scheduled_at:
            yield rx.toast.error("Scheduled date/time is required.")
            return
        if not exam_type:
            yield rx.toast.error("Exam type is required.")
            return
        if not self.form_patient_id:
            yield rx.toast.error("Please select a patient.")
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
                exam_type=exam_type,
                notes=self.form_notes or None,
            )
            AppointmentService.create_appointment(dto)

        yield rx.toast.success("Appointment created")
        from .appointment_list_state import AppointmentListState
        yield AppointmentListState.on_load()

    async def _update(self, form_data: dict) -> AsyncGenerator:
        """Update an existing appointment."""
        scheduled_at = self.form_scheduled_at
        exam_type = self.form_exam_type
        if not scheduled_at:
            yield rx.toast.error("Scheduled date/time is required.")
            return
        if not exam_type:
            yield rx.toast.error("Exam type is required.")
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
                exam_type=exam_type,
                notes=self.form_notes or None,
            )
            AppointmentService.update_appointment(self._editing_appointment_id, dto)

        yield rx.toast.success("Appointment updated")
        from .appointment_list_state import AppointmentListState
        yield AppointmentListState.on_load()
