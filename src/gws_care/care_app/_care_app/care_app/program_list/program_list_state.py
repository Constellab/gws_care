"""State for the program list page."""

import reflex as rx
from pydantic import BaseModel

from ..common.account_picker_state import AccountPickerRowDTO, AccountPickerState


class ProgramRowDTO(BaseModel):
    """Campaign row for list display."""

    id: str
    program_number: str
    name: str
    account_name: str = ""
    account_id: str = ""
    start_date: str
    end_date: str
    status: str
    status_label: str
    patient_count: int = 0
    exam_type_count: int = 0


class CampaignFormPickerState(AccountPickerState):
    """Sibling account picker for the create-program form.

    Fully self-contained: stores the confirmed form account in its own vars.
    ProgramListState.save_program reads them via get_state(ProgramFormPickerState).
    """

    # ── Account picker vars (declared here for independent state storage) ─────
    acct_picker_is_open: bool = False
    acct_picker_filter: str = ""
    acct_picker_accounts: list[AccountPickerRowDTO] = []
    acct_picker_is_loading: bool = False
    acct_picker_error: str = ""
    acct_picker_selected_id: str = ""
    acct_picker_selected_name: str = ""

    # Form account result — written by _on_account_picked on self
    form_account_id: str = ""
    form_account_name: str = ""

    async def _on_account_picked(self, account_id: str) -> None:
        """Store confirmed selection in own vars — no cross-sibling write needed."""
        self.form_account_id = account_id
        self.form_account_name = self.acct_picker_selected_name

    # ── Account picker events ─────────────────────────────────────────────────────

    @rx.event
    async def open_account_picker(self):
        await self._open_account_picker()

    @rx.event
    def close_account_picker(self):
        self.acct_picker_is_open = False

    @rx.event
    async def acct_picker_set_filter(self, value: str):
        await self._acct_picker_set_filter(value)

    @rx.event
    async def acct_picker_confirm(self, account_id: str, name: str):
        await self._acct_picker_confirm(account_id, name)

    @rx.event
    async def acct_picker_clear(self):
        await self._acct_picker_clear()

    @rx.event
    def clear_form_account(self):
        self.form_account_id = ""
        self.form_account_name = ""
        self.acct_picker_selected_id = ""
        self.acct_picker_selected_name = ""

    @rx.event
    def reset_form_picker(self):
        self.form_account_id = ""
        self.form_account_name = ""
        self.acct_picker_selected_id = ""
        self.acct_picker_selected_name = ""
        self.acct_picker_filter = ""
        self.acct_picker_accounts = []
        self.acct_picker_is_open = False

    @rx.event
    async def load_accounts(self):
        """Load the account list into the inline picker without opening a dialog."""
        self.acct_picker_filter = ""
        self.acct_picker_error = ""
        await self._run_acct_picker_search()


