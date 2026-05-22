from typing import List, Optional

from .medical_doctor import MedicalDoctor
from .medical_doctor_dto import MedicalDoctorDTO, SaveMedicalDoctorDTO


class MedicalDoctorService:

    @classmethod
    def _to_dto(cls, d: MedicalDoctor) -> MedicalDoctorDTO:
        return MedicalDoctorDTO(
            id=str(d.id),
            first_name=d.first_name,
            last_name=d.last_name,
            full_name=d.get_full_name(),
            specialization=d.specialization,
            phone=d.phone,
            email=d.email,
            rpps_number=d.rpps_number,
            address=d.address,
            is_active=d.is_active,
        )

    @classmethod
    def list_doctors(cls, active_only: bool = True) -> List[MedicalDoctorDTO]:
        query = MedicalDoctor.select().order_by(MedicalDoctor.last_name, MedicalDoctor.first_name)
        if active_only:
            query = query.where(MedicalDoctor.is_active == True)
        return [cls._to_dto(d) for d in query]

    @classmethod
    def get_doctor(cls, doctor_id: str) -> MedicalDoctorDTO:
        d = MedicalDoctor.get_by_id(doctor_id)
        return cls._to_dto(d)

    @classmethod
    def create_doctor(cls, dto: SaveMedicalDoctorDTO) -> MedicalDoctorDTO:
        d = MedicalDoctor()
        d.first_name = dto.first_name.strip()
        d.last_name = dto.last_name.strip()
        d.specialization = dto.specialization or None
        d.phone = dto.phone or None
        d.email = dto.email or None
        d.rpps_number = dto.rpps_number or None
        d.address = dto.address or None
        d.is_active = True
        d.save(force_insert=True)
        return cls._to_dto(d)

    @classmethod
    def update_doctor(cls, doctor_id: str, dto: SaveMedicalDoctorDTO) -> MedicalDoctorDTO:
        d = MedicalDoctor.get_by_id(doctor_id)
        d.first_name = dto.first_name.strip()
        d.last_name = dto.last_name.strip()
        d.specialization = dto.specialization or None
        d.phone = dto.phone or None
        d.email = dto.email or None
        d.rpps_number = dto.rpps_number or None
        d.address = dto.address or None
        d.save()
        return cls._to_dto(d)

    @classmethod
    def deactivate_doctor(cls, doctor_id: str) -> None:
        d = MedicalDoctor.get_by_id(doctor_id)
        d.is_active = False
        d.save()

    @classmethod
    def get_doctor_model(cls, doctor_id: str) -> Optional[MedicalDoctor]:
        try:
            return MedicalDoctor.get_by_id(doctor_id)
        except Exception:
            return None
