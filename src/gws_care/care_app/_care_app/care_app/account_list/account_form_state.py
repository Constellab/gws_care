"""State for the account create / edit form dialog."""

from typing import AsyncGenerator

import reflex as rx
from gws_reflex_base import FormDialogState
from gws_reflex_main import ReflexMainState


class AccountFormState(FormDialogState, rx.State):
    """Manages the create / update account dialog."""

    # Form fields (public — bound to inputs in the UI)
    form_name: str = ""
    form_registration_number: str = ""
    form_address: str = ""
    form_postal_code: str = ""
    form_city: str = ""
    form_phone: str = ""
    form_email: str = ""
    form_contact_name: str = ""

    # Set when editing an existing account
    _editing_account_id: str = ""

    # ── Setters ───────────────────────────────────────────────────────────────

    @rx.event
    def set_form_name(self, value: str):
        self.form_name = value

    @rx.event
    def set_form_registration_number(self, value: str):
        self.form_registration_number = value

    @rx.event
    def set_form_address(self, value: str):
        self.form_address = value

    @rx.event
    def set_form_postal_code(self, value: str):
        self.form_postal_code = value

    @rx.event
    def set_form_city(self, value: str):
        self.form_city = value

    @rx.event
    def set_form_phone(self, value: str):
        self.form_phone = value

    @rx.event
    def set_form_email(self, value: str):
        self.form_email = value

    @rx.event
    def set_form_contact_name(self, value: str):
        self.form_contact_name = value

    # ── Dialog open helpers ───────────────────────────────────────────────────

    @rx.event
    async def open_create_dialog(self):
        """Open the dialog in create mode."""
        self.is_update_mode = False
        self._editing_account_id = ""
        await self._clear_form_state()
        self.dialog_opened = True

    @rx.event
    async def open_edit_dialog(self, account_id: str):
        """Open the dialog in edit mode pre-filled with the account's data.

        :param account_id: DB id of the account to edit
        :type account_id: str
        """
        self.is_update_mode = True
        self._editing_account_id = account_id

        _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            from gws_care.account.account_service import AccountService
            a = AccountService.get_account(account_id)
            self.form_name = a.name or ""
            self.form_registration_number = a.registration_number or ""
            self.form_address = a.address or ""
            self.form_postal_code = a.postal_code or ""
            self.form_city = a.city or ""
            self.form_phone = a.phone or ""
            self.form_email = a.email or ""
            self.form_contact_name = a.contact_name or ""

        self.dialog_opened = True

    # ── FormDialogState abstract method implementations ───────────────────────

    async def _clear_form_state(self) -> None:
        self.form_name = ""
        self.form_registration_number = ""
        self.form_address = ""
        self.form_postal_code = ""
        self.form_city = ""
        self.form_phone = ""
        self.form_email = ""
        self.form_contact_name = ""
        self._editing_account_id = ""
        self.is_update_mode = False

    async def _create(self, form_data: dict) -> AsyncGenerator:
        """Create a new account from form data."""
        from gws_care.account.account_dto import SaveAccountDTO
        from gws_care.account.account_service import AccountService

        name = self.form_name.strip()
        if not name:
            yield rx.toast.error("Account name is required")
            return

        dto = SaveAccountDTO(
            name=name,
            registration_number=self.form_registration_number or None,
            address=self.form_address or None,
            postal_code=self.form_postal_code or None,
            city=self.form_city or None,
            phone=self.form_phone or None,
            email=self.form_email or None,
            contact_name=self.form_contact_name or None,
        )

        async with self:
            _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            account = AccountService.create_account(dto)

        yield rx.toast.success(f"Account '{account.name}' created")

        from ..account_list.account_list_state import AccountListState
        yield AccountListState.on_load()

    async def _update(self, form_data: dict) -> AsyncGenerator:
        """Update an existing account from form data."""
        from gws_care.account.account_dto import SaveAccountDTO
        from gws_care.account.account_service import AccountService

        name = self.form_name.strip()
        if not name:
            yield rx.toast.error("Account name is required")
            return

        dto = SaveAccountDTO(
            name=name,
            registration_number=self.form_registration_number or None,
            address=self.form_address or None,
            postal_code=self.form_postal_code or None,
            city=self.form_city or None,
            phone=self.form_phone or None,
            email=self.form_email or None,
            contact_name=self.form_contact_name or None,
        )

        async with self:
            _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            AccountService.update_account(self._editing_account_id, dto)

        yield rx.toast.success("Account updated successfully")

        from ..account_list.account_list_state import AccountListState
        yield AccountListState.on_load()
