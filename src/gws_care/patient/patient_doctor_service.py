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
    def get_doctors_from_visits(cls, patient_id: str) -> list[MedicalDoctor]:
        """Doctors assigned to one of this patient's visits at booking time.

        Distinct from explicit PatientDoctor links — surfaces doctors who saw
        the patient via an appointment even if never manually linked.
        """
        from gws_care.visit.visit import Visit
        doctor_ids = {
            str(v.doctor_id)
            for v in Visit.select(Visit.doctor).where(
                (Visit.patient == patient_id) & (Visit.doctor.is_null(False))
            ).distinct()
        }
        if not doctor_ids:
            return []
        return list(MedicalDoctor.select().where(MedicalDoctor.id.in_(doctor_ids)))

    @classmethod
    def get_work_doctors_from_visits(cls, patient_id: str):
        """Médecins du travail (User, role MEDECIN_ENTREPRISE) assigned to one
        of this patient's campaign visits via Visit.work_doctor."""
        from gws_care.user.user import User
        from gws_care.visit.visit import Visit
        user_ids = {
            str(v.work_doctor_id)
            for v in Visit.select(Visit.work_doctor).where(
                (Visit.patient == patient_id) & (Visit.work_doctor.is_null(False))
            ).distinct()
        }
        if not user_ids:
            return []
        return list(User.select().where(User.id.in_(user_ids)))

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
