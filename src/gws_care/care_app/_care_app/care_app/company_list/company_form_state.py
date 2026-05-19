"""State for the company create / edit form dialog."""

from typing import AsyncGenerator

import reflex as rx
from gws_reflex_base import FormDialogState
from gws_reflex_main import ReflexMainState


class CompanyFormState(FormDialogState, rx.State):
    """Manages the create / update company dialog."""

    # Form fields (public — bound to inputs in the UI)
    form_name: str = ""
    form_registration_number: str = ""
    form_address: str = ""
    form_postal_code: str = ""
    form_city: str = ""
    form_phone: str = ""
    form_email: str = ""
    form_contact_name: str = ""

    # Set when editing an existing company
    _editing_company_id: str = ""

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
        self._editing_company_id = ""
        await self._clear_form_state()
        self.dialog_opened = True

    @rx.event
    async def open_edit_dialog(self, company_id: str):
        """Open the dialog in edit mode pre-filled with the company's data.

        :param company_id: DB id of the company to edit
        :type company_id: str
        """
        self.is_update_mode = True
        self._editing_company_id = company_id

        _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            from gws_care.company.company_service import CompanyService
            c = CompanyService.get_company(company_id)
            self.form_name = c.name or ""
            self.form_registration_number = c.registration_number or ""
            self.form_address = c.address or ""
            self.form_postal_code = c.postal_code or ""
            self.form_city = c.city or ""
            self.form_phone = c.phone or ""
            self.form_email = c.email or ""
            self.form_contact_name = c.contact_name or ""

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
        self._editing_company_id = ""
        self.is_update_mode = False

    async def _create(self, form_data: dict) -> AsyncGenerator:
        """Create a new company from form data."""
        from gws_care.company.company_dto import SaveCompanyDTO
        from gws_care.company.company_service import CompanyService

        name = self.form_name.strip()
        if not name:
            yield rx.toast.error("Company name is required")
            return
        if not self.form_email.strip():
            yield rx.toast.error("L'email du responsable est obligatoire")
            return

        dto = SaveCompanyDTO(
            name=name,
            registration_number=self.form_registration_number or None,
            address=self.form_address or None,
            postal_code=self.form_postal_code or None,
            city=self.form_city or None,
            phone=self.form_phone or None,
            email=self.form_email.strip(),
            contact_name=self.form_contact_name or None,
        )

        async with self:
            _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            company = CompanyService.create_company(dto)

        yield rx.toast.success(f"Company '{company.name}' created")

        from ..company_list.company_list_state import CompanyListState
        yield CompanyListState.on_load()

    async def _update(self, form_data: dict) -> AsyncGenerator:
        """Update an existing company from form data."""
        from gws_care.company.company_dto import SaveCompanyDTO
        from gws_care.company.company_service import CompanyService

        name = self.form_name.strip()
        if not name:
            yield rx.toast.error("Company name is required")
            return
        if not self.form_email.strip():
            yield rx.toast.error("L'email du responsable est obligatoire")
            return

        dto = SaveCompanyDTO(
            name=name,
            registration_number=self.form_registration_number or None,
            address=self.form_address or None,
            postal_code=self.form_postal_code or None,
            city=self.form_city or None,
            phone=self.form_phone or None,
            email=self.form_email.strip(),
            contact_name=self.form_contact_name or None,
        )

        async with self:
            _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            CompanyService.update_company(self._editing_company_id, dto)

        yield rx.toast.success("Entreprise mise à jour avec succès")

        from ..company_list.company_list_state import CompanyListState
        from ..company_detail.company_detail_state import CompanyDetailState
        yield CompanyListState.on_load()
        yield CompanyDetailState.on_load()
