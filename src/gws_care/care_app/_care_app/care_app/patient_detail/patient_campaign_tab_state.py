"""State for the Campaigns tab on the patient detail page."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class PatientCampaignRowDTO(BaseModel):
    campaign_id: str
    campaign_number: str
    name: str
    start_date: str
    end_date: str
    status: str
    status_label: str
    status_color: str


class PatientCampaignTabState(rx.State):
    """Shows campaigns the patient is enrolled in."""

    campaigns: list[PatientCampaignRowDTO] = []
    is_loading: bool = False
    error_message: str = ""

    _patient_id: str = ""

    @rx.event
    async def load(self, patient_id: str):
        self._patient_id = patient_id
        await self._load_campaigns()

    async def _load_campaigns(self):
        if not self._patient_id:
            self.campaigns = []
            return
        self.is_loading = True
        self.error_message = ""
        try:
            _main = await self.get_state(ReflexMainState)
            with await _main.authenticate_user():
                from gws_care.campaign.campaign import Campaign
                from gws_care.campaign.campaign_patient import CampaignPatient
                from gws_care.campaign.campaign_status import CampaignStatus

                links = list(
                    CampaignPatient.select(CampaignPatient, Campaign)
                    .join(Campaign)
                    .where(CampaignPatient.patient == self._patient_id)
                    .order_by(Campaign.start_date.desc())
                )

                status_labels = {
                    "draft": ("Brouillon", "gray"),
                    "validated": ("Validée", "blue"),
                    "terrain_exam": ("Examens terrain", "orange"),
                    "sample_analysis": ("Analyse labo", "yellow"),
                    "lab_done": ("Labo terminé", "cyan"),
                    "doctor_clinic_validated": ("Validé médecin clinique", "indigo"),
                    "doctor_company_validated": ("Validé médecin entreprise", "violet"),
                    "closed": ("Clôturée", "green"),
                    "archived": ("Archivée", "gray"),
                }

                rows = []
                for link in links:
                    try:
                        c = link.program
                        status_val = c.status.value if hasattr(c.status, "value") else str(c.status)
                        label, color = status_labels.get(status_val, (status_val, "gray"))
                        rows.append(PatientCampaignRowDTO(
                            campaign_id=str(c.id),
                            campaign_number=c.campaign_number or "",
                            name=c.name or "",
                            start_date=c.start_date.isoformat() if c.start_date else "",
                            end_date=c.end_date.isoformat() if c.end_date else "",
                            status=status_val,
                            status_label=label,
                            status_color=color,
                        ))
                    except Exception:
                        pass
                self.campaigns = rows
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_loading = False

    @rx.event
    def go_to_campaign(self, campaign_id: str):
        return rx.redirect(f"/campaign/{campaign_id}")
