from gws_core import BaseModelDTO, ModelDTO


class AccountDTO(ModelDTO):
    account_type: str = "COMPANY"
    company_id: str | None = None  # FK to Company (employer) — populated when account_type==COMPANY
    name: str
    registration_number: str | None
    address: str | None
    postal_code: str | None
    city: str | None
    phone: str | None
    email: str | None
    contact_name: str | None
    is_active: bool


class SaveAccountDTO(BaseModelDTO):
    account_type: str = "COMPANY"
    company_id: str | None = None  # FK to Company — set when creating a billing account from a Company
    name: str
    registration_number: str | None = None
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    phone: str | None = None
    email: str | None = None
    contact_name: str | None = None
