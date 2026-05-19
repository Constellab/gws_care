"""DTOs for PatientAccount (patient-account affiliation)."""

from datetime import date

from pydantic import BaseModel


class PatientAccountDTO(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    patient_number: str
    account_id: str
    account_name: str
    status: str
    status_label: str
    status_color: str
    start_date: str | None = None
    end_date: str | None = None
    employee_number: str | None = None
    position: str | None = None
    site: str | None = None
    department: str | None = None
    end_reason: str | None = None


class SavePatientAccountDTO(BaseModel):
    patient_id: str
    account_id: str
    status: str = "ACTIVE"
    start_date: date
    end_date: date | None = None
    employee_number: str | None = None
    position: str | None = None
    site: str | None = None
    department: str | None = None
    end_reason: str | None = None
