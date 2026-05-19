"""Doctor PSC queue — interpretation and validation (US-120, US-121, US-122, US-123)."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class DossierRowDTO(BaseModel):
    campaign_patient_id: str
    patient_id: str
    patient_number: str
    patient_name: str
    campaign_id: str
    campaign_name: str
    account_name: str
    medical_status: str
    medical_status_label: str
    medical_status_color: str
    psc_notes: str
    psc_validated_at: str


class DoctorPscState(ReflexMainState):
    dossiers: list[DossierRowDTO] = []
    is_loading: bool = False
    error: str = ""
    success: str = ""
    filter_campaign_id: str = ""
    filter_status: str = "LAB_VALIDATED"

    # Interpretation dialog
    interp_dialog_open: bool = False
    interp_campaign_id: str = ""
    interp_patient_id: str = ""
    interp_patient_name: str = ""
    interp_notes: str = ""
    is_saving: bool = False

    @rx.event
    async def on_load(self):
        await self._load()

    @rx.event
    async def set_filter_status(self, v: str):
        self.filter_status = v
        await self._load()

    @rx.event
    def open_interp_dialog(
        self, campaign_id: str, patient_id: str, patient_name: str, current_notes: str
    ):
        self.interp_campaign_id = campaign_id
        self.interp_patient_id = patient_id
        self.interp_patient_name = patient_name
        self.interp_notes = current_notes
        self.interp_dialog_open = True

    @rx.event
    def close_interp_dialog(self):
        self.interp_dialog_open = False

    @rx.event
    def set_interp_notes(self, v: str):
        self.interp_notes = v

    @rx.event
    async def save_interpretation(self):
        self.is_saving = True
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.add_psc_interpretation(
                    self.interp_campaign_id, self.interp_patient_id, self.interp_notes
                )
            self.interp_dialog_open = False
            self.success = "Interprétation enregistrée."
            await self._load()
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_saving = False

    @rx.event
    async def validate_patient(self, campaign_id: str, patient_id: str):
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.validate_psc_patient(campaign_id, patient_id)
            self.success = "Dossier validé PSC."
            await self._load()
        except Exception as e:
            self.error = str(e)

    @rx.event
    async def validate_campaign(self, campaign_id: str):
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.validate_psc_campaign(campaign_id)
            self.success = "Campagne validée PSC."
            await self._load()
        except Exception as e:
            self.error = str(e)

    @rx.event
    def dismiss_messages(self):
        self.error = ""
        self.success = ""

    async def _load(self):
        if not await self.check_authentication():
            return
        self.is_loading = True
        self.error = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_patient import CampaignPatient, MedicalRecordStatus
                from gws_care.campaign.campaign import Campaign
                from gws_care.patient.patient import Patient
                query = (
                    CampaignPatient.select(CampaignPatient, Campaign, Patient)
                    .join(Campaign)
                    .switch(CampaignPatient)
                    .join(Patient)
                )
                if self.filter_status and self.filter_status != "ALL":
                    query = query.where(CampaignPatient.medical_status == self.filter_status)
                else:
                    query = query.where(
                        CampaignPatient.medical_status.in_([
                            MedicalRecordStatus.LAB_ENTERED.value,
                            MedicalRecordStatus.LAB_VALIDATED.value,
                            MedicalRecordStatus.PSC_INTERPRETED.value,
                        ])
                    )
                if self.filter_campaign_id:
                    query = query.where(CampaignPatient.campaign == self.filter_campaign_id)
                rows = []
                for cp in query.order_by(CampaignPatient.medical_status, Patient.last_name):
                    try:
                        ms = MedicalRecordStatus(cp.medical_status)
                    except ValueError:
                        ms = MedicalRecordStatus.PENDING
                    rows.append(DossierRowDTO(
                        campaign_patient_id=str(cp.id),
                        patient_id=str(cp.patient.id),
                        patient_number=cp.patient.patient_number,
                        patient_name=f"{cp.patient.last_name} {cp.patient.first_name}",
                        campaign_id=str(cp.campaign.id),
                        campaign_name=cp.campaign.name,
                        account_name=cp.campaign.account.name if cp.campaign.account_id else "",
                        medical_status=cp.medical_status,
                        medical_status_label=ms.get_label(),
                        medical_status_color=ms.get_color(),
                        psc_notes=cp.psc_notes or "",
                        psc_validated_at=cp.psc_validated_at.isoformat() if cp.psc_validated_at else "",
                    ))
                self.dossiers = rows
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_loading = False
