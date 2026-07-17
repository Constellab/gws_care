from gws_core import BadRequestException, NotFoundException

from gws_care.account.account import Account
from gws_care.account.account_dto import SaveAccountDTO
from gws_care.user.user import User


class AccountService:
    """CRUD service for Account."""

    @classmethod
    def get_account(cls, account_id: str, user: User | None = None) -> Account:
        """Fetch an account by id.

        *user*, when provided, is checked via PermissionService.require_own_account
        (ADMIN/OPERATOR/DOCTOR always allowed; RH_ENTREPRISE is scoped to their
        own linked accounts). Callers with no end-user context omit it.
        """
        account = Account.get_or_none(Account.id == account_id)
        if account is None:
            raise NotFoundException(f"Account '{account_id}' not found")
        if user is not None:
            from gws_care.role.permission_service import PermissionService
            PermissionService.require_own_account(user, account_id)
        return account

    @classmethod
    def list_accounts(
        cls,
        active_only: bool = True,
        name: str | None = None,
        account_type: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Account]:
        query = Account.select()
        if active_only:
            query = query.where(Account.is_active == True)
        if name:
            query = query.where(Account.name.contains(name))
        if account_type:
            query = query.where(Account.account_type == account_type)
        query = query.order_by(Account.name)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return list(query)

    @classmethod
    def list_accounts_for_company(cls, company_id: str) -> list[Account]:
        """Return all (active) billing accounts linked to a company."""
        return list(
            Account.select()
            .where(Account.company_id == company_id, Account.is_active == True)
            .order_by(Account.name)
        )

    @classmethod
    def create_account(cls, dto: SaveAccountDTO) -> Account:
        if not dto.name or not dto.name.strip():
            raise BadRequestException("Account name is required")
        if Account.get_or_none(Account.name == dto.name.strip()) is not None:
            raise BadRequestException(f"An account named '{dto.name.strip()}' already exists")
        account = Account()
        cls._apply_dto(account, dto)
        account.save()
        return account

    @classmethod
    def update_account(cls, account_id: str, dto: SaveAccountDTO) -> Account:
        account = cls.get_account(account_id)
        existing = Account.get_or_none(Account.name == dto.name.strip())
        if existing is not None and str(existing.id) != str(account_id):
            raise BadRequestException(f"An account named '{dto.name.strip()}' already exists")
        cls._apply_dto(account, dto)
        account.save()
        return account

    @classmethod
    def deactivate_account(cls, account_id: str) -> Account:
        account = cls.get_account(account_id)
        account.is_active = False
        account.save()
        return account

    @classmethod
    def _apply_dto(cls, account: Account, dto: SaveAccountDTO) -> None:
        account.account_type = dto.account_type
        account.company_id = dto.company_id or None
        account.name = dto.name.strip()
        account.registration_number = dto.registration_number
        account.address = dto.address
        account.postal_code = dto.postal_code
        account.city = dto.city
        account.phone = dto.phone
        account.email = dto.email
        account.contact_first_name = getattr(dto, "contact_first_name", None)
        account.contact_last_name = getattr(dto, "contact_last_name", None)
        account.contact_name = dto.contact_name
