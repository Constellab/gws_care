"""State management for the account detail page."""

import reflex as rx
from pydantic import BaseModel

from ..common.patient_picker_state import PatientPickerRowDTO, PatientPickerState


class AccountDetailDTO(BaseModel):
    """Full account details DTO."""

    id: str
    name: str
    registration_number: str | None = None
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    phone: str | None = None
    email: str | None = None
    contact_name: str | None = None
    is_active: bool = True


class AccountPatientRowDTO(BaseModel):
    """Lightweight patient row for the account detail patient list."""

    id: str
    patient_number: str
    last_name: str
    first_name: str
    date_of_birth: str
    gender: str
    city: str | None = None
    phone: str | None = None


class AccountDetailState(PatientPickerState):
    """State for the account detail page."""

    # ── Patient picker vars (declared here for independent state storage) ─────
    picker_patients: list[PatientPickerRowDTO] = []
    picker_is_loading: bool = False
    picker_error: str = ""
    picker_filter_name: str = ""
    picker_filter_number: str = ""
    picker_account_id: str = ""
    picker_is_open: bool = False
    picker_selected_id: str = ""
    picker_selected_label: str = ""

    # ── Patient picker events ─────────────────────────────────────────────────────

    @rx.event
    async def open_patient_picker(self):
        await self._open_patient_picker()

    @rx.event
    def close_patient_picker(self):
        self.picker_is_open = False

    @rx.event
    async def picker_clear_selection(self):
        self.picker_selected_id = ""
        self.picker_selected_label = ""

    @rx.event
    async def picker_set_filter_name(self, value: str):
        await self._picker_set_filter_name(value)

    @rx.event
    async def picker_set_filter_number(self, value: str):
        await self._picker_set_filter_number(value)

    @rx.event
    async def picker_clear_filters(self):
        await self._picker_clear_filters()

    @rx.event
    def picker_select_patient(self, patient_id: str, label: str):
        self.picker_selected_id = patient_id
        self.picker_selected_label = label
        self.picker_is_open = False

    account: AccountDetailDTO | None = None
    patients: list[AccountPatientRowDTO] = []
    is_loading: bool = False
    error_message: str = ""

    # Assign existing patient dialog
    assign_dialog_open: bool = False
    is_assigning: bool = False

    @rx.event
    async def on_load(self):
        """Load account data when the page is mounted."""
        await self._load_account()

    @rx.event
    def go_back(self):
        """Navigate back to the account list."""
        return rx.redirect("/accounts")

    @rx.event
    def go_to_patient(self, patient_id: str):
        """Navigate to the patient detail page."""
        return rx.redirect(f"/patient/{patient_id}")

    # ── Assign patient dialog ──────────────────────────────────────────────

    @rx.event
    async def open_assign_dialog(self):
        """Open the assign-patient dialog using the picker (shows all patients, no account filter)."""
        # No account filter: allow assigning any patient (regardless of current account)
        await self._open_picker(account_id="")
        self.assign_dialog_open = True

    @rx.event
    def close_assign_dialog(self):
        """Close the assign-patient dialog."""
        self.assign_dialog_open = False

    @rx.event
    async def confirm_assign(self):
        """Assign the selected patient to this account."""
        if not self.picker_selected_id or not self.account:
            return
        self.is_assigning = True
        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_service import PatientService
                PatientService.add_account(self.picker_selected_id, self.account.id)
            self.assign_dialog_open = False
            await self._load_patients()
        except Exception as e:
            self.error_message = f"Error assigning patient: {e}"
        finally:
            self.is_assigning = False

    @rx.event
    async def remove_patient(self, patient_id: str):
        """Remove a patient from this account (unlink the account)."""
        if not self.account:
            return
        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_service import PatientService
                PatientService.remove_account(patient_id, self.account.id)
            await self._load_patients()
        except Exception as e:
            self.error_message = f"Error removing patient: {e}"

    # ── Internal loaders ───────────────────────────────────────────────────

    async def _load_account(self):
        """Fetch account info and patients."""
        if not await self.check_authentication():
            self.error_message = "Authentication required"
            return

        account_id = self.account_id_param
        if not account_id:
            self.error_message = "No account ID in URL"
            return

        self.is_loading = True
        self.error_message = ""

        try:
            with await self.authenticate_user():
                from gws_care.account.account_service import AccountService
                a = AccountService.get_account(account_id)
                self.account = AccountDetailDTO(
                    id=str(a.id),
                    name=a.name,
                    registration_number=a.registration_number,
                    address=a.address,
                    postal_code=a.postal_code,
                    city=a.city,
                    phone=a.phone,
                    email=a.email,
                    contact_name=a.contact_name,
                    is_active=a.is_active,
                )

            await self._load_patients()
        except Exception as e:
            self.error_message = f"Error loading account: {e}"
        finally:
            self.is_loading = False

    async def _load_patients(self):
        """Reload patients for this account."""
        if not self.account:
            return
        with await self.authenticate_user():
            from gws_care.patient.patient_service import PatientService
            patients = PatientService.list_patients_for_account(self.account.id)
            self.patients = [
                AccountPatientRowDTO(
                    id=str(p.id),
                    patient_number=p.patient_number,
                    last_name=p.last_name,
                    first_name=p.first_name,
                    date_of_birth=p.date_of_birth.isoformat(),
                    gender=p.gender,
                    city=p.city,
                    phone=p.phone,
                )
                for p in patients
            ]
