from gws_core import BadRequestException, NotFoundException

from gws_care.company.company import Company
from gws_care.company.company_dto import SaveCompanyDTO


class CompanyService:
    """CRUD service for Company."""

    @classmethod
    def get_company(cls, company_id: str) -> Company:
        company = Company.get_or_none(Company.id == company_id)
        if company is None:
            raise NotFoundException(f"Company '{company_id}' not found")
        return company

    @classmethod
    def list_companies(cls, active_only: bool = True) -> list[Company]:
        query = Company.select()
        if active_only:
            query = query.where(Company.is_active == True)
        return list(query.order_by(Company.name))

    @classmethod
    def create_company(cls, dto: SaveCompanyDTO) -> Company:
        if not dto.name or not dto.name.strip():
            raise BadRequestException("Company name is required")
        company = Company()
        cls._apply_dto(company, dto)
        company.save()
        return company

    @classmethod
    def update_company(cls, company_id: str, dto: SaveCompanyDTO) -> Company:
        company = cls.get_company(company_id)
        cls._apply_dto(company, dto)
        company.save()
        return company

    @classmethod
    def deactivate_company(cls, company_id: str) -> Company:
        company = cls.get_company(company_id)
        company.is_active = False
        company.save()
        return company

    @classmethod
    def _apply_dto(cls, company: Company, dto: SaveCompanyDTO) -> None:
        company.name = dto.name.strip()
        company.registration_number = dto.registration_number
        company.address = dto.address
        company.postal_code = dto.postal_code
        company.city = dto.city
        company.phone = dto.phone
        company.email = dto.email
        company.contact_name = dto.contact_name

    @classmethod
    def get_company_id_for_account(cls, account_id: str) -> str | None:
        """Find the company linked to an account via its patients.

        Looks for a patient already linked to this account that has a company_id set,
        and returns that company_id. Returns None if no link is found.
        """
        from gws_care.patient.patient import Patient
        p = (
            Patient.select(Patient.company_id)
            .where(
                (Patient.billing_account == account_id)
                & Patient.company_id.is_null(False)
                & (Patient.company_id != "")
            )
            .first()
        )
        return p.company_id if p else None
