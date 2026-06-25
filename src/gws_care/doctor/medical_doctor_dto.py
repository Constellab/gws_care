from pydantic import BaseModel


class MedicalDoctorDTO(BaseModel):
    id: str
    first_name: str
    last_name: str
    full_name: str
    specialization: str | None = None
    phone: str | None = None
    email: str | None = None
    rpps_number: str | None = None
    address: str | None = None
    is_active: bool = True
    is_archived: bool = False
    status_reason: str = ""


class SaveMedicalDoctorDTO(BaseModel):
    first_name: str
    last_name: str
    specialization: str | None = None
    phone: str | None = None
    email: str | None = None
    rpps_number: str | None = None
    address: str | None = None
