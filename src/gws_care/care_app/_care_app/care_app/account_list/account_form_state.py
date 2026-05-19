"""State for the account create / edit form dialog."""

from typing import AsyncGenerator

import reflex as rx
from gws_reflex_base import FormDialogState
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class PatientFillOption(BaseModel):
    id: str
    display: str        # "First Last"
    patient_number: str = ""
    date_of_birth: str = ""
    gender: str = ""


class AccountFormState(FormDialogState, rx.State):
    """Manages the create / update account dialog."""

    # Account type: "COMPANY" or "INDIVIDUAL"
    form_account_type: str = "COMPANY"

    # Form fields (public — bound to inputs in the UI)
    form_name: str = ""
    form_registration_number: str = ""
    form_address: str = ""
    form_postal_code: str = ""
    form_city: str = ""
    form_phone: str = ""
    form_email: str = ""
    form_contact_name: str = ""

    # Fill-from-patient
    patient_fill_options: list[PatientFillOption] = []
    selected_patient_fill: str = ""
    patient_fill_selected_label: str = ""
    patient_fill_filter_name: str = ""
    patient_fill_filter_number: str = ""
    patient_fill_is_loading: bool = False

    # Set when editing an existing account
    _editing_account_id: str = ""

    # ── Setters ───────────────────────────────────────────────────────────────

    @rx.event
    def set_form_account_type(self, value: str):
        self.form_account_type = value

    @rx.event
    def set_form_name(self, value: str):
        self.form_name = value

    @rx.event
    def set_form_registration_number(self, value: str):
        self.form_registration_number = value

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
    def set_form_phone(self, value: str):
        self.form_phone = value

    @rx.event
    def set_form_email(self, value: str):
        self.form_email = value

    @rx.event
    def set_form_contact_name(self, value: str):
        self.form_contact_name = value

    @rx.event
    def select_patient_fill(self, patient_id: str, label: str):
        """Select a patient from the table and pre-fill the form with their contact details."""
        self.selected_patient_fill = patient_id
        self.patient_fill_selected_label = label
        if not patient_id:
            return
        try:
            from gws_care.patient.patient_service import PatientService
            patient = PatientService.get_patient(patient_id)
            self.form_name = patient.get_full_name()
            self.form_address = patient.address or ""
            self.form_postal_code = patient.postal_code or ""
            self.form_city = patient.city or ""
            self.form_phone = patient.phone or ""
            self.form_email = patient.email or ""
        except Exception:
            pass

    @rx.event
    async def set_patient_fill_filter_name(self, value: str):
        self.patient_fill_filter_name = value
        await self._load_patient_fill_options()

    @rx.event
    async def set_patient_fill_filter_number(self, value: str):
        self.patient_fill_filter_number = value
        await self._load_patient_fill_options()

    @rx.event
    async def clear_patient_fill_filters(self):
        self.patient_fill_filter_name = ""
        self.patient_fill_filter_number = ""
        await self._load_patient_fill_options()

    async def _load_patient_fill_options(self) -> None:
        """Load patients into the fill selector, applying current filters."""
        self.patient_fill_is_loading = True
        try:
            from gws_care.patient.patient_service import PatientService
            name_term = self.patient_fill_filter_name.strip() or None
            raw_pn = self.patient_fill_filter_number.strip()
            if raw_pn.upper().startswith("PAT-"):
                raw_pn = raw_pn[4:]
            pn_prefix = f"PAT-{raw_pn}" if raw_pn else None
            patients = PatientService.search_patients(
                search=name_term,
                patient_number_prefix=pn_prefix,
                limit=50,
            )
            self.patient_fill_options = [
                PatientFillOption(
                    id=str(p.id),
                    display=p.get_full_name(),
                    patient_number=p.patient_number,
                    date_of_birth=p.date_of_birth.isoformat() if p.date_of_birth else "",
                    gender=p.gender or "",
                )
                for p in patients
            ]
        except Exception:
            pass
        finally:
            self.patient_fill_is_loading = False

    # ── Dialog open helpers ───────────────────────────────────────────────────

    @rx.event
    async def open_create_dialog(self):
        """Open the dialog in create mode."""
        self.is_update_mode = False
        self._editing_account_id = ""
        await self._clear_form_state()
        await self._load_patient_fill_options()
        self.dialog_opened = True

    @rx.event
    async def open_edit_dialog(self, account_id: str):
        """Open the dialog in edit mode pre-filled with the account's data."""
        self.is_update_mode = True
        self._editing_account_id = account_id

        _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            from gws_care.account.account_service import AccountService
            a = AccountService.get_account(account_id)
            self.form_account_type = a.account_type or "COMPANY"
            self.form_name = a.name or ""
            self.form_registration_number = a.registration_number or ""
            self.form_address = a.address or ""
            self.form_postal_code = a.postal_code or ""
            self.form_city = a.city or ""
            self.form_phone = a.phone or ""
            self.form_email = a.email or ""
            self.form_contact_name = a.contact_name or ""

        await self._load_patient_fill_options()
        self.dialog_opened = True

    # ── FormDialogState abstract method implementations ───────────────────────

    async def _clear_form_state(self) -> None:
        self.form_account_type = "COMPANY"
        self.form_name = ""
        self.form_registration_number = ""
        self.form_address = ""
        self.form_postal_code = ""
        self.form_city = ""
        self.form_phone = ""
        self.form_email = ""
        self.form_contact_name = ""
        self.selected_patient_fill = ""
        self.patient_fill_selected_label = ""
        self.patient_fill_filter_name = ""
        self.patient_fill_filter_number = ""
        self._editing_account_id = ""
        self.is_update_mode = False

    def _build_save_dto(self):
        from gws_care.account.account_dto import SaveAccountDTO
        name = self.form_name.strip()
        return name, SaveAccountDTO(
            account_type=self.form_account_type,
            name=name,
            registration_number=self.form_registration_number or None,
            address=self.form_address or None,
            postal_code=self.form_postal_code or None,
            city=self.form_city or None,
            phone=self.form_phone or None,
            email=self.form_email or None,
            contact_name=self.form_contact_name or None,
        )

    async def _create(self, form_data: dict) -> AsyncGenerator:
        """Create a new account from form data."""
        from gws_care.account.account_service import AccountService

        name, dto = self._build_save_dto()
        if not name:
            yield rx.toast.error("Account name is required")
            return

        async with self:
            _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            account = AccountService.create_account(dto)

        yield rx.toast.success(f"Account '{account.name}' created")

        from ..account_list.account_list_state import AccountListState
        yield AccountListState.on_load()

    async def _update(self, form_data: dict) -> AsyncGenerator:
        """Update an existing account from form data."""
        from gws_care.account.account_service import AccountService

        name, dto = self._build_save_dto()
        if not name:
            yield rx.toast.error("Account name is required")
            return

        async with self:
            _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            AccountService.update_account(self._editing_account_id, dto)

        yield rx.toast.success("Account updated successfully")

        from ..account_list.account_list_state import AccountListState
        yield AccountListState.on_load()
