"""State for /appointment/[visit_id_param] — view and edit a single appointment."""

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


class DoctorOptionDTO(BaseModel):
    id: str
    name: str


class AppointmentDetailState(RoleState):
    """Appointment detail page — accessible to both patients and staff."""

    # ── Page state ────────────────────────────────────────────────────────────
    is_loading: bool = True
    error_message: str = ""
    success_message: str = ""
    not_found: bool = False

    # ── Visit data (view mode) ─────────────────────────────────────────────────
    visit_id: str = ""
    visit_number: str = ""
    patient_name: str = ""
    patient_id: str = ""
    scheduled_at: str = ""
    appointment_mode: str = ""
    appointment_mode_label: str = ""
    appointment_address: str = ""
    doctor_name: str = ""
    doctor_id: str = ""
    status: str = ""
    status_label: str = ""
    patient_notes: str = ""

    # ── Edit mode ─────────────────────────────────────────────────────────────
    is_editing: bool = False
    show_edit_dialog: bool = False
    edit_scheduled_at: str = ""
    edit_mode: str = ""
    edit_doctor_id: str = ""
    edit_status: str = ""
    edit_appointment_address: str = ""
    edit_notes: str = ""
    edit_error: str = ""
    is_saving: bool = False

    # ── Delete dialog ─────────────────────────────────────────────────────────
    show_delete_dialog: bool = False
    is_deleting: bool = False

    # ── Cancel dialog (patient view) ──────────────────────────────────────────
    show_cancel_dialog: bool = False
    is_cancelling: bool = False

    # ── Doctor picker ─────────────────────────────────────────────────────────
    doctor_options: list[DoctorOptionDTO] = []

    # ── Page guard + load ─────────────────────────────────────────────────────

    @rx.event
    async def on_load(self):
        await self._load_roles()
        redirect = await self._require_any_of(
            self.is_patient_user,
            self.is_operator,
            self.is_doctor,
            self.is_account_admin,
            self.is_admin,
            redirect_to="/dashboard",
        )
        if redirect:
            return redirect
        await self._load_appointment()
        await self._load_doctor_options()

    # ── Data loading ──────────────────────────────────────────────────────────

    async def _load_appointment(self):
        self.is_loading = True
        self.error_message = ""
        self.not_found = False
        try:
            with await self.authenticate_user():
                from gws_care.visit.visit import Visit

                visit_id = self.router.page.params.get("visit_id_param", "")
                if not visit_id:
                    self.not_found = True
                    return
                try:
                    visit = Visit.get_by_id(visit_id)
                except Exception:
                    self.not_found = True
                    return

                # Patients can only view their own appointments
                if self.is_patient_user and not self.is_admin:
                    if str(visit.patient_id) != self._linked_patient_id:
                        self.not_found = True
                        return

                self.visit_id = str(visit.id)
                self.visit_number = visit.visit_number or ""
                self.patient_id = str(visit.patient_id) if visit.patient_id else ""
                patient = visit.patient
                self.patient_name = patient.get_full_name() if patient else ""
                self.scheduled_at = visit.scheduled_at.isoformat() if visit.scheduled_at else ""
                mode = visit.appointment_mode
                self.appointment_mode = mode.value if mode else ""
                self.appointment_mode_label = mode.get_label() if mode else ""
                self.appointment_address = visit.appointment_address or ""
                doctor = visit.doctor if visit.doctor_id else None
                self.doctor_name = doctor.get_full_name() if doctor else ""
                self.doctor_id = str(visit.doctor_id) if visit.doctor_id else ""
                cvs = visit.consultation_visit_status
                self.status = cvs.value if cvs else ""
                self.status_label = cvs.get_label() if cvs else ""
                self.patient_notes = visit.patient_notes or ""
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_loading = False

    async def _load_doctor_options(self):
        try:
            with await self.authenticate_user():
                from gws_care.doctor.medical_doctor import MedicalDoctor

                doctors = list(
                    MedicalDoctor.select()
                    .where(MedicalDoctor.is_active == True, MedicalDoctor.is_archived == False)
                    .order_by(MedicalDoctor.last_name)
                )
                self.doctor_options = [
                    DoctorOptionDTO(id=str(d.id), name=d.get_full_name()) for d in doctors
                ]
        except Exception:
            self.doctor_options = []

    # ── Edit events ───────────────────────────────────────────────────────────

    @rx.event
    def start_edit(self):
        self.edit_scheduled_at = self.scheduled_at
        self.edit_mode = self.appointment_mode
        self.edit_doctor_id = self.doctor_id
        self.edit_status = self.status
        self.edit_appointment_address = self.appointment_address
        self.edit_notes = self.patient_notes
        self.edit_error = ""
        self.is_editing = True
        self.show_edit_dialog = True

    @rx.event
    def cancel_edit(self):
        self.is_editing = False
        self.show_edit_dialog = False
        self.edit_error = ""

    @rx.event
    def set_edit_scheduled_at(self, value: str):
        self.edit_scheduled_at = value

    @rx.event
    def set_edit_mode(self, value: str):
        self.edit_mode = value

    @rx.event
    def set_edit_doctor_id(self, value: str):
        self.edit_doctor_id = "" if value == "none" else value

    @rx.event
    def set_edit_status(self, value: str):
        self.edit_status = value

    @rx.event
    def set_edit_appointment_address(self, value: str):
        self.edit_appointment_address = value

    @rx.event
    def open_address_in_google_maps(self):
        from urllib.parse import quote

        if self.appointment_address:
            encoded = quote(self.appointment_address, safe="")
            return rx.call_script(
                f"window.open('https://www.google.com/maps/search/?api=1&query={encoded}', '_blank')"
            )

    @rx.event
    def open_edit_address_in_google_maps(self):
        from urllib.parse import quote

        if self.edit_appointment_address:
            encoded = quote(self.edit_appointment_address, safe="")
            return rx.call_script(
                f"window.open('https://www.google.com/maps/search/?api=1&query={encoded}', '_blank')"
            )

    @rx.event
    def set_edit_notes(self, value: str):
        self.edit_notes = value

    @rx.event
    async def save_edit(self):
        if not self.edit_scheduled_at:
            self.edit_error = "Please select a date and time."
            return

        self.edit_error = ""
        self.is_saving = True
        try:
            with await self.authenticate_user():
                from datetime import datetime

                from gws_care.visit.appointment_mode import AppointmentMode
                from gws_care.visit.consultation_visit_status import ConsultationVisitStatus
                from gws_care.visit.visit import Visit

                visit = Visit.get_by_id(self.visit_id)
                visit.scheduled_at = datetime.fromisoformat(self.edit_scheduled_at)
                if self.edit_mode:
                    visit.appointment_mode = AppointmentMode(self.edit_mode)
                visit.doctor_id = self.edit_doctor_id or None
                if self.edit_appointment_address:
                    visit.appointment_address = self.edit_appointment_address
                visit.patient_notes = self.edit_notes or None
                # Admin/staff can also change status
                if not self.is_patient_user and self.edit_status:
                    visit.consultation_visit_status = ConsultationVisitStatus(self.edit_status)
                visit.save()
            self.is_editing = False
            self.show_edit_dialog = False
            self.success_message = "Appointment updated."
            await self._load_appointment()
        except Exception as e:
            self.edit_error = str(e)
        finally:
            self.is_saving = False

    # ── Delete (admin/staff) ──────────────────────────────────────────────────

    @rx.event
    def open_delete_dialog(self):
        self.show_delete_dialog = True

    @rx.event
    def close_delete_dialog(self):
        self.show_delete_dialog = False

    @rx.event
    async def confirm_delete(self):
        self.is_deleting = True
        try:
            with await self.authenticate_user():
                from gws_care.visit.visit import Visit

                visit = Visit.get_by_id(self.visit_id)
                visit.delete_instance()
            return rx.redirect("/appointments")
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_deleting = False
            self.show_delete_dialog = False

    # ── Cancel (patient view) ─────────────────────────────────────────────────

    @rx.event
    def open_cancel_dialog(self):
        self.show_cancel_dialog = True

    @rx.event
    def close_cancel_dialog(self):
        self.show_cancel_dialog = False

    @rx.event
    async def confirm_cancel(self):
        self.is_cancelling = True
        try:
            with await self.authenticate_user():
                from gws_care.visit.consultation_visit_status import ConsultationVisitStatus
                from gws_care.visit.visit import Visit

                visit = Visit.get_by_id(self.visit_id)
                visit.consultation_visit_status = ConsultationVisitStatus.CANCELLED
                visit.save()
            self.show_cancel_dialog = False
            self.success_message = "Appointment cancelled."
            await self._load_appointment()
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_cancelling = False

    # ── Navigation ────────────────────────────────────────────────────────────

    @rx.event
    def go_back(self):
        return rx.call_script("window.history.back()")

    @rx.event
    def go_to_consultation(self):
        return rx.redirect(f"/consultation/{self.visit_id}")

    @rx.event
    def go_to_patient(self):
        return rx.redirect(f"/patient/{self.patient_id}")

    # ── Computed vars ─────────────────────────────────────────────────────────

    @rx.var
    def appointment_address_maps_url(self) -> str:
        if not self.appointment_address:
            return ""
        from urllib.parse import quote

        encoded = quote(self.appointment_address, safe="")
        return f"https://www.google.com/maps/search/?api=1&query={encoded}"

    @rx.var
    def can_edit(self) -> bool:
        """Only editable when still scheduled — once started, the appointment is locked."""
        return self.status == "scheduled"

    @rx.var
    def can_cancel(self) -> bool:
        return self.is_patient_user and self.status == "scheduled"

    @rx.var
    def can_delete(self) -> bool:
        return self.is_admin or self.is_operator
