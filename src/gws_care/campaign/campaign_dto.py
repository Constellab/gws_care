"""DTOs for Campaign."""

from datetime import date

from gws_core import BaseModelDTO, ModelDTO

from gws_care.campaign.campaign_status import CampaignStatus


class CampaignDTO(ModelDTO):
    """Full campaign record returned to callers."""

    campaign_number: str
    name: str
    account_id: str | None = None
    account_name: str | None = None
    start_date: date
    end_date: date
    status: CampaignStatus
    notes: str | None = None
    is_individual: bool = False


class CampaignRowDTO(BaseModelDTO):
    """Lightweight row for list views."""

    id: str
    campaign_number: str
    name: str
    account_name: str | None = None
    start_date: str   # ISO string
    end_date: str     # ISO string
    status: str
    status_label: str
    patient_count: int = 0
    exam_type_count: int = 0


class SaveCampaignDTO(BaseModelDTO):
    """DTO for creating or updating a campaign."""

    name: str
    account_id: str
    start_date: str   # ISO date string YYYY-MM-DD
    end_date: str     # ISO date string YYYY-MM-DD
    notes: str | None = None
