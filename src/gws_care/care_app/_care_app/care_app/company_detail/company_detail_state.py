"""State management for the company detail page."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class CompanyDetailDTO(BaseModel):
    """Full company details DTO."""

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


class CompanyPatientRowDTO(BaseModel):
    """Lightweight patient row for the company detail patient list."""

    id: str
    patient_number: str
    last_name: str
    first_name: str
    date_of_birth: str
    gender: str
    city: str | None = None
    phone: str | None = None


class UnassignedPatientOptionDTO(BaseModel):
    """Patient option for the assign dialog (patients without a company)."""

    id: str
    label: str  # "LAST_NAME First (PAT-XXXXXX)"


class CompanyDetailState(ReflexMainState):
    """State for the company detail page."""

    company: CompanyDetailDTO | None = None
    patients: list[CompanyPatientRowDTO] = []
    is_loading: bool = False
    error_message: str = ""

    # Assign existing patient dialog
    assign_dialog_open: bool = False
    unassigned_patients: list[UnassignedPatientOptionDTO] = []
    assign_patient_id: str = ""
    is_assigning: bool = False

    @rx.event
    async def on_load(self):
        """Load company data when the page is mounted."""
        await self._load_company()

    @rx.event
    def go_back(self):
        """Navigate back to the company list."""
        return rx.redirect("/companies")

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
            # Keep only those without a company
            self.unassigned_patients = [
                UnassignedPatientOptionDTO(
                    id=str(p.id),
                    label=f"{p.last_name} {p.first_name} ({p.patient_number})",
                )
                for p in all_patients
                if not p.company_id
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
        """Assign the selected patient to this company."""
        if not self.assign_patient_id or not self.company:
            return
        self.is_assigning = True
        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_service import PatientService
                PatientService.assign_company(self.assign_patient_id, self.company.id)
            self.assign_dialog_open = False
            self.assign_patient_id = ""
            await self._load_patients()
        except Exception as e:
            self.error_message = f"Error assigning patient: {e}"
        finally:
            self.is_assigning = False

    @rx.event
    async def remove_patient(self, patient_id: str):
        """Remove a patient from this company (set company to None)."""
        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_service import PatientService
                PatientService.assign_company(patient_id, None)
            await self._load_patients()
        except Exception as e:
            self.error_message = f"Error removing patient: {e}"

    # ── Internal loaders ───────────────────────────────────────────────────

    async def _load_company(self):
        """Fetch company info and patients."""
        if not await self.check_authentication():
            self.error_message = "Authentication required"
            return

        company_id = self.company_id_param
        if not company_id:
            self.error_message = "No company ID in URL"
            return

        self.is_loading = True
        self.error_message = ""

        try:
            with await self.authenticate_user():
                from gws_care.company.company_service import CompanyService
                c = CompanyService.get_company(company_id)
                self.company = CompanyDetailDTO(
                    id=str(c.id),
                    name=c.name,
                    registration_number=c.registration_number,
                    address=c.address,
                    postal_code=c.postal_code,
                    city=c.city,
                    phone=c.phone,
                    email=c.email,
                    contact_name=c.contact_name,
                    is_active=c.is_active,
                )

            await self._load_patients()
        except Exception as e:
            self.error_message = f"Error loading company: {e}"
        finally:
            self.is_loading = False

    async def _load_patients(self):
        """Reload patients for this company."""
        if not self.company:
            return
        with await self.authenticate_user():
            from gws_care.patient.patient_service import PatientService
            patients = PatientService.list_patients_for_company(self.company.id)
            self.patients = [
                CompanyPatientRowDTO(
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
