"""State for the Medical Doctors admin page."""

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


class DoctorRowDTO(BaseModel):
    id: str
    full_name: str
    specialization: str = ""
    phone: str = ""
    email: str = ""
    rpps_number: str = ""
    address: str = ""
    is_active: bool = True


class DoctorListState(RoleState):

    doctors: list[DoctorRowDTO] = []
    is_loading: bool = False
    error_message: str = ""

    # ── Dialog ────────────────────────────────────────────────────────────────
    show_form_dialog: bool = False
    is_edit_mode: bool = False
    _editing_doctor_id: str = ""

    form_first_name: str = ""
    form_last_name: str = ""
    form_specialization: str = ""
    form_phone_dial_code: str = "+33"
    form_phone: str = ""
    form_email: str = ""
    form_rpps: str = ""
    form_address: str = ""
    form_error: str = ""
    form_is_saving: bool = False

    @rx.event
    async def on_load(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_admin)
        if redirect:
            return redirect
        await self._load_doctors()

    @rx.event
    async def open_create_dialog(self):
        self.is_edit_mode = False
        self._editing_doctor_id = ""
        self._reset_form()
        self.show_form_dialog = True

    @rx.event
    async def open_edit_dialog(self, doctor_id: str):
        self.is_edit_mode = True
        self._editing_doctor_id = doctor_id
        self._reset_form()
        try:
            with await self.authenticate_user():
                from gws_care.doctor.medical_doctor_service import MedicalDoctorService
                d = MedicalDoctorService.get_doctor(doctor_id)
                self.form_first_name = d.first_name
                self.form_last_name = d.last_name
                self.form_specialization = d.specialization or ""
                self.form_phone = d.phone or ""
                self.form_email = d.email or ""
                self.form_rpps = d.rpps_number or ""
                self.form_address = d.address or ""
        except Exception as e:
            self.form_error = str(e)
        self.show_form_dialog = True

    @rx.event
    def close_form_dialog(self):
        self.show_form_dialog = False

    @rx.event
    def set_form_first_name(self, value: str):
        self.form_first_name = value

    @rx.event
    def set_form_last_name(self, value: str):
        self.form_last_name = value

    @rx.event
    def set_form_specialization(self, value: str):
        self.form_specialization = value

    @rx.event
    def set_form_phone_dial_code(self, value: str):
        self.form_phone_dial_code = value

    @rx.event
    def set_form_phone(self, value: str):
        self.form_phone = value

    @rx.event
    def set_form_email(self, value: str):
        self.form_email = value

    @rx.event
    def set_form_rpps(self, value: str):
        self.form_rpps = value

    @rx.event
    def set_form_address(self, value: str):
        self.form_address = value

    @rx.event
    async def save_doctor(self):
        first = self.form_first_name.strip()
        last = self.form_last_name.strip()
        if not first or not last:
            self.form_error = "Le prénom et le nom sont obligatoires."
            return
        self.form_error = ""
        self.form_is_saving = True
        try:
            with await self.authenticate_user():
                from gws_care.doctor.medical_doctor_dto import SaveMedicalDoctorDTO
                from gws_care.doctor.medical_doctor_service import MedicalDoctorService
                dto = SaveMedicalDoctorDTO(
                    first_name=first,
                    last_name=last,
                    specialization=self.form_specialization or None,
                    phone=self.form_phone or None,
                    email=self.form_email or None,
                    rpps_number=self.form_rpps or None,
                    address=self.form_address or None,
                )
                if self.is_edit_mode:
                    MedicalDoctorService.update_doctor(self._editing_doctor_id, dto)
                else:
                    MedicalDoctorService.create_doctor(dto)
            self.show_form_dialog = False
            await self._load_doctors()
        except Exception as e:
            self.form_error = str(e)
        finally:
            self.form_is_saving = False

    @rx.event
    async def deactivate_doctor(self, doctor_id: str):
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.doctor.medical_doctor_service import MedicalDoctorService
                MedicalDoctorService.deactivate_doctor(doctor_id)
            await self._load_doctors()
        except Exception as e:
            self.error_message = str(e)

    def _reset_form(self):
        self.form_first_name = ""
        self.form_last_name = ""
        self.form_specialization = ""
        self.form_phone_dial_code = "+33"
        self.form_phone = ""
        self.form_email = ""
        self.form_rpps = ""
        self.form_address = ""
        self.form_error = ""
        self.form_is_saving = False

    async def _load_doctors(self):
        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.doctor.medical_doctor_service import MedicalDoctorService
                docs = MedicalDoctorService.list_doctors(active_only=False)
                self.doctors = [
                    DoctorRowDTO(
                        id=d.id,
                        full_name=d.full_name,
                        specialization=d.specialization or "",
                        phone=d.phone or "",
                        email=d.email or "",
                        rpps_number=d.rpps_number or "",
                        address=d.address or "",
                        is_active=d.is_active,
                    )
                    for d in docs
                ]
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_loading = False
