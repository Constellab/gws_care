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


class CompanyCampaignRowDTO(BaseModel):
    """Lightweight campaign row for the company detail campaigns list."""

    id: str
    name: str
    status_label: str
    status_color: str
    start_date: str
    end_date: str
    patient_count: int = 0


class CompanyAccountRowDTO(BaseModel):
    """Billing account linked to this company."""

    id: str
    name: str
    account_type: str
    registration_number: str | None = None
    email: str | None = None
    is_active: bool = True


class CompanyDetailState(ReflexMainState):
    """State for the company detail page."""

    company: CompanyDetailDTO | None = None
    patients: list[CompanyPatientRowDTO] = []
    campaigns: list[CompanyCampaignRowDTO] = []
    billing_accounts: list[CompanyAccountRowDTO] = []
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
            from gws_care.patient.patient import Patient
            current_company_id = self.company.id if self.company else None
            q = Patient.select().order_by(Patient.last_name, Patient.first_name)
            if current_company_id:
                q = q.where(
                    Patient.company_id.is_null(True) | (Patient.company_id == current_company_id)
                )
            else:
                q = q.where(Patient.company_id.is_null(True))
            self.unassigned_patients = [
                UnassignedPatientOptionDTO(
                    id=str(p.id),
                    label=f"{p.last_name} {p.first_name} ({p.patient_number})",
                )
                for p in q
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
        except Exception as e:
            self.error_message = f"Error assigning patient: {e}"
        finally:
            self.is_assigning = False
        await self._load_patients()

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

    # ── Billing accounts ──────────────────────────────────────────────────

    @rx.event
    def open_create_billing_account(self):
        """Open the account creation dialog pre-linked to this company."""
        if not self.company:
            return
        from ..account_list.account_form_state import AccountFormState
        return [
            AccountFormState.open_create_dialog_for_company(self.company.id, self.company.name),
        ]

    @rx.event
    def go_to_account(self, account_id: str):
        return rx.redirect(f"/account/{account_id}")

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
            await self._load_campaigns()
            await self._load_accounts()
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

    async def _load_campaigns(self):
        """Load campaigns linked to this company."""
        if not self.company:
            return
        try:
            with await self.authenticate_user():
                from peewee import fn
                from gws_care.campaign.campaign import Campaign
                from gws_care.campaign.campaign_patient import CampaignPatient
                from gws_care.campaign.campaign_status import CampaignStatus
                campaigns_qs = (
                    Campaign.select()
                    .where(Campaign.company_id == self.company.id)
                    .order_by(Campaign.start_date.desc())
                    .limit(20)
                )
                ids = [c.id for c in campaigns_qs]
                count_map: dict[str, int] = {}
                if ids:
                    for row in (
                        CampaignPatient.select(
                            CampaignPatient.campaign_id,
                            fn.COUNT(CampaignPatient.id).alias("cnt"),
                        )
                        .where(CampaignPatient.campaign.in_(ids))
                        .group_by(CampaignPatient.campaign_id)
                        .namedtuples()
                    ):
                        count_map[str(row.campaign_id)] = row.cnt
                rows = []
                for c in campaigns_qs:
                    try:
                        status_enum = CampaignStatus(c.status)
                        status_label = status_enum.get_label()
                        status_color = status_enum.get_color()
                    except Exception:
                        status_label = c.status
                        status_color = "gray"
                    rows.append(CompanyCampaignRowDTO(
                        id=str(c.id),
                        name=c.name,
                        status_label=status_label,
                        status_color=status_color,
                        start_date=c.start_date.isoformat() if c.start_date else "",
                        end_date=c.end_date.isoformat() if c.end_date else "",
                        patient_count=count_map.get(str(c.id), 0),
                    ))
                self.campaigns = rows
        except Exception as e:
            pass  # campaigns section is non-critical

    async def _load_accounts(self):
        """Load billing accounts linked to this company."""
        if not self.company:
            return
        try:
            with await self.authenticate_user():
                from gws_care.account.account_service import AccountService
                accounts = AccountService.list_accounts_for_company(self.company.id)
                self.billing_accounts = [
                    CompanyAccountRowDTO(
                        id=str(a.id),
                        name=a.name,
                        account_type=a.account_type,
                        registration_number=a.registration_number,
                        email=a.email,
                        is_active=a.is_active,
                    )
                    for a in accounts
                ]
        except Exception:
            self.billing_accounts = []
