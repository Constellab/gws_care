"""State for General settings tab (app-wide configuration)."""

import reflex as rx

from ..common.role_state import RoleState

# CSS variable overrides for non-default themes (Constellab palette)
_PINK_CSS = """.radix-themes {
  --accent-1: #fff4fa; --accent-2: #ffe9f6; --accent-3: #ffdff1;
  --accent-4: #ffd4ec; --accent-5: #ffbee3; --accent-6: #ffa9d9;
  --accent-7: #ff93d0; --accent-8: #e176b2; --accent-9: #c35895;
  --accent-10: #a63b77; --accent-11: #972c68; --accent-12: #881d5a;
  --accent-surface: #fff4fa; --accent-indicator: #c35895;
  --accent-track: #c35895; --accent-contrast: #ffffff;
}"""

_PURPLE_CSS = """.radix-themes {
  --accent-1: #f9f8fd; --accent-2: #f3f1fc; --accent-3: #eeebfa;
  --accent-4: #e8e4f8; --accent-5: #dcd6f5; --accent-6: #d1c9f1;
  --accent-7: #c5bbee; --accent-8: #a69bd3; --accent-9: #877bb8;
  --accent-10: #675a9d; --accent-11: #584a90; --accent-12: #483a82;
  --accent-surface: #f9f8fd; --accent-indicator: #877bb8;
  --accent-track: #877bb8; --accent-contrast: #ffffff;
}"""


class GeneralSettingsState(RoleState):
    """State for the General settings tab — manages app-wide config like list page size."""

    page_size: str = "50"
    is_saving_page_size: bool = False
    save_page_size_success: str = ""
    save_page_size_error: str = ""

    color_theme: str = "green"
    is_saving_theme: bool = False
    save_theme_success: str = ""
    save_theme_error: str = ""

    @rx.var
    def theme_css(self) -> str:
        """CSS variable overrides for the active color theme."""
        if self.color_theme == "pink":
            return _PINK_CSS
        if self.color_theme == "purple":
            return _PURPLE_CSS
        return ""  # green is the default — no override needed

    @rx.event
    async def on_load(self):
        try:
            with await self.authenticate_user():
                from gws_care.core.care_app_config_service import CareAppConfigService
                self.page_size = str(CareAppConfigService.get_page_size())
                self.color_theme = CareAppConfigService.get_color_theme()
        except Exception:
            self.page_size = "50"
            self.color_theme = "green"

    @rx.event
    async def load_color_theme(self):
        """Lightweight event to load only the color theme (called on every page)."""
        try:
            with await self.authenticate_user():
                from gws_care.core.care_app_config_service import CareAppConfigService
                self.color_theme = CareAppConfigService.get_color_theme()
        except Exception:
            self.color_theme = "green"

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
            self.save_page_size_success = "Enregistré."
        except Exception as e:
            self.save_page_size_error = f"Erreur : {e}"
        finally:
            self.is_saving_page_size = False

    @rx.event
    async def set_color_theme(self, theme: str):
        """Set and immediately persist the color theme."""
        self.color_theme = theme
        self.save_theme_success = ""
        self.save_theme_error = ""
        self.is_saving_theme = True
        try:
            with await self.authenticate_user():
                from gws_care.core.care_app_config_service import CareAppConfigService
                CareAppConfigService.save_color_theme(theme)
            self.save_theme_success = "Enregistré."
        except Exception as e:
            self.save_theme_error = f"Erreur : {e}"
        finally:
            self.is_saving_theme = False
