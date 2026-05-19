"""State management for the company list page."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class CompanyRowDTO(BaseModel):
    """Lightweight DTO for displaying a company in the list."""

    id: str
    name: str
    city: str | None = None
    phone: str | None = None
    email: str | None = None
    contact_name: str | None = None
    is_active: bool = True


class CompanyListState(ReflexMainState):
    """State for the company list page."""

    companies: list[CompanyRowDTO] = []
    is_loading: bool = False
    error_message: str = ""
    search_name: str = ""

    # Confirm désactivation
    confirm_deactivate_open: bool = False
    confirm_deactivate_id: str = ""
    confirm_deactivate_name: str = ""

    @rx.event
    async def on_load(self):
        """Load companies when the page is mounted."""
        await self._load_companies()

    @rx.event
    async def handle_name_change(self, value: str):
        """Filter companies by name."""
        self.search_name = value
        await self._load_companies()

    @rx.event
    async def clear_filters(self):
        """Reset filters."""
        self.search_name = ""
        await self._load_companies()

    @rx.event
    def go_to_company(self, company_id: str):
        """Navigate to the company detail page."""
        return rx.redirect(f"/company/{company_id}")

    @rx.event
    async def deactivate_company(self, company_id: str):
        """Mark a company as inactive."""
        try:
            with await self.authenticate_user():
                from gws_care.company.company_service import CompanyService
                CompanyService.deactivate_company(company_id)
            await self._load_companies()
        except Exception as e:
            self.error_message = f"Error deactivating company: {e}"

    @rx.event
    def open_confirm_deactivate(self, company_id: str, company_name: str):
        self.confirm_deactivate_id = company_id
        self.confirm_deactivate_name = company_name
        self.confirm_deactivate_open = True

    @rx.event
    def dismiss_confirm_deactivate(self):
        self.confirm_deactivate_open = False
        self.confirm_deactivate_id = ""
        self.confirm_deactivate_name = ""

    @rx.event
    async def confirmed_deactivate(self):
        company_id = self.confirm_deactivate_id
        self.confirm_deactivate_open = False
        self.confirm_deactivate_id = ""
        self.confirm_deactivate_name = ""
        await self.deactivate_company(company_id)

    async def _load_companies(self):
        """Internal: fetch companies from DB."""
        if not await self.check_authentication():
            self.error_message = "Authentication required"
            return

        self.is_loading = True
        self.error_message = ""

        try:
            with await self.authenticate_user():
                from gws_care.company.company_service import CompanyService
                companies = CompanyService.list_companies(active_only=False)
                filtered = [
                    c for c in companies
                    if not self.search_name or self.search_name.lower() in c.name.lower()
                ]
                self.companies = [
                    CompanyRowDTO(
                        id=str(c.id),
                        name=c.name,
                        city=c.city,
                        phone=c.phone,
                        email=c.email,
                        contact_name=c.contact_name,
                        is_active=c.is_active,
                    )
                    for c in filtered
                ]
        except Exception as e:
            self.error_message = f"Error loading companies: {e}"
        finally:
            self.is_loading = False
