"""CampaignVisit model."""

import secrets
import string
from datetime import datetime

from gws_core import EnumField
from peewee import CharField, DateTimeField, ForeignKeyField, TextField

from gws_care.account.account import Account
from gws_care.campaign.campaign import Campaign
from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.doctor.medical_doctor import MedicalDoctor
from gws_care.patient.patient import Patient
from gws_care.user.user import User
from gws_care.visit.appointment_mode import AppointmentMode
from gws_care.visit.campaign_visit_status import CampaignVisitStatus
from gws_care.visit.consultation_visit_status import ConsultationVisitStatus
from gws_care.visit.visit_dto import VisitDTO
from gws_care.visit.visit_type import VisitType


def _generate_visit_number() -> str:
    chars = string.ascii_uppercase + string.digits
    suffix = "".join(secrets.choice(chars) for _ in range(8))
    return f"VIS-{suffix}"


class Visit(ModelWithUser):
    """One medical visit for a patient.

    Two types controlled by visit_type:

    CONSULTATION — standalone medical visit; prescriptions, certificates, and/or
                   exam records can be attached. Simple PENDING → CLOSED lifecycle.

    CAMPAIGN     — visit within a campaign; full validation workflow:
                   PENDING → VISIT_DONE → LAB_DONE
                           → DOCTOR_CLINIC_VALIDATED → DOCTOR_COMPANY_VALIDATED
                   Validation steps tracked in CampaignVisitValidationWorkflow.
    """

    visit_type: VisitType = EnumField(choices=VisitType, default=VisitType.CAMPAIGN, null=False)
    visit_number: str = CharField(max_length=50, unique=True, null=False, index=True)
    campaign: Campaign = ForeignKeyField(Campaign, null=True, backref="visits", on_delete="CASCADE", column_name='program_id')
    patient: Patient = ForeignKeyField(Patient, null=False, backref="visits", on_delete="CASCADE")
    billing_account: Account = ForeignKeyField(Account, null=True, backref="visits", on_delete="SET NULL")
    scheduled_at: datetime = DateTimeField(null=True)
    # Campaign visit lifecycle — used when visit_type=CAMPAIGN
    campaign_visit_status: CampaignVisitStatus = EnumField(choices=CampaignVisitStatus, default=CampaignVisitStatus.PENDING, null=False)
    # Consultation visit lifecycle — used when visit_type=CONSULTATION
    consultation_visit_status: ConsultationVisitStatus = EnumField(choices=ConsultationVisitStatus, null=True)

    # Appointment fields — set when a patient self-books a consultation visit
    doctor: MedicalDoctor = ForeignKeyField(MedicalDoctor, null=True, backref="visits", on_delete="SET NULL")
    appointment_mode: AppointmentMode = EnumField(choices=AppointmentMode, default=AppointmentMode.AT_WORK, null=True)
    patient_notes: str = TextField(null=True)
    appointment_address: str = TextField(null=True)

    # Interpretation text — kept on CampaignVisit for fast access; authorship is in CampaignVisitValidationWorkflow
    doctor_clinic_interpretation: str = TextField(null=True)
    doctor_company_interpretation: str = TextField(null=True)
    doctor_company_message: str = TextField(null=True)

    # Classical / Exam visit closing audit
    closed_by: User = ForeignKeyField(User, null=True, backref="+", on_delete="SET NULL")
    closed_at: datetime = DateTimeField(null=True)

    def _before_insert(self) -> None:
        super()._before_insert()
        if not self.visit_number:
            self.visit_number = _generate_visit_number()

    @property
    def campaign_id(self):
        """Raw FK value for the campaign field (DB column: program_id)."""
        return self.program_id

    def to_dto(self) -> VisitDTO:
        patient = self.patient
        account = self.billing_account if self.billing_account_id else None
        doctor = self.doctor if self.doctor_id else None
        return VisitDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            visit_type=self.visit_type,
            visit_number=self.visit_number,
            campaign_id=str(self.campaign_id) if self.campaign_id else None,
            patient_id=str(self.patient_id),
            billing_account_id=str(self.billing_account_id) if self.billing_account_id else None,
            account_name=account.name if account else None,
            scheduled_at=self.scheduled_at,
            patient_name=patient.get_full_name() if patient else None,
            campaign_visit_status=self.campaign_visit_status,
            doctor_id=str(self.doctor_id) if self.doctor_id else None,
            doctor_name=doctor.get_full_name() if doctor else None,
            appointment_mode=self.appointment_mode,
            patient_notes=self.patient_notes,
            doctor_clinic_interpretation=self.doctor_clinic_interpretation,
            doctor_company_interpretation=self.doctor_company_interpretation,
            doctor_company_message=self.doctor_company_message,
        )

    class Meta:
        table_name = "gws_care_visit"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
