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


class DoctorOptionDTO(BaseModel):
    """One doctor option for the campaign creation dropdown."""

    id: str
    label: str  # "Dr. Dupont Jean"


class CampaignRowDTO(BaseModel):
    """One campaign row for the account detail campaigns list."""
    id: str
    name: str
    status: str
    status_label: str
    status_color: str
    start_date: str
    end_date: str
    patient_count: int
    location: str


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

    # ── Campaigns ─────────────────────────────────────────────────────────
    campaigns: list[CampaignRowDTO] = []
    campaign_dialog_open: bool = False
    new_campaign_name: str = ""
    new_campaign_start: str = ""
    new_campaign_end: str = ""
    new_campaign_location: str = ""
    new_campaign_psc_doctor_id: str = ""
    new_campaign_enterprise_doctor_id: str = ""
    psc_doctor_options: list[DoctorOptionDTO] = []
    enterprise_doctor_options: list[DoctorOptionDTO] = []
    is_creating_campaign: bool = False
    campaign_error: str = ""

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
            from gws_care.patient.patient import Patient
            unassigned = list(
                Patient.select()
                .where(Patient.billing_account.is_null(True))
                .order_by(Patient.last_name, Patient.first_name)
            )
            self.unassigned_patients = [
                UnassignedPatientOptionDTO(
                    id=str(p.id),
                    label=f"{p.last_name} {p.first_name} ({p.patient_number})",
                )
                for p in unassigned
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
            await self._load_campaigns()
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

    async def _load_campaigns(self):
        """Reload campaigns for this account."""
        if not self.account:
            return
        with await self.authenticate_user():
            from peewee import fn
            from gws_care.campaign.campaign_patient import CampaignPatient
            from gws_care.campaign.campaign_service import CampaignService
            from gws_care.campaign.campaign_status import CampaignStatus
            campaigns = CampaignService.list_campaigns_for_account(self.account.id)
            ids = [c.id for c in campaigns]
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
            rows: list[CampaignRowDTO] = []
            for c in campaigns:
                try:
                    status_enum = CampaignStatus(c.status)
                    status_label = status_enum.get_label()
                    status_color = status_enum.get_color()
                except Exception:
                    status_label = c.status
                    status_color = "gray"
                rows.append(CampaignRowDTO(
                    id=str(c.id),
                    name=c.name,
                    status=c.status,
                    status_label=status_label,
                    status_color=status_color,
                    start_date=c.start_date.isoformat() if c.start_date else "-",
                    end_date=c.end_date.isoformat() if c.end_date else "-",
                    patient_count=count_map.get(str(c.id), 0),
                    location=c.location or "",
                ))
            self.campaigns = rows

    # ── Campaign dialog events ─────────────────────────────────────────────

    @rx.event
    async def open_campaign_dialog(self):
        self.new_campaign_name = ""
        self.new_campaign_start = ""
        self.new_campaign_end = ""
        self.new_campaign_location = ""
        self.new_campaign_psc_doctor_id = ""
        self.new_campaign_enterprise_doctor_id = ""
        self.campaign_error = ""
        self.campaign_dialog_open = True
        # Load doctor options
        try:
            with await self.authenticate_user():
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_care_role import UserCareRole
                from gws_care.user.user import User

                psc_rows = list(
                    UserCareRole.select(UserCareRole, User).join(User)
                    .where(UserCareRole.role == CareRole.MEDECIN_PSC.value)
                    .order_by(User.last_name)
                )
                self.psc_doctor_options = [
                    DoctorOptionDTO(id=str(r.user.id), label=f"{r.user.last_name} {r.user.first_name}")
                    for r in psc_rows
                ]

                ent_rows = list(
                    UserCareRole.select(UserCareRole, User).join(User)
                    .where(UserCareRole.role == CareRole.MEDECIN_ENTREPRISE.value)
                    .order_by(User.last_name)
                )
                self.enterprise_doctor_options = [
                    DoctorOptionDTO(id=str(r.user.id), label=f"{r.user.last_name} {r.user.first_name}")
                    for r in ent_rows
                ]
        except Exception as exc:
            self.psc_doctor_options = []
            self.enterprise_doctor_options = []

    @rx.event
    def close_campaign_dialog(self):
        self.campaign_dialog_open = False

    @rx.event
    def set_new_campaign_name(self, value: str):
        self.new_campaign_name = value

    @rx.event
    def set_new_campaign_start(self, value: str):
        self.new_campaign_start = value

    @rx.event
    def set_new_campaign_end(self, value: str):
        self.new_campaign_end = value

    @rx.event
    def set_new_campaign_location(self, value: str):
        self.new_campaign_location = value

    @rx.event
    def set_new_campaign_psc_doctor(self, value: str):
        self.new_campaign_psc_doctor_id = "" if value == "__none__" else value

    @rx.event
    def set_new_campaign_enterprise_doctor(self, value: str):
        self.new_campaign_enterprise_doctor_id = "" if value == "__none__" else value

    @rx.event
    async def create_campaign(self):
        if not self.new_campaign_name.strip():
            self.campaign_error = "Le nom de la campagne est obligatoire."
            return
        if not self.account:
            return
        self.is_creating_campaign = True
        self.campaign_error = ""
        try:
            with await self.authenticate_user():
                from datetime import date
                from gws_care.campaign.campaign_service import CampaignService
                start = date.fromisoformat(self.new_campaign_start) if self.new_campaign_start else None
                end = date.fromisoformat(self.new_campaign_end) if self.new_campaign_end else None
                CampaignService.create_campaign(
                    account_id=self.account.id,
                    name=self.new_campaign_name.strip(),
                    start_date=start,
                    end_date=end,
                    location=self.new_campaign_location.strip() or None,
                    psc_doctor_id=self.new_campaign_psc_doctor_id or None,
                    enterprise_doctor_id=self.new_campaign_enterprise_doctor_id or None,
                )
            self.campaign_dialog_open = False
            await self._load_campaigns()
        except Exception as e:
            self.campaign_error = f"Erreur : {e}"
        finally:
            self.is_creating_campaign = False

    @rx.event
    def go_to_campaign(self, campaign_id: str):
        return rx.redirect(f"/campaign/{campaign_id}")
