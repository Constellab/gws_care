from datetime import date

from gws_core import BaseModelDTO, ModelDTO


class PatientDTO(ModelDTO):
    patient_number: str
    last_name: str
    first_name: str
    birth_name: str | None
    date_of_birth: date
    gender: str
    photo: str | None
    address: str | None
    postal_code: str | None
    city: str | None
    phone: str | None
    email: str | None
    primary_physician_name: str | None
    primary_physician_phone: str | None
    account_id: str | None = None
    company_id: str | None = None


class SavePatientDTO(BaseModelDTO):
    last_name: str
    first_name: str
    birth_name: str | None = None
    date_of_birth: date
    gender: str
    photo: str | None = None
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    phone: str | None = None
    email: str | None = None
    primary_physician_name: str | None = None
    primary_physician_phone: str | None = None
    account_id: str | None = None