class CampaignListState(AccountPickerState):
    """State for the /programs page."""

    # ── Account picker vars (declared here for independent state storage) ─────
    acct_picker_is_open: bool = False
    acct_picker_filter: str = ""
    acct_picker_accounts: list[AccountPickerRowDTO] = []
    acct_picker_is_loading: bool = False
    acct_picker_error: str = ""
    acct_picker_selected_id: str = ""
    acct_picker_selected_name: str = ""

    programs: list[ProgramRowDTO] = []
    is_loading: bool = False
    is_loading_more: bool = False
    has_more: bool = False
    error_message: str = ""

    _page_offset: int = 0
    _current_page_size: int = 50

    # Filters
    filter_account_id: str = ""
    filter_status: str = "ALL"
    search_name: str = ""

    # Sorting
    sort_column: str = "start_date"
    sort_ascending: bool = False

    # Create dialog
    create_dialog_open: bool = False
    form_name: str = ""
    form_start_date: str = ""
    form_end_date: str = ""
    form_notes: str = ""
    is_saving: bool = False
    form_error: str = ""

    # ── Account picker events ─────────────────────────────────────────────────────

    @rx.event
    async def open_account_picker(self):
        await self._open_account_picker()

    @rx.event
    def close_account_picker(self):
        self.acct_picker_is_open = False

    @rx.event
    async def acct_picker_set_filter(self, value: str):
        await self._acct_picker_set_filter(value)

    @rx.event
    async def acct_picker_confirm(self, account_id: str, name: str):
        await self._acct_picker_confirm(account_id, name)

    @rx.event
    async def acct_picker_clear(self):
        await self._acct_picker_clear()

    @rx.event
    async def on_load(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_operator, self.is_doctor, self.is_admin)
        if redirect:
            return redirect
        await self._load_programs()

    async def _on_account_picked(self, account_id: str) -> None:
        self.filter_account_id = account_id
        await self._load_programs()

    @rx.event
    async def set_filter_account(self, value: str):
        self.filter_account_id = value if value != "ALL" else ""
        await self._load_programs()

    @rx.event
    async def set_filter_status(self, value: str):
        self.filter_status = value
        await self._load_programs()

    @rx.event
    async def set_search_name(self, value: str):
        self.search_name = value
        await self._load_programs()

    @rx.event
    async def set_sort(self, column: str):
        """Sort by column; toggle direction if already sorted by the same column."""
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column
            self.sort_ascending = True
        await self._load_programs()

    @rx.event
    def go_to_program(self, program_id: str):
        return rx.redirect(f"/campaign/{program_id}")

    @rx.event
    async def archive_program(self, program_id: str):
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                CampaignService.archive_campaign(program_id)
            await self._load_programs()
        except Exception as e:
            self.error_message = str(e)

    @rx.event
    async def load_more_programs(self):
        """Append the next page of programs to the current list."""
        self.is_loading_more = True
        await self._load_programs(reset=False)

    # ── Create dialog ─────────────────────────────────────────────────────────

    @rx.event
    def open_create_dialog(self):
        self.create_dialog_open = True
        self.form_name = ""
        self.form_start_date = ""
        self.form_end_date = ""
        self.form_notes = ""
        self.form_error = ""
        yield CampaignFormPickerState.reset_form_picker
        yield CampaignFormPickerState.load_accounts

    @rx.event
    def close_create_dialog(self):
        self.create_dialog_open = False
        self.form_error = ""

    @rx.event
    def set_form_name(self, value: str):
        self.form_name = value

    @rx.event
    def set_form_start_date(self, value: str):
        self.form_start_date = value

    @rx.event
    def set_form_end_date(self, value: str):
        self.form_end_date = value

    @rx.event
    def set_form_notes(self, value: str):
        self.form_notes = value

    @rx.event
    async def save_program(self):
        form_picker = await self.get_state(CampaignFormPickerState)
        form_account_id = form_picker.form_account_id
        if not self.form_name.strip() or not form_account_id or not self.form_start_date or not self.form_end_date:
            self.form_error = "Please fill in all required fields."
            return
        self.is_saving = True
        self.form_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_dto import SaveCampaignDTO
                from gws_care.campaign.campaign_service import CampaignService
                dto = SaveCampaignDTO(
                    name=self.form_name.strip(),
                    account_id=form_account_id,
                    start_date=self.form_start_date,
                    end_date=self.form_end_date,
                    notes=self.form_notes or None,
                )
                program = CampaignService.create_campaign(dto)
            self.create_dialog_open = False
            await self._load_programs()
            return rx.redirect(f"/campaign/{program.id}")
        except Exception as e:
            self.form_error = str(e)
        finally:
            self.is_saving = False

    # ── Internal loaders ──────────────────────────────────────────────────────

    async def _load_programs(self, reset: bool = True):
        if not await self.check_authentication():
            return
        if reset:
            self._page_offset = 0
            self.is_loading = True
            from gws_care.core.care_app_config_service import CareAppConfigService
            self._current_page_size = CareAppConfigService.get_page_size()
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.campaign.campaign_service import CampaignService
                from gws_care.campaign.campaign_status import CampaignStatus

                status_filter = None
                if self.filter_status != "ALL":
                    try:
                        status_filter = CampaignStatus(self.filter_status)
                    except ValueError:
                        pass

                programs = CampaignService.list_campaigns(
                    account_id=self.filter_account_id or None,
                    status=status_filter,
                    search=self.search_name,
                    limit=self._current_page_size + 1,
                    offset=self._page_offset,
                )
                has_more = len(programs) > self._current_page_size
                programs = programs[:self._current_page_size]
                new_rows = [
                    ProgramRowDTO(
                        id=str(c.id),
                        program_number=c.program_number,
                        name=c.name,
                        account_name=c.account.name if c.account_id else "",
                        account_id=str(c.account_id) if c.account_id else "",
                        start_date=str(c.start_date),
                        end_date=str(c.end_date),
                        status=c.status.value,
                        status_label=c.status.get_label(),
                        patient_count=CampaignService.to_row_dto(c).patient_count,
                        exam_type_count=CampaignService.to_row_dto(c).exam_type_count,
                    )
                    for c in programs
                ]
                sort_col = self.sort_column
                all_rows = new_rows if reset else self.programs + new_rows
                self.programs = sorted(
                    all_rows,
                    key=lambda row: (getattr(row, sort_col) or "").lower(),
                    reverse=not self.sort_ascending,
                )
                self.has_more = has_more
                self._page_offset += self._current_page_size
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_loading = False
            self.is_loading_more = False

