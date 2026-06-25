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
    is_archived: bool = False
    status_reason: str = ""


class DoctorListState(RoleState):

    doctors: list[DoctorRowDTO] = []
    is_loading: bool = False
    error_message: str = ""

    # ── Create/edit dialog ────────────────────────────────────────────────────
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
    specialty_suggestions: list[str] = []
    show_specialty_suggestions: bool = False

    # ── Action confirmation dialog (deactivate / archive / delete / reactivate)
    show_action_confirm: bool = False
    _action_type: str = ""          # "deactivate" | "reactivate" | "archive" | "delete"
    _action_doctor_id: str = ""
    action_confirm_title: str = ""
    action_confirm_desc: str = ""
    action_confirm_btn_label: str = ""
    action_confirm_is_red: bool = False
    action_confirm_show_reason: bool = False
    action_reason: str = ""
    action_is_saving: bool = False

    @rx.var
    def filtered_specialty_suggestions(self) -> list[str]:
        q = self.form_specialization.strip().lower()
        if not q:
            return self.specialty_suggestions
        return [s for s in self.specialty_suggestions if q in s.lower()]

    @rx.event
    async def on_load(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_admin)
        if redirect:
            return redirect
        await self._load_doctors()

    # ── Create / edit ─────────────────────────────────────────────────────────

    @rx.event
    async def open_create_dialog(self):
        self.is_edit_mode = False
        self._editing_doctor_id = ""
        self._reset_form()
        self._load_specialty_suggestions()
        self.show_form_dialog = True

    @rx.event
    async def open_edit_dialog(self, doctor_id: str):
        self.is_edit_mode = True
        self._editing_doctor_id = doctor_id
        self._reset_form()
        self._load_specialty_suggestions()
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
        self.show_specialty_suggestions = bool(self.specialty_suggestions)

    @rx.event
    def focus_specialty_input(self):
        """Show all suggestions on field focus."""
        self.show_specialty_suggestions = bool(self.specialty_suggestions)

    @rx.event
    def pick_specialty_suggestion(self, value: str):
        self.form_specialization = value
        self.show_specialty_suggestions = False

    @rx.event
    def hide_specialty_suggestions(self):
        self.show_specialty_suggestions = False

    def _load_specialty_suggestions(self):
        try:
            from gws_care.doctor.medical_doctor_service import MedicalDoctorService
            self.specialty_suggestions = MedicalDoctorService.get_specializations()
        except Exception:
            self.specialty_suggestions = []

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

    # ── Action confirmation dialog ────────────────────────────────────────────

    @rx.event
    def open_action_confirm(self, doctor_id: str, doctor_name: str, action_type: str):
        self._action_type = action_type
        self._action_doctor_id = doctor_id
        self.action_reason = ""
        if action_type == "deactivate":
            self.action_confirm_title = f"Désactiver {doctor_name}"
            self.action_confirm_desc = "Ce médecin ne sera plus proposé aux patients ni aux campagnes. Veuillez indiquer le motif."
            self.action_confirm_btn_label = "Désactiver"
            self.action_confirm_is_red = False
            self.action_confirm_show_reason = True
        elif action_type == "reactivate":
            self.action_confirm_title = f"Réactiver {doctor_name}"
            self.action_confirm_desc = "Ce médecin sera à nouveau disponible pour les patients et les campagnes."
            self.action_confirm_btn_label = "Réactiver"
            self.action_confirm_is_red = False
            self.action_confirm_show_reason = False
        elif action_type == "archive":
            self.action_confirm_title = f"Archiver {doctor_name}"
            self.action_confirm_desc = "Ce médecin sera archivé et ne sera plus disponible. Veuillez indiquer le motif."
            self.action_confirm_btn_label = "Archiver"
            self.action_confirm_is_red = False
            self.action_confirm_show_reason = True
        elif action_type == "delete":
            self.action_confirm_title = f"Supprimer {doctor_name}"
            self.action_confirm_desc = "Cette action est irréversible. Le médecin sera définitivement supprimé du système."
            self.action_confirm_btn_label = "Supprimer définitivement"
            self.action_confirm_is_red = True
            self.action_confirm_show_reason = True
        self.show_action_confirm = True

    @rx.event
    def close_action_confirm(self):
        self.show_action_confirm = False
        self._action_type = ""
        self._action_doctor_id = ""
        self.action_reason = ""

    @rx.event
    def set_action_reason(self, value: str):
        self.action_reason = value

    @rx.event
    async def confirm_action(self):
        reason = self.action_reason.strip()
        if self.action_confirm_show_reason and not reason:
            return rx.toast.error("Le motif est obligatoire.")
        self.action_is_saving = True
        self.show_action_confirm = False
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.doctor.medical_doctor_service import MedicalDoctorService
                if self._action_type == "deactivate":
                    MedicalDoctorService.deactivate_doctor(self._action_doctor_id, reason)
                elif self._action_type == "reactivate":
                    MedicalDoctorService.reactivate_doctor(self._action_doctor_id)
                elif self._action_type == "archive":
                    MedicalDoctorService.archive_doctor(self._action_doctor_id, reason)
                elif self._action_type == "delete":
                    MedicalDoctorService.delete_doctor(self._action_doctor_id)
            self._action_type = ""
            self._action_doctor_id = ""
            self.action_reason = ""
            await self._load_doctors()
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.action_is_saving = False

    # ── Helpers ───────────────────────────────────────────────────────────────

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
        self.show_specialty_suggestions = False

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
                        is_archived=d.is_archived,
                        status_reason=d.status_reason or "",
                    )
                    for d in docs
                ]
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_loading = False
