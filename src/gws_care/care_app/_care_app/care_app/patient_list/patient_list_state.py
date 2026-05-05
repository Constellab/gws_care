"""State management for the patient list page."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class PatientRowDTO(BaseModel):
    """Lightweight DTO for displaying a patient row in the list."""

    id: str
    patient_number: str
    last_name: str
    first_name: str
    date_of_birth: str
    gender: str
    city: str | None = None
    phone: str | None = None
    account_name: str | None = None


class AccountOptionDTO(BaseModel):
    """Lightweight account option for filter dropdown."""

    id: str
    name: str


class PatientListState(ReflexMainState):
    """State for the patient list page."""

    patients: list[PatientRowDTO] = []
    companies: list[AccountOptionDTO] = []
    is_loading: bool = False
    error_message: str = ""

    search_name: str = ""
    search_patient_number: str = ""
    search_phone: str = ""
    filter_account_id: str = ""
    filter_dob_from: str = ""
    filter_dob_to: str = ""
    sort_column: str = "last_name"
    sort_ascending: bool = True

    @rx.event
    async def on_load(self):
        """Load patients when the page is mounted."""
        await self._load_companies()
        await self._load_patients()

    @rx.event
    async def set_filter_account(self, value: str):
        """Filter by account."""
        self.filter_account_id = value if value != "ALL" else ""
        await self._load_patients()

    @rx.event
    async def set_filter_dob_from(self, value: str):
        """Filter patients born on or after this date."""
        self.filter_dob_from = value
        await self._load_patients()

    @rx.event
    async def set_filter_dob_to(self, value: str):
        """Filter patients born on or before this date."""
        self.filter_dob_to = value
        await self._load_patients()

    @rx.event
    async def handle_name_change(self, value: str):
        """Filter by name."""
        self.search_name = value
        await self._load_patients()

    @rx.event
    async def handle_patient_number_change(self, value: str):
        """Filter by patient number."""
        self.search_patient_number = value
        await self._load_patients()

    @rx.event
    async def handle_phone_change(self, value: str):
        """Filter by phone."""
        self.search_phone = value
        await self._load_patients()

    @rx.event
    async def clear_filters(self):
        """Reset all filters and reload."""
        self.search_name = ""
        self.search_patient_number = ""
        self.search_phone = ""
        self.filter_account_id = ""
        self.filter_dob_from = ""
        self.filter_dob_to = ""
        await self._load_patients()

    @rx.event
    async def set_sort(self, column: str):
        """Sort by column; toggle direction if already sorted by the same column."""
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column
            self.sort_ascending = True
        await self._load_patients()

    @rx.event
    def go_to_patient(self, patient_id: str):
        """Navigate to the patient detail page."""
        return rx.redirect(f"/patient/{patient_id}")

    async def _load_companies(self):
        """Internal: load active accounts for the filter dropdown."""
        try:
            with await self.authenticate_user():
                from gws_care.account.account_service import AccountService
                comps = AccountService.list_accounts()
                self.companies = [
                    AccountOptionDTO(id=str(c.id), name=c.name) for c in comps
                ]
        except Exception:
            self.companies = []

    async def _load_patients(self):
        """Internal: load patients from DB with current filters."""
        if not await self.check_authentication():
            self.error_message = "Authentication required"
            return

        self.is_loading = True
        self.error_message = ""

        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_service import PatientService
                patients = PatientService.search_patients(
                    name=self.search_name or None,
                    patient_number=self.search_patient_number or None,
                    phone=self.search_phone or None,
                    account_id=self.filter_account_id or None,
                    dob_from=self.filter_dob_from or None,
                    dob_to=self.filter_dob_to or None,
                )
                patient_rows = [
                    PatientRowDTO(
                        id=str(p.id),
                        patient_number=p.patient_number,
                        last_name=p.last_name,
                        first_name=p.first_name,
                        date_of_birth=p.date_of_birth.isoformat(),
                        gender=p.gender,
                        city=p.city,
                        phone=p.phone,
                        account_name=p.billing_account.name if p.billing_account_id else None,
                    )
                    for p in patients
                ]
                sort_col = self.sort_column
                self.patients = sorted(
                    patient_rows,
                    key=lambda row: (getattr(row, sort_col) or "").lower(),
                    reverse=not self.sort_ascending,
                )
        except Exception as e:
            self.error_message = f"Error loading patients: {e}"
        finally:
            self.is_loading = False
