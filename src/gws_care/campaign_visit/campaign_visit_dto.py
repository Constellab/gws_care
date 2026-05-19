"""DTOs for CampaignVisit."""

from datetime import datetime

from gws_core import BaseModelDTO, ModelDTO

from gws_care.campaign_visit.campaign_visit_status import CampaignVisitStatus


class CampaignVisitDTO(ModelDTO):
    """Full campaign visit record returned to callers."""

    visit_number: str
    program_id: str | None = None
    patient_id: str
    patient_name: str | None = None
    billing_account_id: str | None = None
    account_name: str | None = None
    scheduled_at: datetime | None = None
    status: CampaignVisitStatus

    # Interpretation text (authorship tracked in CampaignVisitValidationWorkflow)
    doctor_clinic_interpretation: str | None = None
    doctor_company_interpretation: str | None = None
    doctor_company_message: str | None = None


class CampaignVisitRowDTO(BaseModelDTO):
    """Lightweight row for list views."""

    id: str
    visit_number: str
    patient_id: str | None = None
    patient_name: str | None = None
    patient_number: str | None = None
    billing_account_id: str | None = None
    account_name: str | None = None
    scheduled_at: str | None = None
    status: str
    status_label: str


class ValidateLabDTO(BaseModelDTO):
    """DTO for Lab Validation."""
    pass  # No extra payload; the acting user is taken from auth context


class ValidateDoctorClinicDTO(BaseModelDTO):
    """DTO for Validation Clinic Doctor / Employé."""

    interpretation: str | None = None


class ValidateDoctorCompanyDTO(BaseModelDTO):
    """DTO for Validation Company Doctor / Employé."""

    interpretation: str | None = None
    message: str | None = None  # Message transmitted to the patient


class SaveStandaloneVisitDTO(BaseModelDTO):
    """DTO for creating or updating a standalone scheduled visit (no campaign)."""

    patient_id: str
    billing_account_id: str | None = None
    scheduled_at: str          # ISO datetime string (YYYY-MM-DDTHH:MM)
    notes: str | None = None
