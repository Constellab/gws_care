"""State for the My Accounts patient portal page (/my-patient-accounts).

Shows accounts associated with the logged-in patient.
Patients can create or edit personal (INDIVIDUAL) accounts.
Enterprise (COMPANY) accounts are read-only.
"""

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


class PatientAccountRowDTO(BaseModel):
    id: str
    name: str = ""
    account_type: str = ""
    city: str = ""
    phone: str = ""
    email: str = ""
    contact_name: str = ""
    is_active: bool = True


class PatientAccountsState(RoleState):
    """State for the /my-patient-accounts page."""

    accounts: list[PatientAccountRowDTO] = []
    is_loading: bool = False
    error_message: str = ""

    # Sorting
    sort_column: str = "name"
    sort_ascending: bool = True

    # Create/edit form dialog
    form_dialog_open: bool = False
    form_is_edit_mode: bool = False
    form_name: str = ""
    form_address: str = ""
    form_postal_code: str = ""
    form_city: str = ""
    form_phone: str = ""
    form_email: str = ""
    form_is_loading: bool = False
    form_error_message: str = ""

    _editing_account_id: str = ""

    # ── Page guard ────────────────────────────────────────────────────────

    @rx.event
    async def on_load(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_patient_user, redirect_to="/dashboard")
        if redirect:
            return redirect
        await self._load_accounts()

    # ── Sorting ───────────────────────────────────────────────────────────

    @rx.event
    def set_sort(self, column: str):
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column
            self.sort_ascending = True
        self.accounts = sorted(
            self.accounts,
            key=lambda row: "" if getattr(row, column) is None else str(getattr(row, column)).lower(),
            reverse=not self.sort_ascending,
        )

    # ── Form dialog — open/close ──────────────────────────────────────────

    @rx.event
    def open_create_dialog(self):
        self._editing_account_id = ""
        self.form_is_edit_mode = False
        self.form_name = ""
        self.form_address = ""
        self.form_postal_code = ""
        self.form_city = ""
        self.form_phone = ""
        self.form_email = ""
        self.form_error_message = ""
        self.form_dialog_open = True

    @rx.event
    async def open_edit_dialog(self, account_id: str):
        """Pre-fill the form with existing INDIVIDUAL account data."""
        self._editing_account_id = account_id
        self.form_is_edit_mode = True
        self.form_error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.account.account_service import AccountService
                acct = AccountService.get_account(account_id)
                self.form_name = acct.name or ""
                self.form_address = acct.address or ""
                self.form_postal_code = acct.postal_code or ""
                self.form_city = acct.city or ""
                self.form_phone = acct.phone or ""
                self.form_email = acct.email or ""
        except Exception as e:
            self.form_error_message = str(e)
            return
        self.form_dialog_open = True

    @rx.event
    def close_dialog(self):
        self.form_dialog_open = False

    # ── Form field setters ────────────────────────────────────────────────

    @rx.event
    def set_form_name(self, value: str):
        self.form_name = value

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

    # ── Submit (create or update) ─────────────────────────────────────────

    @rx.event
    async def submit_account_form(self, form_data: dict):
        """Create or update an INDIVIDUAL account."""
        name = self.form_name.strip()
        if not name:
            self.form_error_message = "Name is required"
            return

        self.form_is_loading = True
        self.form_error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.account.account_dto import SaveAccountDTO
                from gws_care.account.account_service import AccountService

                dto = SaveAccountDTO(
                    account_type="INDIVIDUAL",
                    name=name,
                    address=self.form_address or None,
                    postal_code=self.form_postal_code or None,
                    city=self.form_city or None,
                    phone=self.form_phone or None,
                    email=self.form_email or None,
                    contact_name=None,
                    registration_number=None,
                )

                if self.form_is_edit_mode:
                    AccountService.update_account(self._editing_account_id, dto)
                    msg = f"Account '{name}' updated"
                else:
                    from gws_care.patient.patient_account import PatientAccount
                    account = AccountService.create_account(dto)
                    patient_id = self._linked_patient_id
                    if patient_id:
                        link = PatientAccount()
                        link.patient = patient_id
                        link.account = account.id
                        link.save()
                    msg = f"Account '{name}' created"

            self.form_dialog_open = False
            yield rx.toast.success(msg)
            await self._load_accounts()
        except Exception as e:
            self.form_error_message = str(e)
        finally:
            self.form_is_loading = False

    # ── Data loader ────────────────────────────────────────────────────────

    async def _load_accounts(self):
        if not await self.check_authentication():
            return
        patient_id = self._linked_patient_id
        if not patient_id:
            self.accounts = []
            return

        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.patient.patient_account import PatientAccount
                links = list(
                    PatientAccount.select().where(PatientAccount.patient == patient_id)
                )
                rows = []
                for link in links:
                    try:
                        acct = link.account
                        rows.append(PatientAccountRowDTO(
                            id=str(acct.id),
                            name=acct.name or "",
                            account_type=acct.account_type or "COMPANY",
                            city=acct.city or "",
                            phone=acct.phone or "",
                            email=acct.email or "",
                            contact_name=acct.contact_name or "",
                            is_active=bool(acct.is_active),
                        ))
                    except Exception:
                        pass
                self.accounts = sorted(
                    rows,
                    key=lambda row: str(getattr(row, self.sort_column) or "").lower(),
                    reverse=not self.sort_ascending,
                )
        except Exception as e:
            self.error_message = f"Error loading accounts: {e}"
        finally:
            self.is_loading = False
