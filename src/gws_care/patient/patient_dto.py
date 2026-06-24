from datetime import date

from gws_core import BaseModelDTO, ModelDTO


class PatientDTO(ModelDTO):
    patient_number: str
    last_name: str
    first_name: str
    birth_name: str | None
    date_of_birth: date
    gender: str
    sex: str | None = None
    nationality: str | None = None
    photo: str | None
    address: str | None
    address_complement: str | None = None
    postal_code: str | None
    city: str | None
    country: str | None = None
    phone: str | None
    phone_country: str | None = None
    email: str | None
    primary_physician_name: str | None = None
    primary_physician_phone: str | None = None
    account_ids: list[str] = []
    company_id: str | None = None
    social_security_number: str | None = None
    weight: float | None = None
    height: float | None = None
    notification_preferences: dict | None = None
    is_draft: bool = False


class SavePatientDTO(BaseModelDTO):
    last_name: str
    first_name: str
    birth_name: str | None = None
    date_of_birth: date
    gender: str
    sex: str | None = None
    nationality: str | None = None
    photo: str | None = None
    address: str | None = None
    address_complement: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country: str | None = None
    phone: str | None = None
    phone_country: str | None = None
    email: str | None = None
    primary_physician_name: str | None = None
    primary_physician_phone: str | None = None
    # Optional: link to an account at creation time
    account_id: str | None = None
    social_security_number: str | None = None
    weight: float | None = None
    height: float | None = None
    notification_preferences: dict | None = None
    is_draft: bool = False
