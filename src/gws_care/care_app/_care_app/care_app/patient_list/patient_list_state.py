"""State management for the patient list page."""

import reflex as rx
from pydantic import BaseModel

from ..common.account_picker_state import AccountPickerRowDTO, AccountPickerState


class PatientRowDTO(BaseModel):
    """Lightweight DTO for displaying a patient row in the list."""

    id: str
    patient_number: str
    last_name: str
    first_name: str
    date_of_birth: str
    gender: str
    city: str | None = None
    country: str | None = None
    phone: str | None = None
    account_name: str | None = None
    is_draft: bool = False


class PatientListState(AccountPickerState):
    """State for the patient list page."""

    # ── Account picker vars (declared here for independent state storage) ─────
    acct_picker_is_open: bool = False
    acct_picker_filter: str = ""
    acct_picker_accounts: list[AccountPickerRowDTO] = []
    acct_picker_is_loading: bool = False
    acct_picker_error: str = ""
    acct_picker_selected_id: str = ""
    acct_picker_selected_name: str = ""

    patients: list[PatientRowDTO] = []
    is_loading: bool = False
    is_loading_more: bool = False
    has_more: bool = False
    error_message: str = ""
    is_doctor_view: bool = False

    # Pagination
    total_count: int = 0

    _page_offset: int = 0
    _current_page_size: int = 50

    search_name: str = ""
    search_patient_number: str = ""
    search_phone: str = ""
    filter_account_id: str = ""
    filter_dob_from: str = ""
    filter_dob_to: str = ""
    sort_column: str = "last_name"
    sort_ascending: bool = True

    # ── Account picker events ─────────────────────────────────────────────────────

    @rx.event
    async def open_account_picker(self):
        await self._open_account_picker()

    @rx.event
    def close_account_picker(self):
        self.acct_picker_is_open = False

    @rx.event
    async def acct_picker_set_filter(self, value: str):
        await self._acct_picker_set_filter(value)

    @rx.event
    async def acct_picker_confirm(self, account_id: str, name: str):
        await self._acct_picker_confirm(account_id, name)

    @rx.event
    async def acct_picker_clear(self):
        await self._acct_picker_clear()

    @rx.event
    async def on_load(self):
        """Load patients when the page is mounted."""
        await self._load_roles()
        redirect = await self._require_any_of(
            self.is_operator, self.is_doctor, self.is_admin, self.is_account_admin,
            redirect_to="/patient-dashboard",
        )
        if redirect:
            return redirect
        await self._load_patients()

    async def _on_account_picked(self, account_id: str) -> None:
        self.filter_account_id = account_id
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

    @rx.event
    async def load_more_patients(self):
        """Append the next page of patients to the current list."""
        self.is_loading_more = True
        await self._load_patients(reset=False)

    async def _load_patients(self, reset: bool = True):
        """Internal: load patients from DB with current filters."""
        if not await self.check_authentication():
            self.error_message = "Authentication required"
            return

        if reset:
            self._page_offset = 0
            self.is_loading = True
            from gws_care.core.care_app_config_service import CareAppConfigService
            self._current_page_size = CareAppConfigService.get_page_size()
        self.error_message = ""

        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_service import PatientService
                # Normalize patient number input: strip "PAT-" prefix so that
                # typing "PAT-01" or "01" both match PAT-01XXXX. An input of
                # just "PAT-" strips to empty and shows all patients.
                raw_pn = self.search_patient_number.strip()
                if raw_pn.upper().startswith("PAT-"):
                    raw_pn = raw_pn[4:]
                search_kwargs = dict(
                    name=self.search_name or None,
                    patient_number_prefix=f"PAT-{raw_pn}" if raw_pn else None,
                    phone=self.search_phone or None,
                    account_id=self.filter_account_id or None,
                    dob_from=self.filter_dob_from or None,
                    dob_to=self.filter_dob_to or None,
                )
                # Total count for the "N patient(s)" display
                all_for_count = PatientService.search_patients(**search_kwargs)
                self.total_count = len(all_for_count)
                ps = self._current_page_size

                patients = PatientService.search_patients(
                    **search_kwargs,
                    limit=ps + 1,
                    offset=self._page_offset,
                )
                has_more = len(patients) > ps
                patients = patients[:ps]
                # Batch-fetch account names via join table
                patient_ids = [str(p.id) for p in patients]
                account_names_by_patient: dict[str, list[str]] = {}
                if patient_ids:
                    from gws_care.account.account import Account
                    from gws_care.patient.patient_account import PatientAccount
                    from peewee import JOIN
                    rows = (
                        PatientAccount.select(PatientAccount.patient, Account.name)
                        .join(Account, JOIN.INNER, on=(PatientAccount.account == Account.id))
                        .where(PatientAccount.patient.in_(patient_ids))
                        .tuples()
                    )
                    for patient_fk, account_name in rows:
                        pid = str(patient_fk)
                        account_names_by_patient.setdefault(pid, []).append(account_name)
                new_rows = [
                    PatientRowDTO(
                        id=str(p.id),
                        patient_number=p.patient_number,
                        last_name=p.last_name,
                        first_name=p.first_name,
                        date_of_birth=p.date_of_birth.isoformat(),
                        gender=p.gender,
                        city=p.city,
                        country=p.country,
                        phone=p.phone,
                        account_name=", ".join(account_names_by_patient.get(str(p.id), [])) or None,
                        is_draft=bool(getattr(p, "is_draft", False)),
                    )
                    for p in patients
                ]
                sort_col = self.sort_column
                all_rows = new_rows if reset else self.patients + new_rows
                self.patients = sorted(
                    all_rows,
                    key=lambda row: (getattr(row, sort_col) or "").lower(),
                    reverse=not self.sort_ascending,
                )
                self.has_more = has_more
                self._page_offset += ps
        except Exception as e:
            self.error_message = f"Error loading patients: {e}"
        finally:
            self.is_loading = False
            self.is_loading_more = False
