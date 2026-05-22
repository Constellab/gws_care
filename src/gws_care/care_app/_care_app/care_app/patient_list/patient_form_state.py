"""State for the patient create / edit form dialog."""

from typing import AsyncGenerator

import reflex as rx
from gws_reflex_base import FormDialogState
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class AccountPickerRowDTO(BaseModel):
    """Lightweight account row for the account picker table in the patient form."""

    id: str
    name: str
    account_type: str = ""
    city: str | None = None


class DoctorPickerRowDTO(BaseModel):
    id: str
    full_name: str
    specialization: str = ""

class PatientFormState(FormDialogState, rx.State):
    """Manages the create / update patient dialog.

    Inherits `FormDialogState` for dialog lifecycle and `submit_form` dispatch.
    """

    # Form fields (public — bound to inputs in the UI)
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
    form_primary_physician_name: str = ""
    form_primary_physician_phone: str = ""
    form_physician_id: str = ""
    form_physician_name: str = ""  # display label shown on the picker button

    # Doctor picker
    doc_picker_is_open: bool = False
    doc_picker_filter: str = ""
    doc_picker_rows: list[DoctorPickerRowDTO] = []
    doc_picker_is_loading: bool = False
    doc_picker_error: str = ""

    # New optional fields
    form_social_security_number: str = ""
    form_weight: str = ""  # stored as string; converted to float on save
    form_height: str = ""  # stored as string; converted to float on save
    form_sex: str = ""  # "M", "F", "Autre" or ""
    form_notif_email: bool = False
    form_notif_sms: bool = False
    form_notif_whatsapp: bool = False

    # Account assignment (inline picker)
    form_account_id: str = ""
    form_account_name: str = ""        # display label shown on the picker button
    acct_picker_is_open: bool = False
    acct_picker_filter: str = ""
    acct_picker_accounts: list[AccountPickerRowDTO] = []
    acct_picker_is_loading: bool = False
    acct_picker_error: str = ""

    # Set when editing an existing patient
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
    def set_form_primary_physician_name(self, value: str):
        self.form_primary_physician_name = value

    @rx.event
    def set_form_primary_physician_phone(self, value: str):
        self.form_primary_physician_phone = value

    # ── Doctor picker ───────────────────────────────────────────────────────

    @rx.event
    async def open_doctor_picker(self):
        self.doc_picker_filter = ""
        self.doc_picker_error = ""
        self.doc_picker_is_open = True
        await self._run_doc_search()

    @rx.event
    def close_doctor_picker(self):
        self.doc_picker_is_open = False

    @rx.event
    async def doc_picker_set_filter(self, value: str):
        self.doc_picker_filter = value
        await self._run_doc_search()

    @rx.event
    def doc_picker_confirm(self, doctor_id: str, name: str):
        self.form_physician_id = doctor_id
        self.form_physician_name = name
        self.doc_picker_is_open = False

    @rx.event
    def doc_picker_clear(self):
        self.form_physician_id = ""
        self.form_physician_name = ""

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
    def set_form_notif_email(self, value: bool):
        self.form_notif_email = value

    @rx.event
    def set_form_notif_sms(self, value: bool):
        self.form_notif_sms = value

    @rx.event
    def set_form_notif_whatsapp(self, value: bool):
        self.form_notif_whatsapp = value

    @rx.event
    def set_form_account_id(self, value: str):
        self.form_account_id = "" if value == "__none__" else value

    # ── Account picker ─────────────────────────────────────────────────────

    @rx.event
    async def open_account_picker(self):
        self.acct_picker_filter = ""
        self.acct_picker_error = ""
        self.acct_picker_is_open = True
        await self._run_acct_search()

    @rx.event
    def close_account_picker(self):
        self.acct_picker_is_open = False

    @rx.event
    async def acct_picker_set_filter(self, value: str):
        self.acct_picker_filter = value
        await self._run_acct_search()

    @rx.event
    def acct_picker_confirm(self, account_id: str, name: str):
        """Select an account and close the picker."""
        self.form_account_id = account_id
        self.form_account_name = name
        self.acct_picker_is_open = False

    @rx.event
    def acct_picker_clear(self):
        """Clear the current account selection."""
        self.form_account_id = ""
        self.form_account_name = ""

    async def _run_acct_search(self) -> None:
        self.acct_picker_is_loading = True
        self.acct_picker_error = ""
        try:
            _main = await self.get_state(ReflexMainState)
            with await _main.authenticate_user():
                from gws_care.account.account_service import AccountService
                accounts = AccountService.list_accounts(active_only=False)
                name_filter = self.acct_picker_filter.strip().lower()
                if name_filter:
                    accounts = [a for a in accounts if name_filter in a.name.lower()]
                self.acct_picker_accounts = [
                    AccountPickerRowDTO(
                        id=str(a.id),
                        name=a.name,
                        account_type=a.account_type or "",
                        city=a.city,
                    )
                    for a in accounts
                ]
        except Exception as e:
            self.acct_picker_error = str(e)
        finally:
            self.acct_picker_is_loading = False


    async def _run_doc_search(self) -> None:
        self.doc_picker_is_loading = True
        self.doc_picker_error = ""
        try:
            _main = await self.get_state(ReflexMainState)
            with await _main.authenticate_user():
                from gws_care.doctor.medical_doctor_service import MedicalDoctorService
                doctors = MedicalDoctorService.list_doctors(active_only=True)
                name_filter = self.doc_picker_filter.strip().lower()
                if name_filter:
                    doctors = [d for d in doctors if name_filter in d.full_name.lower()
                               or name_filter in (d.specialization or "").lower()]
                self.doc_picker_rows = [
                    DoctorPickerRowDTO(
                        id=d.id,
                        full_name=d.full_name,
                        specialization=d.specialization or "",
                    )
                    for d in doctors
                ]
        except Exception as e:
            self.doc_picker_error = str(e)
        finally:
            self.doc_picker_is_loading = False

    @rx.event
    async def open_create_dialog(self):
        """Open the dialog in create mode with blank fields."""
        self.is_update_mode = False
        self._editing_patient_id = ""
        await self._clear_form_state()
        self.dialog_opened = True

    @rx.event
    async def open_create_for_account(self, account_id: str):
        """Open the create dialog pre-linked to an account."""
        self.is_update_mode = False
        self._editing_patient_id = ""
        await self._clear_form_state()
        # pre-populate account (look up name from DB for display label)
        self.form_account_id = account_id
        try:
            _main = await self.get_state(ReflexMainState)
            with await _main.authenticate_user():
                from gws_care.account.account_service import AccountService
                acc = AccountService.get_account(account_id)
                self.form_account_name = acc.name
        except Exception:
            self.form_account_name = ""
        self.dialog_opened = True

    @rx.event
    async def open_edit_dialog(self, patient_id: str):
        """Open the dialog in edit mode pre-filled with the patient's data.

        :param patient_id: DB id of the patient to edit
        :type patient_id: str
        """
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
            self.form_primary_physician_name = p.primary_physician_name or ""
            self.form_primary_physician_phone = p.primary_physician_phone or ""
            self.form_physician_id = str(p.primary_physician_id) if p.primary_physician_id else ""
            from gws_care.patient.patient_account import PatientAccount
            first_link = PatientAccount.select().where(PatientAccount.patient == patient_id).first()
            self.form_account_id = str(first_link.account_id) if first_link else ""
            self.form_social_security_number = p.social_security_number or ""
            self.form_weight = str(p.weight) if p.weight is not None else ""
            self.form_height = str(p.height) if p.height is not None else ""
            self.form_sex = p.sex or ""
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

        # Resolve the account display name for the picker button
        if self.form_account_id:
            try:
                _main2 = await self.get_state(ReflexMainState)
                with await _main2.authenticate_user():
                    from gws_care.account.account_service import AccountService
                    acc = AccountService.get_account(self.form_account_id)
                    self.form_account_name = acc.name
            except Exception:
                self.form_account_name = ""
        else:
            self.form_account_name = ""

        # Resolve the doctor display name for the picker button
        if self.form_physician_id:
            try:
                _main3 = await self.get_state(ReflexMainState)
                with await _main3.authenticate_user():
                    from gws_care.doctor.medical_doctor_service import MedicalDoctorService
                    doc = MedicalDoctorService.get_doctor(self.form_physician_id)
                    self.form_physician_name = doc.full_name
            except Exception:
                self.form_physician_name = ""
        else:
            self.form_physician_name = ""

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
        self.form_primary_physician_name = ""
        self.form_primary_physician_phone = ""
        self.form_physician_id = ""
        self._editing_patient_id = ""
        self.is_update_mode = False
        self.form_social_security_number = ""
        self.form_weight = ""
        self.form_height = ""
        self.form_sex = ""
        self.form_notif_email = False
        self.form_notif_sms = False
        self.form_notif_whatsapp = False
        self.form_account_id = ""
        self.form_account_name = ""
        self.acct_picker_is_open = False
        self.acct_picker_filter = ""
        self.acct_picker_accounts = []
        self.acct_picker_error = ""
        self.form_physician_name = ""
        self.doc_picker_is_open = False
        self.doc_picker_filter = ""
        self.doc_picker_rows = []
        self.doc_picker_error = ""

    async def _create(self, form_data: dict) -> AsyncGenerator:
        """Create a new patient from form data."""
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
            primary_physician_name=None,
            primary_physician_phone=None,
            primary_physician_id=self.form_physician_id or None,
            account_id=self.form_account_id or None,
            social_security_number=self.form_social_security_number or None,
            weight=float(self.form_weight) if self.form_weight.strip() else None,
            height=float(self.form_height) if self.form_height.strip() else None,
            sex=self.form_sex or None,
        )

        async with self:
            _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            patient = PatientService.create_patient(dto)

        yield rx.toast.success(f"Patient {patient.patient_number} created")

        if self.form_account_id:
            from ..account_detail.account_detail_state import AccountDetailState
            yield AccountDetailState.on_load()
        else:
            from ..patient_list.patient_list_state import PatientListState
            yield PatientListState.on_load()

    async def _update(self, form_data: dict) -> AsyncGenerator:
        """Update an existing patient from form data."""
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
            primary_physician_name=None,
            primary_physician_phone=None,
            primary_physician_id=self.form_physician_id or None,
            account_id=self.form_account_id or None,
            social_security_number=self.form_social_security_number or None,
            weight=float(self.form_weight) if self.form_weight.strip() else None,
            height=float(self.form_height) if self.form_height.strip() else None,
            sex=self.form_sex or None,
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
