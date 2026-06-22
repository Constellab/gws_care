"""Reusable account picker state — filter + table, then select one account."""

from __future__ import annotations

import reflex as rx
from pydantic import BaseModel

from .role_state import RoleState


class AccountPickerRowDTO(BaseModel):
    id: str
    name: str
    account_type: str = ""
    city: str | None = None
    phone: str | None = None


class AccountPickerState(RoleState):
    """Mixin state for picking an account from a filterable table dialog.

    Each subclass MUST declare the following vars in its own class body so
    Reflex stores them in a separate state node (prevents cross-page sharing):

        acct_picker_is_open: bool = False
        acct_picker_filter: str = ""
        acct_picker_accounts: list[AccountPickerRowDTO] = []
        acct_picker_is_loading: bool = False
        acct_picker_error: str = ""
        acct_picker_selected_id: str = ""
        acct_picker_selected_name: str = ""

    Usage pattern
    -------------
    1. Inherit this class and declare the vars above in the subclass.
    2. Override ``_on_account_picked(account_id)`` to react when an account
       is selected (update ``filter_account_id``, reload data, etc.).
    3. Add ``account_picker_dialog()`` to the page component.
    4. Render ``account_picker_button()`` where the filter trigger should appear.
    """

    # ── Dialog lifecycle (private — subclasses expose these as @rx.event) ─────

    async def _open_account_picker(self):
        """Open the account picker dialog and load initial list."""
        self.acct_picker_filter = ""
        self.acct_picker_error = ""
        self.acct_picker_is_open = True
        await self._run_acct_picker_search()

    # ── Filter ────────────────────────────────────────────────────────────────

    async def _acct_picker_set_filter(self, value: str):
        self.acct_picker_filter = value
        await self._run_acct_picker_search()

    # ── Selection ─────────────────────────────────────────────────────────────

    async def _acct_picker_confirm(self, account_id: str, name: str):
        """Select an account and close the dialog."""
        self.acct_picker_selected_id = account_id
        self.acct_picker_selected_name = name
        self.acct_picker_is_open = False
        await self._on_account_picked(account_id)

    async def _acct_picker_clear(self):
        """Clear the current account selection."""
        self.acct_picker_selected_id = ""
        self.acct_picker_selected_name = ""
        await self._on_account_picked("")

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _on_account_picked(self, account_id: str) -> None:
        """Hook called after selection changes. Override to react to selection."""

    async def _run_acct_picker_search(self) -> None:
        """Load / filter the account list."""
        self.acct_picker_is_loading = True
        self.acct_picker_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.account.account_service import AccountService
                accounts = AccountService.list_accounts(active_only=False)
                name_filter = self.acct_picker_filter.strip().lower()
                if name_filter:
                    accounts = [a for a in accounts if name_filter in a.name.lower()]
                self.acct_picker_accounts = [
                    AccountPickerRowDTO(
                        id=str(a.id),
                        name=a.name,
                        account_type=a.account_type or "",
                        city=a.city,
                        phone=a.phone,
                    )
                    for a in accounts
                ]
        except Exception as e:
            self.acct_picker_error = str(e)
        finally:
            self.acct_picker_is_loading = False
