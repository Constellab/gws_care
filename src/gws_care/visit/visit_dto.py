"""DTOs for Visit."""

from datetime import datetime
from typing import Optional

from gws_core import BaseModelDTO, ModelDTO

from gws_care.visit.appointment_mode import AppointmentMode
from gws_care.visit.campaign_visit_status import CampaignVisitStatus
from gws_care.visit.consultation_visit_status import ConsultationVisitStatus
from gws_care.visit.visit_type import VisitType


class VisitDTO(ModelDTO):
    """Full visit record returned to callers."""

    visit_type: VisitType = VisitType.CAMPAIGN
    visit_number: str
    campaign_id: str | None = None
    patient_id: str
    patient_name: str | None = None
    billing_account_id: str | None = None
    account_name: str | None = None
    scheduled_at: datetime | None = None
    campaign_visit_status: CampaignVisitStatus
    consultation_visit_status: Optional[ConsultationVisitStatus] = None

    # Appointment booking fields
    doctor_id: str | None = None
    doctor_name: str | None = None
    appointment_mode: AppointmentMode | None = None
    patient_notes: str | None = None

    # Interpretation text (authorship tracked in CampaignVisitValidationWorkflow)
    doctor_clinic_interpretation: str | None = None
    doctor_company_interpretation: str | None = None
    doctor_company_message: str | None = None


class VisitRowDTO(BaseModelDTO):
    """Lightweight row for list views."""

    id: str
    visit_number: str
    patient_id: str | None = None
    patient_name: str | None = None
    patient_number: str | None = None
    billing_account_id: str | None = None
    account_name: str | None = None
    scheduled_at: str | None = None
    campaign_visit_status: str
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


class BookAppointmentDTO(BaseModelDTO):
    """DTO submitted when a patient self-books a consultation appointment."""

    scheduled_at: str                   # ISO datetime string (YYYY-MM-DDTHH:MM)
    doctor_id: str | None = None
    appointment_mode: str = "onsite"    # AppointmentMode value
    patient_notes: str | None = None
