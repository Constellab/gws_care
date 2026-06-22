"""State for the Doctors tab on the patient detail page."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class LinkedDoctorRowDTO(BaseModel):
    doctor_id: str
    full_name: str = ""
    specialization: str = ""
    phone: str = ""
    email: str = ""
    is_referent: bool = False


class DoctorPickerRowDTO(BaseModel):
    id: str
    full_name: str = ""
    specialization: str = ""


class PatientDoctorTabState(rx.State):
    """Manages the Doctors tab: list linked doctors, link/unlink, set referent."""

    linked_doctors: list[LinkedDoctorRowDTO] = []
    is_loading: bool = False
    error_message: str = ""

    # Doctor picker (for linking a new doctor)
    picker_open: bool = False
    picker_filter: str = ""
    picker_rows: list[DoctorPickerRowDTO] = []
    picker_is_loading: bool = False
    picker_error: str = ""

    # Unlink confirmation dialog
    confirm_unlink_open: bool = False
    confirm_unlink_doctor_id: str = ""
    confirm_unlink_doctor_name: str = ""

    # Remove referent confirmation dialog
    confirm_clear_referent_open: bool = False
    confirm_clear_referent_doctor_id: str = ""
    confirm_clear_referent_doctor_name: str = ""

    _patient_id: str = ""

    # ── Load ─────────────────────────────────────────────────────────────────

    @rx.event
    async def load(self, patient_id: str):
        self._patient_id = patient_id
        await self._load_linked()

    # ── Picker ────────────────────────────────────────────────────────────────

    @rx.event
    async def open_picker(self):
        self.picker_filter = ""
        self.picker_error = ""
        self.picker_open = True
        await self._run_picker_search()

    @rx.event
    def close_picker(self):
        self.picker_open = False

    @rx.event
    async def set_picker_filter(self, value: str):
        self.picker_filter = value
        await self._run_picker_search()

    @rx.event
    async def link_doctor(self, doctor_id: str):
        self.picker_open = False
        try:
            _main = await self.get_state(ReflexMainState)
            with await _main.authenticate_user():
                from gws_care.patient.patient_doctor_service import PatientDoctorService
                PatientDoctorService.link_doctor(self._patient_id, doctor_id)
            await self._load_linked()
        except Exception as e:
            self.error_message = str(e)

    @rx.event
    def open_confirm_unlink(self, doctor_id: str, doctor_name: str):
        self.confirm_unlink_doctor_id = doctor_id
        self.confirm_unlink_doctor_name = doctor_name
        self.confirm_unlink_open = True

    @rx.event
    def close_confirm_unlink(self):
        self.confirm_unlink_open = False
        self.confirm_unlink_doctor_id = ""
        self.confirm_unlink_doctor_name = ""

    @rx.event
    async def unlink_doctor(self, doctor_id: str):
        self.confirm_unlink_open = False
        try:
            _main = await self.get_state(ReflexMainState)
            with await _main.authenticate_user():
                from gws_care.patient.patient_doctor_service import PatientDoctorService
                PatientDoctorService.unlink_doctor(self._patient_id, doctor_id)
            await self._load_linked()
        except Exception as e:
            self.error_message = str(e)

    @rx.event
    def open_confirm_clear_referent(self, doctor_id: str, doctor_name: str):
        self.confirm_clear_referent_doctor_id = doctor_id
        self.confirm_clear_referent_doctor_name = doctor_name
        self.confirm_clear_referent_open = True

    @rx.event
    def close_confirm_clear_referent(self):
        self.confirm_clear_referent_open = False
        self.confirm_clear_referent_doctor_id = ""
        self.confirm_clear_referent_doctor_name = ""

    @rx.event
    async def set_referent(self, doctor_id: str):
        try:
            _main = await self.get_state(ReflexMainState)
            with await _main.authenticate_user():
                from gws_care.patient.patient_doctor_service import PatientDoctorService
                PatientDoctorService.set_referent(self._patient_id, doctor_id)
            await self._load_linked()
        except Exception as e:
            self.error_message = str(e)

    @rx.event
    async def clear_referent(self, doctor_id: str):
        self.confirm_clear_referent_open = False
        try:
            _main = await self.get_state(ReflexMainState)
            with await _main.authenticate_user():
                from gws_care.patient.patient_doctor_service import PatientDoctorService
                PatientDoctorService.clear_referent(self._patient_id)
            await self._load_linked()
        except Exception as e:
            self.error_message = str(e)

    # ── Internal loaders ─────────────────────────────────────────────────────

    async def _load_linked(self):
        if not self._patient_id:
            self.linked_doctors = []
            return
        self.is_loading = True
        self.error_message = ""
        try:
            _main = await self.get_state(ReflexMainState)
            with await _main.authenticate_user():
                from gws_care.patient.patient_doctor_service import PatientDoctorService
                rows = PatientDoctorService.get_linked_doctors(self._patient_id)
                self.linked_doctors = [
                    LinkedDoctorRowDTO(
                        doctor_id=str(r.doctor_id),
                        full_name=r.doctor.get_full_name(),
                        specialization=r.doctor.specialization or "",
                        phone=r.doctor.phone or "",
                        email=r.doctor.email or "",
                        is_referent=bool(r.is_referent),
                    )
                    for r in rows
                ]
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_loading = False

    async def _run_picker_search(self):
        self.picker_is_loading = True
        self.picker_error = ""
        already_linked = {d.doctor_id for d in self.linked_doctors}
        try:
            _main = await self.get_state(ReflexMainState)
            with await _main.authenticate_user():
                from gws_care.doctor.medical_doctor_service import MedicalDoctorService
                doctors = MedicalDoctorService.list_doctors(active_only=True)
                f = self.picker_filter.strip().lower()
                self.picker_rows = [
                    DoctorPickerRowDTO(
                        id=d.id,
                        full_name=d.full_name,
                        specialization=d.specialization or "",
                    )
                    for d in doctors
                    if d.id not in already_linked
                    and (not f or f in d.full_name.lower() or f in (d.specialization or "").lower())
                ]
        except Exception as e:
            self.picker_error = str(e)
        finally:
            self.picker_is_loading = False
