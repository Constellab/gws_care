"""State for General settings tab (app-wide configuration)."""

import reflex as rx

from ..common.role_state import RoleState


class GeneralSettingsState(RoleState):
    """State for the General settings tab — manages app-wide config like list page size."""

    page_size: str = "50"
    is_saving_page_size: bool = False
    save_page_size_success: str = ""
    save_page_size_error: str = ""

    @rx.event
    async def on_load(self):
        try:
            with await self.authenticate_user():
                from gws_care.core.care_app_config_service import CareAppConfigService
                self.page_size = str(CareAppConfigService.get_page_size())
        except Exception:
            self.page_size = "50"

    @rx.event
    def set_page_size(self, value: str):
        self.page_size = value
        self.save_page_size_success = ""
        self.save_page_size_error = ""

    @rx.event
    async def save_page_size_setting(self):
        self.is_saving_page_size = True
        self.save_page_size_success = ""
        self.save_page_size_error = ""
        try:
            with await self.authenticate_user():
                from gws_care.core.care_app_config_service import CareAppConfigService
                CareAppConfigService.save_page_size(int(self.page_size))
            self.save_page_size_success = "Saved."
        except Exception as e:
            self.save_page_size_error = f"Error: {e}"
        finally:
            self.is_saving_page_size = False
