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

    # Pagination
    page: int = 1
    page_size: int = 50
    total_count: int = 0

    # Doctor view: when logged in as a doctor, only their own patients are shown
    is_doctor_view: bool = False
    doctor_context_id: str = ""

    @rx.var
    def total_pages(self) -> int:
        if self.total_count == 0:
            return 1
        return max(1, (self.total_count + self.page_size - 1) // self.page_size)

    @rx.var
    def has_prev_page(self) -> bool:
        return self.page > 1

    @rx.var
    def has_next_page(self) -> bool:
        return self.page < self.total_pages

    @rx.event
    async def on_load(self):
        """Load patients when the page is mounted."""
        # Detect if the authenticated user is a doctor role (not an admin)
        if not await self.check_authentication():
            return
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.user.user_role_service import UserRoleService
                from gws_care.user.care_role import CareRole
                roles = UserRoleService.get_roles_for_user(str(auth_user.id))
                _doctor_roles = {CareRole.MEDECIN_PSC, CareRole.MEDECIN_ENTREPRISE}
                _admin_roles = {CareRole.SUPER_ADMIN_PSC, CareRole.ADMIN_PSC}
                is_doctor = any(r in _doctor_roles for r in roles)
                is_admin = any(r in _admin_roles for r in roles)
                if is_doctor and not is_admin:
                    self.is_doctor_view = True
                    self.doctor_context_id = str(auth_user.id)
                else:
                    self.is_doctor_view = False
                    self.doctor_context_id = ""
        except Exception:
            self.is_doctor_view = False
            self.doctor_context_id = ""
        await self._load_companies()
        await self._load_patients()

    @rx.event
    async def go_to_page(self, page: int):
        self.page = max(1, min(page, self.total_pages))
        await self._load_patients()

    @rx.event
    async def prev_page(self):
        if self.has_prev_page:
            self.page -= 1
            await self._load_patients()

    @rx.event
    async def next_page(self):
        if self.has_next_page:
            self.page += 1
            await self._load_patients()

    @rx.event
    async def set_filter_account(self, value: str):
        """Filter by account — reset to page 1."""
        self.filter_account_id = value if value != "ALL" else ""
        self.page = 1
        await self._load_patients()

    @rx.event
    async def set_filter_dob_from(self, value: str):
        self.filter_dob_from = value
        self.page = 1
        await self._load_patients()

    @rx.event
    async def set_filter_dob_to(self, value: str):
        self.filter_dob_to = value
        self.page = 1
        await self._load_patients()

    @rx.event
    async def handle_name_change(self, value: str):
        """Debounce: state stores value immediately; _load_patients is called.
        The actual debounce is handled in the component via rx.debounce_input."""
        self.search_name = value
        self.page = 1
        await self._load_patients()

    @rx.event
    async def handle_patient_number_change(self, value: str):
        self.search_patient_number = value
        self.page = 1
        await self._load_patients()

    @rx.event
    async def handle_phone_change(self, value: str):
        self.search_phone = value
        self.page = 1
        await self._load_patients()

    @rx.event
    async def clear_filters(self):
        self.search_name = ""
        self.search_patient_number = ""
        self.search_phone = ""
        self.filter_account_id = ""
        self.filter_dob_from = ""
        self.filter_dob_to = ""
        self.page = 1
        await self._load_patients()

    @rx.event
    async def set_sort(self, column: str):
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column
            self.sort_ascending = True
        self.page = 1
        await self._load_patients()

    @rx.event
    def go_to_patient(self, patient_id: str):
        return rx.redirect(f"/patient/{patient_id}")

    async def _load_companies(self):
        try:
            with await self.authenticate_user():
                from gws_care.account.account_service import AccountService
                comps = AccountService.list_accounts()
                self.companies = [
                    AccountOptionDTO(id=str(c.id), name=c.name) for c in comps
                ]
        except Exception as exc:
            self.companies = []

    async def _load_patients(self):
        """Load one page of patients from DB — sort and filter are handled at SQL level."""
        if not await self.check_authentication():
            self.error_message = "Authentication required"
            return
        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_service import PatientService
                filters = dict(
                    name=self.search_name or None,
                    patient_number=self.search_patient_number or None,
                    phone=self.search_phone or None,
                    account_id=self.filter_account_id or None,
                    dob_from=self.filter_dob_from or None,
                    dob_to=self.filter_dob_to or None,
                    doctor_id=self.doctor_context_id or None,
                )
                self.total_count = PatientService.count_patients(**filters)
                # Clamp page to valid range after count update
                self.page = max(1, min(self.page, self.total_pages))
                patients = PatientService.search_patients(
                    **filters,
                    sort_column=self.sort_column,
                    sort_ascending=self.sort_ascending,
                    limit=self.page_size,
                    offset=(self.page - 1) * self.page_size,
                )
                self.patients = [
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
        except Exception as e:
            self.error_message = f"Erreur lors du chargement des patients : {e}"
        finally:
            self.is_loading = False
