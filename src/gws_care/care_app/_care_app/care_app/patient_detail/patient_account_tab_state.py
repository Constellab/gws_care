"""State for the Accounts tab on the patient detail page."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class LinkedAccountRowDTO(BaseModel):
    account_id: str
    name: str = ""
    account_type: str = ""
    city: str = ""
    phone: str = ""
    is_active: bool = True


class AccountPickerRowDTO(BaseModel):
    id: str
    name: str = ""
    account_type: str = ""
    city: str = ""


class PatientAccountTabState(rx.State):
    """Manages the Accounts tab: list linked accounts, link/unlink."""

    linked_accounts: list[LinkedAccountRowDTO] = []
    is_loading: bool = False
    error_message: str = ""

    # Account picker
    picker_open: bool = False
    picker_filter: str = ""
    picker_rows: list[AccountPickerRowDTO] = []
    picker_is_loading: bool = False
    picker_error: str = ""

    _patient_id: str = ""

    # ── Load ─────────────────────────────────────────────────────────────────

    @rx.event
    async def load(self, patient_id: str):
        self._patient_id = patient_id
        await self._load_linked()

    # ── Picker ────────────────────────────────────────────────────────────────

    @rx.event
    async def open_picker(self):
        self.picker_filter = ""
        self.picker_error = ""
        self.picker_open = True
        await self._run_picker_search()

    @rx.event
    def close_picker(self):
        self.picker_open = False

    @rx.event
    async def set_picker_filter(self, value: str):
        self.picker_filter = value
        await self._run_picker_search()

    @rx.event
    async def link_account(self, account_id: str):
        self.picker_open = False
        try:
            _main = await self.get_state(ReflexMainState)
            with await _main.authenticate_user():
                from gws_care.patient.patient_service import PatientService
                PatientService.add_account(self._patient_id, account_id)
            await self._load_linked()
        except Exception as e:
            self.error_message = str(e)

    @rx.event
    async def unlink_account(self, account_id: str):
        try:
            _main = await self.get_state(ReflexMainState)
            with await _main.authenticate_user():
                from gws_care.patient.patient_service import PatientService
                PatientService.remove_account(self._patient_id, account_id)
            await self._load_linked()
        except Exception as e:
            self.error_message = str(e)

    # ── Internal loaders ─────────────────────────────────────────────────────

    async def _load_linked(self):
        if not self._patient_id:
            self.linked_accounts = []
            return
        self.is_loading = True
        self.error_message = ""
        try:
            _main = await self.get_state(ReflexMainState)
            with await _main.authenticate_user():
                from gws_care.patient.patient_account import PatientAccount
                links = list(PatientAccount.select().where(
                    PatientAccount.patient == self._patient_id
                ))
                rows = []
                for link in links:
                    try:
                        a = link.account
                        rows.append(LinkedAccountRowDTO(
                            account_id=str(a.id),
                            name=a.name or "",
                            account_type=a.account_type or "COMPANY",
                            city=a.city or "",
                            phone=a.phone or "",
                            is_active=bool(a.is_active),
                        ))
                    except Exception:
                        pass
                self.linked_accounts = rows
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_loading = False

    async def _run_picker_search(self):
        self.picker_is_loading = True
        self.picker_error = ""
        already_linked = {a.account_id for a in self.linked_accounts}
        try:
            _main = await self.get_state(ReflexMainState)
            with await _main.authenticate_user():
                from gws_care.account.account_service import AccountService
                accounts = AccountService.list_accounts(active_only=True)
                f = self.picker_filter.strip().lower()
                self.picker_rows = [
                    AccountPickerRowDTO(
                        id=str(a.id),
                        name=a.name or "",
                        account_type=a.account_type or "COMPANY",
                        city=a.city or "",
                    )
                    for a in accounts
                    if str(a.id) not in already_linked
                    and a.account_type == "COMPANY"
                    and (not f or f in (a.name or "").lower() or f in (a.city or "").lower())
                ]
        except Exception as e:
            self.picker_error = str(e)
        finally:
            self.picker_is_loading = False
