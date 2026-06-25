from typing import List, Optional

from .medical_doctor import MedicalDoctor
from .medical_doctor_dto import MedicalDoctorDTO, SaveMedicalDoctorDTO


class DoctorSelectionDTO:
    """Lightweight DTO for doctor dropdowns (appointment booking, campaign assignment)."""
    def __init__(self, id: str, full_name: str, specialization: str = ""):
        self.id = id
        self.full_name = full_name
        self.specialization = specialization


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
            is_archived=d.is_archived,
            status_reason=d.status_reason or "",
        )

    @classmethod
    def list_doctors(cls, active_only: bool = True) -> List[MedicalDoctorDTO]:
        """Return doctors. active_only=True excludes inactive AND archived."""
        query = MedicalDoctor.select().order_by(MedicalDoctor.last_name, MedicalDoctor.first_name)
        if active_only:
            query = query.where(
                (MedicalDoctor.is_active == True) & (MedicalDoctor.is_archived == False)
            )
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
        d.is_archived = False
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
    def deactivate_doctor(cls, doctor_id: str, reason: str = "") -> None:
        d = MedicalDoctor.get_by_id(doctor_id)
        d.is_active = False
        d.status_reason = reason or None
        d.save()

    @classmethod
    def reactivate_doctor(cls, doctor_id: str) -> None:
        d = MedicalDoctor.get_by_id(doctor_id)
        d.is_active = True
        d.is_archived = False
        d.status_reason = None
        d.save()

    @classmethod
    def archive_doctor(cls, doctor_id: str, reason: str = "") -> None:
        d = MedicalDoctor.get_by_id(doctor_id)
        d.is_archived = True
        d.is_active = False
        d.status_reason = reason or None
        d.save()

    @classmethod
    def delete_doctor(cls, doctor_id: str) -> None:
        """Physically remove a doctor from the registry."""
        d = MedicalDoctor.get_by_id(doctor_id)
        d.delete_instance()

    @classmethod
    def get_doctor_model(cls, doctor_id: str) -> Optional[MedicalDoctor]:
        try:
            return MedicalDoctor.get_by_id(doctor_id)
        except Exception:
            return None

    @classmethod
    def get_specializations(cls) -> List[str]:
        """Return sorted list of distinct active (non-archived) specializations."""
        specs = set()
        for d in MedicalDoctor.select(MedicalDoctor.specialization).where(
            (MedicalDoctor.is_active == True)
            & (MedicalDoctor.is_archived == False)
            & (MedicalDoctor.specialization.is_null(False))
        ):
            s = (d.specialization or "").strip()
            if s:
                specs.add(s)
        return sorted(specs)

    @classmethod
    def list_for_selection(cls, specialization: str = "") -> List[DoctorSelectionDTO]:
        """Return active, non-archived doctors for dropdowns."""
        query = MedicalDoctor.select().where(
            (MedicalDoctor.is_active == True) & (MedicalDoctor.is_archived == False)
        )
        if specialization:
            query = query.where(MedicalDoctor.specialization == specialization)
        query = query.order_by(MedicalDoctor.last_name, MedicalDoctor.first_name)
        return [
            DoctorSelectionDTO(
                id=str(d.id),
                full_name=d.get_full_name(),
                specialization=d.specialization or "",
            )
            for d in query
        ]

    @classmethod
    def get_doctor_by_id_or_none(cls, doctor_id: str) -> Optional["MedicalDoctorDTO"]:
        """Return None if doctor not found (no exception)."""
        try:
            return cls.get_doctor(doctor_id)
        except Exception:
            return None
