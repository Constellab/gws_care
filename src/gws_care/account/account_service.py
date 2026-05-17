from gws_core import BadRequestException, NotFoundException

from gws_care.account.account import Account
from gws_care.account.account_dto import SaveAccountDTO


class AccountService:
    """CRUD service for Account."""

    @classmethod
    def get_account(cls, account_id: str) -> Account:
        account = Account.get_or_none(Account.id == account_id)
        if account is None:
            raise NotFoundException(f"Account '{account_id}' not found")
        return account

    @classmethod
    def list_accounts(
        cls,
        active_only: bool = True,
        name: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Account]:
        query = Account.select()
        if active_only:
            query = query.where(Account.is_active == True)
        if name:
            query = query.where(Account.name.contains(name))
        query = query.order_by(Account.name)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return list(query)

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
        account.name = dto.name.strip()
        account.registration_number = dto.registration_number
        account.address = dto.address
        account.postal_code = dto.postal_code
        account.city = dto.city
        account.phone = dto.phone
        account.email = dto.email
        account.contact_name = dto.contact_name
