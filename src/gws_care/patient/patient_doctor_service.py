"""Service for managing patient ↔ doctor links."""

from gws_core import BadRequestException, NotFoundException

from gws_care.doctor.medical_doctor import MedicalDoctor
from gws_care.doctor.medical_doctor_service import MedicalDoctorDTO
from gws_care.patient.patient import Patient
from gws_care.patient.patient_doctor import PatientDoctor


class LinkedDoctorDTO:
    """Lightweight doctor row for the patient Doctors tab."""

    def __init__(self, doctor_id: str, full_name: str, specialization: str,
                 phone: str, email: str, is_referent: bool):
        self.doctor_id = doctor_id
        self.full_name = full_name
        self.specialization = specialization
        self.phone = phone
        self.email = email
        self.is_referent = is_referent


class PatientDoctorService:

    @classmethod
    def get_linked_doctors(cls, patient_id: str) -> list[PatientDoctor]:
        return list(
            PatientDoctor.select(PatientDoctor, MedicalDoctor)
            .join(MedicalDoctor)
            .where(PatientDoctor.patient == patient_id)
            .order_by(PatientDoctor.is_referent.desc(), MedicalDoctor.last_name)
        )

    @classmethod
    def get_referent(cls, patient_id: str) -> MedicalDoctor | None:
        row = PatientDoctor.get_or_none(
            (PatientDoctor.patient == patient_id) & (PatientDoctor.is_referent == True)
        )
        return row.doctor if row else None

    @classmethod
    def link_doctor(cls, patient_id: str, doctor_id: str) -> PatientDoctor:
        patient = Patient.get_or_none(Patient.id == patient_id)
        if patient is None:
            raise NotFoundException(f"Patient '{patient_id}' not found")
        doctor = MedicalDoctor.get_or_none(MedicalDoctor.id == doctor_id)
        if doctor is None:
            raise NotFoundException(f"Doctor '{doctor_id}' not found")
        row, created = PatientDoctor.get_or_create(
            patient=patient, doctor=doctor,
            defaults={"is_referent": False}
        )
        return row

    @classmethod
    def unlink_doctor(cls, patient_id: str, doctor_id: str) -> None:
        PatientDoctor.delete().where(
            (PatientDoctor.patient == patient_id) & (PatientDoctor.doctor == doctor_id)
        ).execute()

    @classmethod
    def set_referent(cls, patient_id: str, doctor_id: str) -> None:
        """Set doctor_id as the referent for patient_id (clears previous referent)."""
        if not PatientDoctor.get_or_none(
            (PatientDoctor.patient == patient_id) & (PatientDoctor.doctor == doctor_id)
        ):
            raise BadRequestException("Doctor is not linked to this patient")
        # Clear all referent flags for this patient
        PatientDoctor.update(is_referent=False).where(
            PatientDoctor.patient == patient_id
        ).execute()
        # Set the new referent
        PatientDoctor.update(is_referent=True).where(
            (PatientDoctor.patient == patient_id) & (PatientDoctor.doctor == doctor_id)
        ).execute()

    @classmethod
    def clear_referent(cls, patient_id: str) -> None:
        PatientDoctor.update(is_referent=False).where(
            PatientDoctor.patient == patient_id
        ).execute()
