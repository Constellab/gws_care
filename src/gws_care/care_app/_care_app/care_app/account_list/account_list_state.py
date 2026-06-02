"""State management for the account list page."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


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


class AccountListState(ReflexMainState):
    """State for the account list page."""

    accounts: list[AccountRowDTO] = []
    is_loading: bool = False
    error_message: str = ""
    search_name: str = ""
    sort_column: str = "name"
    sort_ascending: bool = True

    # Confirm désactivation
    confirm_deactivate_open: bool = False
    confirm_deactivate_id: str = ""
    confirm_deactivate_name: str = ""

    @rx.event
    async def on_load(self):
        """Load accounts when the page is mounted."""
        await self._load_accounts()

    @rx.event
    async def handle_name_change(self, value: str):
        """Filter accounts by name — debounce handled in component."""
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
    async def deactivate_account(self, account_id: str):
        """Mark an account as inactive."""
        try:
            with await self.authenticate_user():
                from gws_care.account.account_service import AccountService
                AccountService.deactivate_account(account_id)
            await self._load_accounts()
        except Exception as e:
            self.error_message = f"Error deactivating account: {e}"

    @rx.event
    def open_confirm_deactivate(self, account_id: str, account_name: str):
        self.confirm_deactivate_id = account_id
        self.confirm_deactivate_name = account_name
        self.confirm_deactivate_open = True

    @rx.event
    def dismiss_confirm_deactivate(self):
        self.confirm_deactivate_open = False
        self.confirm_deactivate_id = ""
        self.confirm_deactivate_name = ""

    @rx.event
    async def confirmed_deactivate(self):
        account_id = self.confirm_deactivate_id
        self.confirm_deactivate_open = False
        self.confirm_deactivate_id = ""
        self.confirm_deactivate_name = ""
        await self.deactivate_account(account_id)

    async def _load_accounts(self):
        """Internal: fetch accounts from DB."""
        if not await self.check_authentication():
            self.error_message = "Authentication required"
            return

        self.is_loading = True
        self.error_message = ""

        try:
            with await self.authenticate_user():
                from gws_care.account.account_service import AccountService
                accounts = AccountService.list_accounts(active_only=False)
                if self.search_name.strip():
                    s = self.search_name.strip().lower()
                    accounts = [a for a in accounts if s in a.name.lower() or (a.city and s in a.city.lower()) or (a.contact_name and s in a.contact_name.lower())]
                account_rows = [
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
                self.accounts = sorted(
                    account_rows,
                    key=lambda row: "" if getattr(row, sort_col) is None else str(getattr(row, sort_col)).lower(),
                    reverse=not self.sort_ascending,
                )
        except Exception as e:
            self.error_message = f"Error loading accounts: {e}"
        finally:
            self.is_loading = False
