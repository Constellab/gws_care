"""HR Portal — administrative campaign tracking (US-150)."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class HRPatientDTO(BaseModel):
    patient_id: str
    patient_number: str
    patient_name: str
    phone: str
    presence_status: str
    presence_label: str
    presence_color: str
    appointment_date: str
    exam_done: bool        # True once past PENDING status
    result_published: bool # True when status is PUBLISHED


class HRCampaignDTO(BaseModel):
    id: str
    name: str
    status_label: str
    status_color: str
    start_date: str
    end_date: str
    location: str
    total_patients: int
    present_count: int
    absent_count: int
    pending_count: int


class HRPortalState(ReflexMainState):
    campaigns: list[HRCampaignDTO] = []
    patients: list[HRPatientDTO] = []
    selected_campaign_id: str = ""
    selected_campaign_name: str = ""
    is_loading: bool = False
    is_loading_patients: bool = False
    error: str = ""

    @rx.event
    async def on_load(self):
        await self._load_campaigns()

    @rx.event
    async def select_campaign(self, campaign_id: str, campaign_name: str):
        self.selected_campaign_id = campaign_id
        self.selected_campaign_name = campaign_name
        await self._load_campaign_patients(campaign_id)

    async def _load_campaigns(self):
        if not await self.check_authentication():
            return
        self.is_loading = True
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.campaign.campaign import Campaign
                from gws_care.campaign.campaign_patient import CampaignPatient, PresenceStatus
                from gws_care.campaign.campaign_service import CampaignService
                from gws_care.campaign.campaign_status import CampaignStatus
                from gws_care.role.user_role_service import UserRoleService

                # Filter to linked account if user is RH_ENTREPRISE
                linked_account_id = UserRoleService.get_linked_account_id(str(auth_user.id))

                if linked_account_id:
                    campaigns = list(
                        Campaign.select()
                        .where(Campaign.account == linked_account_id)
                        .order_by(Campaign.start_date.desc())
                    )
                else:
                    campaigns = CampaignService.list_all_campaigns()
                rows = []
                for c in campaigns:
                    total = CampaignPatient.select().where(CampaignPatient.campaign == c.id).count()
                    present = CampaignPatient.select().where(
                        (CampaignPatient.campaign == c.id)
                        & (CampaignPatient.presence_status == PresenceStatus.PRESENT.value)
                    ).count()
                    absent = CampaignPatient.select().where(
                        (CampaignPatient.campaign == c.id)
                        & (CampaignPatient.presence_status == PresenceStatus.ABSENT.value)
                    ).count()
                    try:
                        status_e = CampaignStatus(c.status)
                    except ValueError:
                        status_e = CampaignStatus.DRAFT
                    rows.append(HRCampaignDTO(
                        id=str(c.id),
                        name=c.name,
                        status_label=status_e.get_label(),
                        status_color=status_e.get_color(),
                        start_date=c.start_date.isoformat() if c.start_date else "",
                        end_date=c.end_date.isoformat() if c.end_date else "",
                        location=c.location or "",
                        total_patients=total,
                        present_count=present,
                        absent_count=absent,
                        pending_count=total - present - absent,
                    ))
                self.campaigns = rows
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_loading = False

    async def _load_campaign_patients(self, campaign_id: str):
        self.is_loading_patients = True
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_patient import CampaignPatient, PresenceStatus
                from gws_care.patient.patient import Patient
                rows = (
                    CampaignPatient.select(CampaignPatient, Patient)
                    .join(Patient)
                    .where(CampaignPatient.campaign == campaign_id)
                    .order_by(Patient.last_name)
                )
                patients = []
                for cp in rows:
                    try:
                        ps = PresenceStatus(cp.presence_status)
                    except ValueError:
                        ps = PresenceStatus.PENDING
                    patients.append(HRPatientDTO(
                        patient_id=str(cp.patient.id),
                        patient_number=cp.patient.patient_number,
                        patient_name=f"{cp.patient.last_name} {cp.patient.first_name}",
                        phone=cp.patient.phone or "",
                        presence_status=cp.presence_status,
                        presence_label=ps.get_label(),
                        presence_color=ps.get_color(),
                        appointment_date="",
                        exam_done=cp.medical_status not in ("PENDING", ""),
                        result_published=cp.medical_status == "PUBLISHED",
                    ))
                self.patients = patients
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_loading_patients = False
