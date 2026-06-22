"""Service for reading and updating the singleton CareAppConfig row."""

_DEFAULT_PAGE_SIZE = 50
VALID_PAGE_SIZES = [10, 25, 50, 100, 200]
VALID_THEMES = ["green", "pink", "purple"]


class CareAppConfigService:
    """Read/write the singleton CareAppConfig row (no auth context required)."""

    @classmethod
    def get_page_size(cls) -> int:
        try:
            from gws_care.core.care_app_config import CareAppConfig
            config = CareAppConfig.get_or_none()
            if config is None:
                CareAppConfig.insert(list_page_size=_DEFAULT_PAGE_SIZE).execute()
                return _DEFAULT_PAGE_SIZE
            return int(config.list_page_size)
        except Exception:
            return _DEFAULT_PAGE_SIZE

    @classmethod
    def save_page_size(cls, page_size: int) -> None:
        from gws_care.core.care_app_config import CareAppConfig
        if page_size not in VALID_PAGE_SIZES:
            page_size = _DEFAULT_PAGE_SIZE
        rows_updated = CareAppConfig.update(list_page_size=page_size).execute()
        if rows_updated == 0:
            CareAppConfig.insert(list_page_size=page_size).execute()

    @classmethod
    def get_color_theme(cls) -> str:
        try:
            from gws_care.core.care_app_config import CareAppConfig
            config = CareAppConfig.get_or_none()
            if config is None:
                return "green"
            return config.color_theme or "green"
        except Exception:
            return "green"

    @classmethod
    def save_color_theme(cls, theme: str) -> None:
        from gws_care.core.care_app_config import CareAppConfig
        if theme not in VALID_THEMES:
            theme = "green"
        rows_updated = CareAppConfig.update(color_theme=theme).execute()
        if rows_updated == 0:
            CareAppConfig.insert(color_theme=theme).execute()
