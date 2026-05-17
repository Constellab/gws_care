"""State management for the account list page."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel

from ..common.role_state import RoleState


class AccountRowDTO(BaseModel):
    """Lightweight DTO for displaying an account in the list."""

    id: str
    account_type: str = "COMPANY"
    name: str
    city: str | None = None
    phone: str | None = None
    email: str | None = None
    contact_name: str | None = None
    is_active: bool = True


class AccountListState(RoleState):
    """State for the account list page."""

    accounts: list[AccountRowDTO] = []
    is_loading: bool = False
    is_loading_more: bool = False
    has_more: bool = False
    error_message: str = ""
    search_name: str = ""
    sort_column: str = "name"
    sort_ascending: bool = True

    _page_offset: int = 0
    _current_page_size: int = 50

    @rx.event
    async def on_load(self):
        """Load accounts when the page is mounted."""
        await self._load_roles()
        redirect = await self._require_any_of(self.is_operator, self.is_doctor, self.is_account_admin)
        if redirect:
            return redirect
        await self._load_accounts()

    @rx.event
    async def handle_name_change(self, value: str):
        """Filter accounts by name."""
        self.search_name = value
        await self._load_accounts()

    @rx.event
    async def clear_filters(self):
        """Reset filters."""
        self.search_name = ""
        await self._load_accounts()

    @rx.event
    async def set_sort(self, column: str):
        """Sort by column; toggle direction if already sorted by the same column."""
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column
            self.sort_ascending = True
        await self._load_accounts()

    @rx.event
    def go_to_account(self, account_id: str):
        """Navigate to the account detail page."""
        return rx.redirect(f"/account/{account_id}")

    @rx.event
    async def load_more_accounts(self):
        """Append the next page of accounts to the current list."""
        self.is_loading_more = True
        await self._load_accounts(reset=False)

    @rx.event
    async def deactivate_account(self, account_id: str):
        """Mark an account as inactive.

        :param account_id: DB id of the account to deactivate
        :type account_id: str
        """
        try:
            with await self.authenticate_user():
                from gws_care.account.account_service import AccountService
                AccountService.deactivate_account(account_id)
            await self._load_accounts()
        except Exception as e:
            self.error_message = f"Error deactivating account: {e}"

    async def _load_accounts(self, reset: bool = True):
        """Internal: fetch accounts from DB."""
        if not await self.check_authentication():
            self.error_message = "Authentication required"
            return

        if reset:
            self._page_offset = 0
            self.is_loading = True
            from gws_care.core.care_app_config_service import CareAppConfigService
            self._current_page_size = CareAppConfigService.get_page_size()
        self.error_message = ""

        try:
            with await self.authenticate_user():
                from gws_care.account.account_service import AccountService
                accounts = AccountService.list_accounts(
                    active_only=False,
                    name=self.search_name or None,
                    limit=self._current_page_size + 1,
                    offset=self._page_offset,
                )
                has_more = len(accounts) > self._current_page_size
                accounts = accounts[:self._current_page_size]
                new_rows = [
                    AccountRowDTO(
                        id=str(a.id),
                        account_type=a.account_type or "COMPANY",
                        name=a.name,
                        city=a.city,
                        phone=a.phone,
                        email=a.email,
                        contact_name=a.contact_name,
                        is_active=a.is_active,
                    )
                    for a in accounts
                ]
                sort_col = self.sort_column
                all_rows = new_rows if reset else self.accounts + new_rows
                self.accounts = sorted(
                    all_rows,
                    key=lambda row: "" if getattr(row, sort_col) is None else str(getattr(row, sort_col)).lower(),
                    reverse=not self.sort_ascending,
                )
                self.has_more = has_more
                self._page_offset += self._current_page_size
        except Exception as e:
            self.error_message = f"Error loading accounts: {e}"
        finally:
            self.is_loading = False
            self.is_loading_more = False
