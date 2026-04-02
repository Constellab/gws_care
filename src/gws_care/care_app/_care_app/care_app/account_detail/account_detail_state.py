"""State management for the account detail page."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


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


class UnassignedPatientOptionDTO(BaseModel):
    """Patient option for the assign dialog (patients without an account)."""

    id: str
    label: str  # "LAST_NAME First (PAT-XXXXXX)"


class AccountDetailState(ReflexMainState):
    """State for the account detail page."""

    account: AccountDetailDTO | None = None
    patients: list[AccountPatientRowDTO] = []
    is_loading: bool = False
    error_message: str = ""

    # Assign existing patient dialog
    assign_dialog_open: bool = False
    unassigned_patients: list[UnassignedPatientOptionDTO] = []
    assign_patient_id: str = ""
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
        """Open the assign-patient dialog and load unassigned patients."""
        if not await self.check_authentication():
            return
        with await self.authenticate_user():
            from gws_care.patient.patient_service import PatientService
            all_patients = PatientService.search_patients()
            # Keep only those without an account
            self.unassigned_patients = [
                UnassignedPatientOptionDTO(
                    id=str(p.id),
                    label=f"{p.last_name} {p.first_name} ({p.patient_number})",
                )
                for p in all_patients
                if not p.billing_account_id
            ]
        self.assign_patient_id = ""
        self.assign_dialog_open = True

    @rx.event
    def close_assign_dialog(self):
        """Close the assign-patient dialog."""
        self.assign_dialog_open = False
        self.assign_patient_id = ""

    @rx.event
    def set_assign_patient_id(self, value: str):
        self.assign_patient_id = value

    @rx.event
    async def confirm_assign(self):
        """Assign the selected patient to this account."""
        if not self.assign_patient_id or not self.account:
            return
        self.is_assigning = True
        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_service import PatientService
                PatientService.assign_account(self.assign_patient_id, self.account.id)
            self.assign_dialog_open = False
            self.assign_patient_id = ""
            await self._load_patients()
        except Exception as e:
            self.error_message = f"Error assigning patient: {e}"
        finally:
            self.is_assigning = False

    @rx.event
    async def remove_patient(self, patient_id: str):
        """Remove a patient from this account (set account to None)."""
        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_service import PatientService
                PatientService.assign_account(patient_id, None)
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
