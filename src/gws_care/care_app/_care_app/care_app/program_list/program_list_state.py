"""State for the program list page."""

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


class ProgramRowDTO(BaseModel):
    """MedicalProgram row for list display."""

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


class AccountOptionDTO(BaseModel):
    id: str
    name: str


class ProgramListState(RoleState):
    """State for the /programs page."""

    programs: list[ProgramRowDTO] = []
    account_options: list[AccountOptionDTO] = []
    is_loading: bool = False
    error_message: str = ""

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
    form_account_id: str = ""
    form_start_date: str = ""
    form_end_date: str = ""
    form_notes: str = ""
    is_saving: bool = False
    form_error: str = ""

    @rx.event
    async def on_load(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_operator, self.is_doctor, self.is_admin)
        if redirect:
            return redirect
        await self._load_accounts()
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
        return rx.redirect(f"/program/{program_id}")

    @rx.event
    async def archive_program(self, program_id: str):
        try:
            with await self.authenticate_user():
                from gws_care.medical_program.medical_program_service import MedicalProgramService
                MedicalProgramService.archive_program(program_id)
            await self._load_programs()
        except Exception as e:
            self.error_message = str(e)

    # ── Create dialog ─────────────────────────────────────────────────────────

    @rx.event
    def open_create_dialog(self):
        self.create_dialog_open = True
        self.form_name = ""
        self.form_account_id = ""
        self.form_start_date = ""
        self.form_end_date = ""
        self.form_notes = ""
        self.form_error = ""

    @rx.event
    def close_create_dialog(self):
        self.create_dialog_open = False
        self.form_error = ""

    @rx.event
    def set_form_name(self, value: str):
        self.form_name = value

    @rx.event
    def set_form_account_id(self, value: str):
        self.form_account_id = value

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
        if not self.form_name.strip() or not self.form_account_id or not self.form_start_date or not self.form_end_date:
            self.form_error = "Please fill in all required fields."
            return
        self.is_saving = True
        self.form_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.medical_program.medical_program_dto import SaveProgramDTO
                from gws_care.medical_program.medical_program_service import MedicalProgramService
                dto = SaveProgramDTO(
                    name=self.form_name.strip(),
                    account_id=self.form_account_id,
                    start_date=self.form_start_date,
                    end_date=self.form_end_date,
                    notes=self.form_notes or None,
                )
                program = MedicalProgramService.create_program(dto)
            self.create_dialog_open = False
            await self._load_programs()
            return rx.redirect(f"/program/{program.id}")
        except Exception as e:
            self.form_error = str(e)
        finally:
            self.is_saving = False

    # ── Internal loaders ──────────────────────────────────────────────────────

    async def _load_accounts(self):
        if not await self.check_authentication():
            return
        try:
            with await self.authenticate_user():
                from gws_care.account.account_service import AccountService
                accounts = AccountService.list_accounts(active_only=True)
                self.account_options = [
                    AccountOptionDTO(id=str(a.id), name=a.name) for a in accounts
                ]
        except Exception as e:
            self.error_message = str(e)

    async def _load_programs(self):
        if not await self.check_authentication():
            return
        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.medical_program.medical_program_service import MedicalProgramService
                from gws_care.medical_program.program_status import ProgramStatus

                status_filter = None
                if self.filter_status != "ALL":
                    try:
                        status_filter = ProgramStatus(self.filter_status)
                    except ValueError:
                        pass

                programs = MedicalProgramService.list_programs(
                    account_id=self.filter_account_id or None,
                    status=status_filter,
                    search=self.search_name,
                )
                rows = [
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
                        patient_count=MedicalProgramService.to_row_dto(c).patient_count,
                        exam_type_count=MedicalProgramService.to_row_dto(c).exam_type_count,
                    )
                    for c in programs
                ]
                sort_col = self.sort_column
                self.programs = sorted(
                    rows,
                    key=lambda row: (getattr(row, sort_col) or "").lower(),
                    reverse=not self.sort_ascending,
                )
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_loading = False
