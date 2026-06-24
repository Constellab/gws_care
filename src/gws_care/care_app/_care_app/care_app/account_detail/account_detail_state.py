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


class CampaignRowDTO(BaseModel):
    """Lightweight campaign row for the account detail campaign list."""

    id: str
    name: str
    status_label: str
    status_color: str
    patient_count: str
    start_date: str
    end_date: str
    location: str


class DoctorOptionDTO(BaseModel):
    """Doctor option for the campaign creation doctor selector."""

    id: str
    label: str


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

    # Campaigns list
    campaigns: list[CampaignRowDTO] = []

    # Campaign creation dialog
    campaign_dialog_open: bool = False
    is_creating_campaign: bool = False
    campaign_error: str = ""
    new_campaign_name: str = ""
    new_campaign_start: str = ""
    new_campaign_end: str = ""
    new_campaign_location: str = ""
    new_campaign_psc_doctor_id: str = ""
    new_campaign_enterprise_doctor_id: str = ""
    psc_doctor_options: list[DoctorOptionDTO] = []
    enterprise_doctor_options: list[DoctorOptionDTO] = []

    @rx.event
    async def on_load(self):
        """Load account data when the page is mounted."""
        await self._load_account()

    @rx.event
    def go_back(self):
        return rx.call_script("window.history.back()")

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
            return
        finally:
            self.is_assigning = False
        from ..patient_list.patient_list_state import PatientListState
        yield PatientListState.on_load

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
            return
        from ..patient_list.patient_list_state import PatientListState
        yield PatientListState.on_load

    # ── Campaign navigation ────────────────────────────────────────────────

    @rx.event
    def go_to_campaign(self, campaign_id: str):
        return rx.redirect(f"/campaign/{campaign_id}")

    # ── Campaign creation dialog ───────────────────────────────────────────

    @rx.event
    async def open_campaign_dialog(self):
        self.campaign_dialog_open = True
        self.campaign_error = ""
        self.new_campaign_name = ""
        self.new_campaign_start = ""
        self.new_campaign_end = ""
        self.new_campaign_location = ""
        self.new_campaign_psc_doctor_id = ""
        self.new_campaign_enterprise_doctor_id = ""
        # Load doctor options
        try:
            with await self.authenticate_user():
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_care_role import UserCareRole
                from gws_care.user.user import User
                psc_roles = list(UserCareRole.select().where(UserCareRole.role == CareRole.MEDECIN_PSC))
                ent_roles = list(UserCareRole.select().where(UserCareRole.role == CareRole.MEDECIN_ENTREPRISE))

                def _doctor_label(user_id) -> str:
                    u = User.get_or_none(User.id == user_id)
                    return u.full_name if u else str(user_id)

                self.psc_doctor_options = [
                    DoctorOptionDTO(id=str(r.user_id), label=_doctor_label(r.user_id))
                    for r in psc_roles
                ]
                self.enterprise_doctor_options = [
                    DoctorOptionDTO(id=str(r.user_id), label=_doctor_label(r.user_id))
                    for r in ent_roles
                ]
        except Exception:
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
        self.new_campaign_psc_doctor_id = value

    @rx.event
    def set_new_campaign_enterprise_doctor(self, value: str):
        self.new_campaign_enterprise_doctor_id = value

    @rx.event
    async def create_campaign(self):
        if not self.account or not self.new_campaign_name.strip():
            return
        self.is_creating_campaign = True
        self.campaign_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_dto import SaveCampaignDTO
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.create_campaign(SaveCampaignDTO(
                    name=self.new_campaign_name.strip(),
                    account_id=self.account.id,
                    start_date=self.new_campaign_start or "2025-01-01",
                    end_date=self.new_campaign_end or "2025-12-31",
                    notes=self.new_campaign_location.strip() or None,
                ))
            self.campaign_dialog_open = False
            await self._load_campaigns()
        except Exception as e:
            self.campaign_error = str(e)
        finally:
            self.is_creating_campaign = False

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
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign import Campaign
                from gws_care.campaign.campaign_patient import CampaignPatient
                from gws_care.campaign.campaign_status import CampaignStatus
                campaigns = list(
                    Campaign.select()
                    .where(Campaign.account == self.account.id)
                    .order_by(Campaign.created_at.desc())
                )
                status_label_map = {
                    CampaignStatus.DRAFT.value: "Brouillon",
                    CampaignStatus.VALIDATED.value: "Validée",
                    CampaignStatus.TERRAIN_EXAM.value: "Terrain",
                    CampaignStatus.SAMPLE_ANALYSIS.value: "Analyse",
                    CampaignStatus.LAB_DONE.value: "Labo terminé",
                    CampaignStatus.DOCTOR_CLINIC_VALIDATED.value: "Médecin clinique",
                    CampaignStatus.DOCTOR_COMPANY_VALIDATED.value: "Médecin entreprise",
                    CampaignStatus.CLOSED.value: "Clôturée",
                    CampaignStatus.ARCHIVED.value: "Archivée",
                }
                status_color_map = {
                    CampaignStatus.DRAFT.value: "gray",
                    CampaignStatus.VALIDATED.value: "blue",
                    CampaignStatus.TERRAIN_EXAM.value: "orange",
                    CampaignStatus.SAMPLE_ANALYSIS.value: "amber",
                    CampaignStatus.LAB_DONE.value: "teal",
                    CampaignStatus.DOCTOR_CLINIC_VALIDATED.value: "indigo",
                    CampaignStatus.DOCTOR_COMPANY_VALIDATED.value: "violet",
                    CampaignStatus.CLOSED.value: "green",
                    CampaignStatus.ARCHIVED.value: "gray",
                }
                rows = []
                for c in campaigns:
                    patient_count = CampaignPatient.select().where(CampaignPatient.campaign == c.id).count()
                    status_val = c.status.value if hasattr(c.status, "value") else str(c.status)
                    rows.append(CampaignRowDTO(
                        id=str(c.id),
                        name=c.name,
                        status_label=status_label_map.get(status_val, status_val),
                        status_color=status_color_map.get(status_val, "gray"),
                        patient_count=str(patient_count),
                        start_date=c.start_date.isoformat() if c.start_date else "—",
                        end_date=c.end_date.isoformat() if c.end_date else "—",
                        location=c.notes or "—",
                    ))
                self.campaigns = rows
        except Exception:
            self.campaigns = []
