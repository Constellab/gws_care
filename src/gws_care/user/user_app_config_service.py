"""Service for reading and updating per-user app configuration."""

_DEFAULT_PAGE_SIZE = 50
VALID_PAGE_SIZES = [10, 25, 50, 100, 200]
VALID_THEMES = ["green", "pink", "purple"]


class UserAppConfigService:
    """Read/write per-user app config rows (no auth context required)."""

    @classmethod
    def get_page_size(cls, user_id: str) -> int:
        try:
            from gws_care.user.user_app_config import UserAppConfig
            config = UserAppConfig.get_or_none(UserAppConfig.user_id == user_id)
            return int(config.page_size) if config else _DEFAULT_PAGE_SIZE
        except Exception:
            return _DEFAULT_PAGE_SIZE

    @classmethod
    def get_color_theme(cls, user_id: str) -> str:
        try:
            from gws_care.user.user_app_config import UserAppConfig
            config = UserAppConfig.get_or_none(UserAppConfig.user_id == user_id)
            return config.color_theme if config else "green"
        except Exception:
            return "green"

    @classmethod
    def save_page_size(cls, user_id: str, page_size: int) -> None:
        from gws_care.user.user_app_config import UserAppConfig
        if page_size not in VALID_PAGE_SIZES:
            page_size = _DEFAULT_PAGE_SIZE
        rows_updated = (
            UserAppConfig.update(page_size=page_size)
            .where(UserAppConfig.user_id == user_id)
            .execute()
        )
        if rows_updated == 0:
            UserAppConfig.create(user_id=user_id, page_size=page_size)

    @classmethod
    def save_color_theme(cls, user_id: str, theme: str) -> None:
        from gws_care.user.user_app_config import UserAppConfig
        if theme not in VALID_THEMES:
            theme = "green"
        rows_updated = (
            UserAppConfig.update(color_theme=theme)
            .where(UserAppConfig.user_id == user_id)
            .execute()
        )
        if rows_updated == 0:
            UserAppConfig.create(user_id=user_id, color_theme=theme)
