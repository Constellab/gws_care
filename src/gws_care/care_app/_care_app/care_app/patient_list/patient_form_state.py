"""State for the patient create / edit form dialog."""

from typing import AsyncGenerator

import reflex as rx
from gws_reflex_base import FormDialogState
from gws_reflex_main import ReflexMainState


class PatientFormState(FormDialogState, rx.State):
    """Manages the create / update patient dialog (demographics only).

    Doctor and account links are managed from the patient detail tabs.
    """

    form_last_name: str = ""
    form_first_name: str = ""
    form_birth_name: str = ""
    form_date_of_birth: str = ""
    form_gender: str = "M"
    form_phone: str = ""
    form_email: str = ""
    form_address: str = ""
    form_postal_code: str = ""
    form_city: str = ""
    form_social_security_number: str = ""
    form_weight: str = ""
    form_height: str = ""
    form_sex: str = ""
    form_nationality: str = ""
    form_phone_country: str = ""
    form_notif_email: bool = False
    form_notif_sms: bool = False
    form_notif_whatsapp: bool = False

    _editing_patient_id: str = ""

    # ── Setters ───────────────────────────────────────────────────────────────

    @rx.event
    def set_form_last_name(self, value: str):
        self.form_last_name = value

    @rx.event
    def set_form_first_name(self, value: str):
        self.form_first_name = value

    @rx.event
    def set_form_birth_name(self, value: str):
        self.form_birth_name = value

    @rx.event
    def set_form_date_of_birth(self, value: str):
        self.form_date_of_birth = value

    @rx.event
    def set_form_gender(self, value: str):
        self.form_gender = value

    @rx.event
    def set_form_phone(self, value: str):
        self.form_phone = value

    @rx.event
    def set_form_email(self, value: str):
        self.form_email = value

    @rx.event
    def set_form_address(self, value: str):
        self.form_address = value

    @rx.event
    def set_form_postal_code(self, value: str):
        self.form_postal_code = value

    @rx.event
    def set_form_city(self, value: str):
        self.form_city = value

    @rx.event
    def set_form_social_security_number(self, value: str):
        self.form_social_security_number = value

    @rx.event
    def set_form_weight(self, value: str):
        self.form_weight = value

    @rx.event
    def set_form_height(self, value: str):
        self.form_height = value

    @rx.event
    def set_form_sex(self, value: str):
        self.form_sex = value

    @rx.event
    def set_form_nationality(self, value: str):
        self.form_nationality = value

    @rx.event
    def set_form_phone_country(self, value: str):
        self.form_phone_country = value

    @rx.event
    def set_form_notif_email(self, value: bool):
        self.form_notif_email = value

    @rx.event
    def set_form_notif_sms(self, value: bool):
        self.form_notif_sms = value

    @rx.event
    def set_form_notif_whatsapp(self, value: bool):
        self.form_notif_whatsapp = value

    # ── Dialog lifecycle ──────────────────────────────────────────────────────

    @rx.event
    async def open_create_dialog(self):
        self.is_update_mode = False
        self._editing_patient_id = ""
        await self._clear_form_state()
        self.dialog_opened = True

    @rx.event
    async def open_edit_dialog(self, patient_id: str):
        self.is_update_mode = True
        self._editing_patient_id = patient_id
        _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            from gws_care.patient.patient_service import PatientService
            p = PatientService.get_patient(patient_id)
            self.form_last_name = p.last_name or ""
            self.form_first_name = p.first_name or ""
            self.form_birth_name = p.birth_name or ""
            self.form_date_of_birth = p.date_of_birth.isoformat() if p.date_of_birth else ""
            self.form_gender = p.gender or "M"
            self.form_phone = p.phone or ""
            self.form_email = p.email or ""
            self.form_address = p.address or ""
            self.form_postal_code = p.postal_code or ""
            self.form_city = p.city or ""
            self.form_social_security_number = p.social_security_number or ""
            self.form_weight = str(p.weight) if p.weight is not None else ""
            self.form_height = str(p.height) if p.height is not None else ""
            self.form_sex = p.sex or ""
            self.form_nationality = p.nationality or ""
            self.form_phone_country = p.phone_country or ""
            notif = p.notification_preferences or {}
            if isinstance(notif, str):
                import json as _json
                try:
                    notif = _json.loads(notif)
                except Exception:
                    notif = {}
            self.form_notif_email = bool(notif.get("email", False))
            self.form_notif_sms = bool(notif.get("sms", False))
            self.form_notif_whatsapp = bool(notif.get("whatsapp", False))
        self.dialog_opened = True

    # ── FormDialogState abstract method implementations ───────────────────────

    async def _clear_form_state(self) -> None:
        self.form_last_name = ""
        self.form_first_name = ""
        self.form_birth_name = ""
        self.form_date_of_birth = ""
        self.form_gender = "M"
        self.form_phone = ""
        self.form_email = ""
        self.form_address = ""
        self.form_postal_code = ""
        self.form_city = ""
        self.form_social_security_number = ""
        self.form_weight = ""
        self.form_height = ""
        self.form_sex = ""
        self.form_nationality = ""
        self.form_phone_country = ""
        self.form_notif_email = False
        self.form_notif_sms = False
        self.form_notif_whatsapp = False
        self._editing_patient_id = ""
        self.is_update_mode = False

    async def _create(self, form_data: dict) -> AsyncGenerator:
        from datetime import date as date_type
        from gws_care.patient.patient_dto import SavePatientDTO
        from gws_care.patient.patient_service import PatientService

        last_name = self.form_last_name.strip()
        first_name = self.form_first_name.strip()
        if not last_name:
            yield rx.toast.error("Last name is required")
            return
        if not first_name:
            yield rx.toast.error("First name is required")
            return
        if not self.form_date_of_birth:
            yield rx.toast.error("Date of birth is required")
            return

        dto = SavePatientDTO(
            last_name=last_name,
            first_name=first_name,
            birth_name=self.form_birth_name or None,
            date_of_birth=date_type.fromisoformat(self.form_date_of_birth),
            gender=self.form_gender,
            phone=self.form_phone or None,
            email=self.form_email or None,
            address=self.form_address or None,
            postal_code=self.form_postal_code or None,
            city=self.form_city or None,
            social_security_number=self.form_social_security_number or None,
            weight=float(self.form_weight) if self.form_weight.strip() else None,
            height=float(self.form_height) if self.form_height.strip() else None,
            sex=self.form_sex or None,
            nationality=self.form_nationality or None,
            phone_country=self.form_phone_country or None,
        )

        async with self:
            _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            patient = PatientService.create_patient(dto)

        yield rx.toast.success(f"Patient {patient.patient_number} created")
        from ..patient_list.patient_list_state import PatientListState
        yield PatientListState.on_load()

    async def _update(self, form_data: dict) -> AsyncGenerator:
        from datetime import date as date_type
        from gws_care.patient.patient_dto import SavePatientDTO
        from gws_care.patient.patient_service import PatientService

        last_name = self.form_last_name.strip()
        first_name = self.form_first_name.strip()
        if not last_name:
            yield rx.toast.error("Last name is required")
            return
        if not first_name:
            yield rx.toast.error("First name is required")
            return
        if not self.form_date_of_birth:
            yield rx.toast.error("Date of birth is required")
            return

        dto = SavePatientDTO(
            last_name=last_name,
            first_name=first_name,
            birth_name=self.form_birth_name or None,
            date_of_birth=date_type.fromisoformat(self.form_date_of_birth),
            gender=self.form_gender,
            phone=self.form_phone or None,
            email=self.form_email or None,
            address=self.form_address or None,
            postal_code=self.form_postal_code or None,
            city=self.form_city or None,
            social_security_number=self.form_social_security_number or None,
            weight=float(self.form_weight) if self.form_weight.strip() else None,
            height=float(self.form_height) if self.form_height.strip() else None,
            sex=self.form_sex or None,
            nationality=self.form_nationality or None,
            phone_country=self.form_phone_country or None,
            notification_preferences={
                "email": self.form_notif_email,
                "sms": self.form_notif_sms,
                "whatsapp": self.form_notif_whatsapp,
            },
        )

        async with self:
            _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            PatientService.update_patient(self._editing_patient_id, dto)

        yield rx.toast.success("Patient updated successfully")
        from ..patient_detail.patient_detail_state import PatientDetailState
        yield PatientDetailState.on_load()
