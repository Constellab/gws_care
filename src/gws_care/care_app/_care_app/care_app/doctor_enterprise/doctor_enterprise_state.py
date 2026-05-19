"""Doctor Enterprise page — view PSC-validated dossiers, add interpretation, publish (US-130-132)."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class EntDossierRowDTO(BaseModel):
    campaign_patient_id: str
    patient_id: str
    patient_number: str
    patient_name: str
    campaign_id: str
    campaign_name: str
    medical_status: str
    medical_status_label: str
    medical_status_color: str
    psc_notes: str
    enterprise_notes: str
    patient_message: str
    enterprise_validated_at: str
    published_at: str


class DoctorEnterpriseState(ReflexMainState):
    dossiers: list[EntDossierRowDTO] = []
    is_loading: bool = False
    error: str = ""
    success: str = ""

    # Dialog
    dialog_open: bool = False
    dialog_patient_id: str = ""
    dialog_patient_name: str = ""
    dialog_campaign_id: str = ""
    enterprise_notes_input: str = ""
    patient_message_input: str = ""
    dialog_error: str = ""
    is_saving: bool = False

    @rx.event
    async def on_load(self):
        await self._load()

    @rx.event
    def open_dialog(
        self, campaign_id: str, patient_id: str, patient_name: str,
        current_notes: str, current_message: str
    ):
        self.dialog_campaign_id = campaign_id
        self.dialog_patient_id = patient_id
        self.dialog_patient_name = patient_name
        self.enterprise_notes_input = current_notes
        self.patient_message_input = current_message
        self.dialog_error = ""
        self.dialog_open = True

    @rx.event
    def close_dialog(self):
        self.dialog_open = False

    @rx.event
    def set_enterprise_notes(self, v: str):
        self.enterprise_notes_input = v

    @rx.event
    def set_patient_message(self, v: str):
        self.patient_message_input = v

    @rx.event
    async def save_interpretation(self):
        self.is_saving = True
        self.dialog_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.add_enterprise_interpretation(
                    self.dialog_campaign_id, self.dialog_patient_id,
                    self.enterprise_notes_input, self.patient_message_input
                )
            self.dialog_open = False
            self.success = "Interprétation entreprise enregistrée."
            await self._load()
        except Exception as e:
            self.dialog_error = str(e)
        finally:
            self.is_saving = False

    @rx.event
    async def validate_patient(self, campaign_id: str, patient_id: str):
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.validate_enterprise_patient(campaign_id, patient_id)
            self.success = "Dossier validé entreprise."
            await self._load()
        except Exception as e:
            self.error = str(e)

    @rx.event
    async def publish_patient(self, campaign_id: str, patient_id: str):
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.publish_patient_results(campaign_id, patient_id)
            self.success = "Résultats publiés au patient."
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
                from gws_care.role.user_role_service import UserRoleService
                from gws_care.role.care_role import CareRole
                from gws_core import CurrentUserService

                gws_user = CurrentUserService.get_and_check_current_user()
                linked_account_id = UserRoleService.get_linked_account_id(str(gws_user.id))

                query = (
                    CampaignPatient.select(CampaignPatient, Campaign, Patient)
                    .join(Campaign)
                    .switch(CampaignPatient)
                    .join(Patient)
                    .where(
                        (CampaignPatient.presence_status == "PRESENT")
                        & CampaignPatient.medical_status.in_([
                            MedicalRecordStatus.PSC_VALIDATED.value,
                            MedicalRecordStatus.ENTERPRISE_INTERPRETED.value,
                            MedicalRecordStatus.ENTERPRISE_VALIDATED.value,
                        ])
                    )
                    .order_by(Patient.last_name)
                )

                # Filter by linked account for non-admin enterprise roles
                if linked_account_id:
                    query = query.where(Campaign.account == linked_account_id)
                rows = []
                for cp in query:
                    try:
                        ms = MedicalRecordStatus(cp.medical_status)
                    except ValueError:
                        ms = MedicalRecordStatus.PENDING
                    rows.append(EntDossierRowDTO(
                        campaign_patient_id=str(cp.id),
                        patient_id=str(cp.patient.id),
                        patient_number=cp.patient.patient_number,
                        patient_name=f"{cp.patient.last_name} {cp.patient.first_name}",
                        campaign_id=str(cp.campaign.id),
                        campaign_name=cp.campaign.name,
                        medical_status=cp.medical_status,
                        medical_status_label=ms.get_label(),
                        medical_status_color=ms.get_color(),
                        psc_notes=cp.psc_notes or "",
                        enterprise_notes=cp.enterprise_notes or "",
                        patient_message=cp.patient_message or "",
                        enterprise_validated_at=(
                            cp.enterprise_validated_at.isoformat() if cp.enterprise_validated_at else ""
                        ),
                        published_at=cp.published_at.isoformat() if cp.published_at else "",
                    ))
                self.dossiers = rows
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_loading = False
