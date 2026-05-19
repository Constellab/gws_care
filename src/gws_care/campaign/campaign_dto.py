"""Campaign DTO — lightweight Pydantic models for Reflex state serialization."""

from datetime import date

from pydantic import BaseModel


class CampaignDTO(BaseModel):
    id: str
    name: str
    account_id: str
    account_name: str
    status: str
    status_label: str
    status_color: str
    start_date: date | None
    end_date: date | None
    location: str | None
    psc_doctor_name: str | None
    enterprise_doctor_name: str | None
    requires_medical_review: bool
    patient_count: int = 0
    notes: str | None


class SaveCampaignDTO(BaseModel):
    name: str
    account_id: str
    start_date: date | None = None
    end_date: date | None = None
    location: str | None = None
    psc_doctor_id: str | None = None
    enterprise_doctor_id: str | None = None
    requires_medical_review: bool = False
    notes: str | None = None
