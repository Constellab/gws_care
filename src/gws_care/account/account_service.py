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
    def list_accounts(cls, active_only: bool = True) -> list[Account]:
        query = Account.select()
        if active_only:
            query = query.where(Account.is_active == True)
        return list(query.order_by(Account.name))

    @classmethod
    def create_account(cls, dto: SaveAccountDTO) -> Account:
        if not dto.name or not dto.name.strip():
            raise BadRequestException("Account name is required")
        account = Account()
        cls._apply_dto(account, dto)
        account.save()
        return account

    @classmethod
    def update_account(cls, account_id: str, dto: SaveAccountDTO) -> Account:
        account = cls.get_account(account_id)
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
        account.name = dto.name.strip()
        account.registration_number = dto.registration_number
        account.address = dto.address
        account.postal_code = dto.postal_code
        account.city = dto.city
        account.phone = dto.phone
        account.email = dto.email
        account.contact_name = dto.contact_name
