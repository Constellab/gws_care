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

    @classmethod
    def get_org_info(cls) -> dict:
        """Return organization info dict."""
        _default = {
            "name": "", "acronym": "PSC", "siret": "", "phone": "", "email": "",
            "address": "", "address_complement": "", "postal_code": "", "city": "", "country": "France",
        }
        try:
            from gws_care.core.care_app_config import CareAppConfig
            config = CareAppConfig.get_or_none()
            if config is None:
                return _default
            return {
                "name": config.org_name or "",
                "acronym": config.org_acronym or "PSC",
                "siret": config.org_siret or "",
                "phone": config.org_phone or "",
                "email": config.org_email or "",
                "address": config.org_address or "",
                "address_complement": config.org_address_complement or "",
                "postal_code": config.org_postal_code or "",
                "city": config.org_city or "",
                "country": config.org_country or "France",
            }
        except Exception:
            return _default

    @classmethod
    def save_org_info(
        cls,
        name: str,
        acronym: str,
        siret: str,
        phone: str,
        email: str,
        address: str,
        address_complement: str,
        postal_code: str,
        city: str,
        country: str,
    ) -> None:
        from gws_care.core.care_app_config import CareAppConfig
        data = dict(
            org_name=name.strip(),
            org_acronym=acronym.strip() or "PSC",
            org_siret=siret.strip(),
            org_phone=phone.strip(),
            org_email=email.strip(),
            org_address=address.strip(),
            org_address_complement=address_complement.strip(),
            org_postal_code=postal_code.strip(),
            org_city=city.strip(),
            org_country=country.strip() or "France",
        )
        rows_updated = CareAppConfig.update(**data).execute()
        if rows_updated == 0:
            CareAppConfig.insert(**data).execute()
