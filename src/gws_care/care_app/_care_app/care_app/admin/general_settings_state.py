"""State for General settings tab (app-wide configuration)."""

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState

_IGN_SEARCH_URL = "https://data.geopf.fr/geocodage/search"
_FRANCE_COUNTRIES = {"France"}
_DEFAULT_COUNTRY_OPTIONS = [
    "France", "Côte d'Ivoire", "Maroc", "Algérie", "Tunisie",
    "Sénégal", "Belgique", "Suisse", "Canada", "Autre",
]


class OrgAddressSuggestion(BaseModel):
    fulltext: str
    street: str = ""
    zip_code: str = ""
    city: str = ""


class DialCodeOption(BaseModel):
    flag: str = "🌐"
    code: str = ""
    name: str = ""


_DEFAULT_DIAL_CODE_OPTIONS: list[DialCodeOption] = [
    DialCodeOption(flag="🇫🇷", code="+33", name="France"),
    DialCodeOption(flag="🇨🇮", code="+225", name="Côte d'Ivoire"),
    DialCodeOption(flag="🇲🇦", code="+212", name="Maroc"),
    DialCodeOption(flag="🇩🇿", code="+213", name="Algérie"),
    DialCodeOption(flag="🇹🇳", code="+216", name="Tunisie"),
    DialCodeOption(flag="🇸🇳", code="+221", name="Sénégal"),
    DialCodeOption(flag="🇧🇪", code="+32", name="Belgique"),
    DialCodeOption(flag="🇨🇭", code="+41", name="Suisse"),
    DialCodeOption(flag="🇨🇦", code="+1", name="Canada"),
    DialCodeOption(flag="🇩🇪", code="+49", name="Allemagne"),
    DialCodeOption(flag="🇬🇧", code="+44", name="Royaume-Uni"),
    DialCodeOption(flag="🇪🇸", code="+34", name="Espagne"),
    DialCodeOption(flag="🇮🇹", code="+39", name="Italie"),
    DialCodeOption(flag="🇵🇹", code="+351", name="Portugal"),
    DialCodeOption(flag="🇺🇸", code="+1", name="États-Unis"),
]

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

    # Organization identity (loaded values, used in labels/computed vars)
    org_name: str = ""
    org_acronym: str = "PSC"
    org_siret: str = ""
    org_phone: str = ""
    org_email: str = ""

    # Form fields — simple inputs
    form_org_name: str = ""
    form_org_acronym: str = ""
    form_org_siret: str = ""
    form_org_phone: str = ""
    form_org_email: str = ""

    # Form fields — phone dial code (interface required by phone_input_field())
    form_phone_dial_code: str = "+33"
    dial_code_options: list[DialCodeOption] = list(_DEFAULT_DIAL_CODE_OPTIONS)
    dial_code_filter: str = "🇫🇷 +33"
    filtered_dial_codes: list[DialCodeOption] = []
    show_dial_code_suggestions: bool = False

    # Form fields — address (same interface as address_section() shared component)
    form_country: str = "France"
    form_address: str = ""
    form_address_complement: str = ""
    form_postal_code: str = ""
    form_city: str = ""
    address_manual_mode: bool = False
    address_suggestions: list[OrgAddressSuggestion] = []
    show_address_suggestions: bool = False
    is_fetching_suggestions: bool = False
    country_options: list[str] = list(_DEFAULT_COUNTRY_OPTIONS)
    country_filter: str = "France"
    filtered_countries: list[str] = []
    show_country_suggestions: bool = False

    is_saving_org: bool = False
    save_org_success: str = ""
    save_org_error: str = ""

    # Mirrors LanguageState.language — loaded in load_color_theme on every page
    app_language: str = "fr"

    @rx.var
    def send_to_org_doctor_label(self) -> str:
        if self.app_language == "fr":
            return f"Envoyer au médecin {self.org_acronym}"
        return f"Send to {self.org_acronym} doctor"

    @rx.var
    def sent_to_org_doctor_label(self) -> str:
        if self.app_language == "fr":
            return f"Transmis au médecin {self.org_acronym}"
        return f"Sent to {self.org_acronym} doctor"

    @rx.var
    def transfer_all_to_org_doctor_label(self) -> str:
        if self.app_language == "fr":
            return f"Transmettre tous les résultats au médecin {self.org_acronym}"
        return f"Transfer all results to the {self.org_acronym} doctor"

    @rx.var
    def click_to_transfer_org_label(self) -> str:
        if self.app_language == "fr":
            return f"Tous les examens sont enregistrés. Cliquez pour transmettre au médecin {self.org_acronym}."
        return f"All exams are saved. Click the button to transfer to the {self.org_acronym} doctor."

    @rx.var
    def org_validated_label(self) -> str:
        if self.app_language == "fr":
            return f"{self.org_acronym} validé"
        return f"{self.org_acronym} validated"

    @rx.var
    def awaiting_org_label(self) -> str:
        if self.app_language == "fr":
            return f"En attente de validation du médecin {self.org_acronym}."
        return f"Awaiting {self.org_acronym} doctor validation."

    @rx.var
    def step_transmitted_label(self) -> str:
        if self.app_language == "fr":
            return f"Transmis Dr {self.org_acronym}"
        return f"Sent to {self.org_acronym}"

    @rx.var
    def step_org_validated_label(self) -> str:
        if self.app_language == "fr":
            return f"Dr {self.org_acronym} validé"
        return f"{self.org_acronym} validated"

    @rx.var
    def org_doctor_label(self) -> str:
        if self.app_language == "fr":
            return f"Médecin {self.org_acronym}"
        return f"{self.org_acronym} Doctor"

    @rx.var
    def org_doctor_placeholder(self) -> str:
        if self.app_language == "fr":
            return f"Sélectionner un médecin {self.org_acronym}"
        return f"Select a {self.org_acronym} Doctor"

    @rx.var
    def org_interpretation_heading(self) -> str:
        if self.app_language == "fr":
            return f"Interprétation {self.org_acronym} — "
        return f"{self.org_acronym} Interpretation — "

    @rx.var
    def org_doctor_interpretation_label(self) -> str:
        if self.app_language == "fr":
            return f"Interprétation Médecin {self.org_acronym}"
        return f"{self.org_acronym} Doctor Interpretation"

    @rx.var
    def theme_css(self) -> str:
        """CSS variable overrides for the active color theme."""
        if self.color_theme == "pink":
            return _PINK_CSS
        if self.color_theme == "purple":
            return _PURPLE_CSS
        return ""  # green is the default — no override needed

    @rx.var
    def form_phone(self) -> str:
        """Alias for form_org_phone — satisfies the phone_input_field() component interface."""
        return self.form_org_phone

    @rx.event
    async def on_load(self):
        try:
            with await self.authenticate_user() as auth_user:
                user_id = str(auth_user.id)
                from gws_care.user.user_app_config_service import UserAppConfigService
                self.page_size = str(UserAppConfigService.get_page_size(user_id))
                self.color_theme = UserAppConfigService.get_color_theme(user_id)
        except Exception:
            self.page_size = "50"
            self.color_theme = "green"
        try:
            from gws_care.core.care_app_config_service import CareAppConfigService
            org = CareAppConfigService.get_org_info()
            self.org_name = org["name"]
            self.org_acronym = org["acronym"]
            self.org_siret = org["siret"]
            self.org_phone = org["phone"]
            self.org_email = org["email"]
            self.form_org_name = self.org_name
            self.form_org_acronym = self.org_acronym
            self.form_org_siret = self.org_siret
            self.form_org_email = self.org_email
            raw_phone = org["phone"]
            if raw_phone and raw_phone.startswith("+") and " " in raw_phone:
                parts = raw_phone.split(" ", 1)
                self.form_phone_dial_code = parts[0]
                self.form_org_phone = parts[1]
                dial_code_str = parts[0]
                matching = next((d for d in _DEFAULT_DIAL_CODE_OPTIONS if d.code == dial_code_str), None)
                self.dial_code_filter = f"{matching.flag} {dial_code_str}" if matching else dial_code_str
            else:
                self.form_org_phone = raw_phone
                self.form_phone_dial_code = "+33"
                self.dial_code_filter = "🇫🇷 +33"
            self.form_address = org["address"]
            self.form_address_complement = org["address_complement"]
            self.form_postal_code = org["postal_code"]
            self.form_city = org["city"]
            country = org["country"] or "France"
            self.form_country = country
            self.country_filter = country
            self.address_manual_mode = country not in _FRANCE_COUNTRIES
        except Exception:
            pass

    @rx.event
    async def load_color_theme(self):
        """Lightweight event to load the color theme, org acronym and language (called on every page)."""
        try:
            with await self.authenticate_user() as auth_user:
                user_id = str(auth_user.id)
                from gws_care.user.user_app_config_service import UserAppConfigService
                self.color_theme = UserAppConfigService.get_color_theme(user_id)
        except Exception:
            self.color_theme = "green"
        try:
            from gws_care.core.care_app_config_service import CareAppConfigService
            org = CareAppConfigService.get_org_info()
            self.org_acronym = org["acronym"]
        except Exception:
            pass
        try:
            from ..common.language_state import LanguageState
            lang_state = await self.get_state(LanguageState)
            self.app_language = lang_state.language
        except Exception:
            pass

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
            with await self.authenticate_user() as auth_user:
                user_id = str(auth_user.id)
                from gws_care.user.user_app_config_service import UserAppConfigService
                UserAppConfigService.save_page_size(user_id, int(self.page_size))
            self.save_page_size_success = "Enregistré."
        except Exception as e:
            self.save_page_size_error = f"Erreur : {e}"
        finally:
            self.is_saving_page_size = False

    @rx.event
    def set_form_org_name(self, value: str):
        self.form_org_name = value

    @rx.event
    def set_form_org_acronym(self, value: str):
        self.form_org_acronym = value

    @rx.event
    def set_form_org_siret(self, value: str):
        self.form_org_siret = value

    @rx.event
    def set_form_org_phone(self, value: str):
        self.form_org_phone = value

    @rx.event
    def set_form_org_email(self, value: str):
        self.form_org_email = value

    @rx.event
    def set_form_phone(self, value: str):
        """Alias for set_form_org_phone — satisfies the phone_input_field() component interface."""
        self.form_org_phone = value

    # ── Address autocomplete events (interface required by address_section()) ──

    @rx.event
    def set_form_address(self, value: str):
        self.form_address = value

    @rx.event
    def set_form_address_complement(self, value: str):
        self.form_address_complement = value

    @rx.event
    def set_form_postal_code(self, value: str):
        self.form_postal_code = value

    @rx.event
    def set_form_city(self, value: str):
        self.form_city = value

    @rx.event
    def set_country_filter(self, value: str):
        self.country_filter = value
        if not value:
            self.filtered_countries = []
            self.show_country_suggestions = False
            return
        q = value.lower()
        self.filtered_countries = [c for c in self.country_options if q in c.lower()][:8]
        self.show_country_suggestions = len(self.filtered_countries) > 0

    @rx.event
    def select_country_suggestion(self, country: str):
        self.form_country = country
        self.country_filter = country
        self.filtered_countries = []
        self.show_country_suggestions = False
        if country not in _FRANCE_COUNTRIES:
            self.address_manual_mode = True
            self.address_suggestions = []
            self.show_address_suggestions = False
        else:
            self.address_manual_mode = False

    @rx.event
    def toggle_address_manual_mode(self):
        self.address_manual_mode = not self.address_manual_mode
        if self.address_manual_mode:
            self.address_suggestions = []
            self.show_address_suggestions = False

    # ── Dial code events (interface required by phone_input_field()) ─────────────

    @rx.event
    def set_dial_code_filter(self, value: str):
        self.dial_code_filter = value
        q = value.lower()
        if not value:
            self.filtered_dial_codes = list(self.dial_code_options[:20])
            self.show_dial_code_suggestions = True
        else:
            self.filtered_dial_codes = [
                d for d in self.dial_code_options
                if q in d.name.lower() or q in d.code
            ][:12]
            self.show_dial_code_suggestions = len(self.filtered_dial_codes) > 0

    @rx.event
    def select_dial_code_option(self, code: str, flag: str):
        self.form_phone_dial_code = code
        self.dial_code_filter = f"{flag} {code}"
        self.filtered_dial_codes = []
        self.show_dial_code_suggestions = False

    @rx.event
    def close_dial_code_suggestions(self):
        self.show_dial_code_suggestions = False

    @rx.event
    def close_autocomplete_dropdowns(self):
        self.show_country_suggestions = False
        self.show_address_suggestions = False
        self.show_dial_code_suggestions = False

    @rx.event
    async def fetch_address_suggestions(self, query: str):
        self.form_address = query
        if not query or len(query) < 3 or self.address_manual_mode or self.form_country not in _FRANCE_COUNTRIES:
            self.address_suggestions = []
            self.show_address_suggestions = False
            return
        self.is_fetching_suggestions = True
        try:
            import httpx
            params = {"q": query, "limit": 6}
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(_IGN_SEARCH_URL, params=params)
                data = resp.json()
            features = data.get("features", [])
            suggestions = []
            for f in features:
                props = f.get("properties", {})
                fulltext = props.get("label", "")
                street = props.get("name", "")
                if not street:
                    hn = props.get("housenumber", "")
                    sn = props.get("street", "")
                    street = f"{hn} {sn}".strip() if hn or sn else fulltext.split(",")[0]
                suggestions.append(OrgAddressSuggestion(
                    fulltext=fulltext,
                    street=street,
                    zip_code=props.get("postcode", ""),
                    city=props.get("city", ""),
                ))
            self.address_suggestions = suggestions
            self.show_address_suggestions = len(suggestions) > 0
        except Exception:
            self.address_suggestions = []
            self.show_address_suggestions = False
        finally:
            self.is_fetching_suggestions = False

    @rx.event
    def select_address_suggestion(self, street: str, zip_code: str, city: str):
        self.form_address = street
        self.form_postal_code = zip_code
        self.form_city = city
        self.address_suggestions = []
        self.show_address_suggestions = False

    @rx.event
    async def save_org_info(self):
        self.save_org_success = ""
        self.save_org_error = ""
        if not self.form_org_name.strip() or not self.form_org_acronym.strip():
            self.save_org_error = "Le nom de l'entreprise et l'acronyme sont obligatoires."
            return
        self.is_saving_org = True
        try:
            from gws_care.core.care_app_config_service import CareAppConfigService
            CareAppConfigService.save_org_info(
                name=self.form_org_name,
                acronym=self.form_org_acronym,
                siret=self.form_org_siret,
                phone=f"{self.form_phone_dial_code} {self.form_org_phone}".strip(),
                email=self.form_org_email,
                address=self.form_address,
                address_complement=self.form_address_complement,
                postal_code=self.form_postal_code,
                city=self.form_city,
                country=self.form_country,
            )
            self.org_name = self.form_org_name
            self.org_acronym = self.form_org_acronym
            self.org_siret = self.form_org_siret
            self.org_phone = f"{self.form_phone_dial_code} {self.form_org_phone}".strip()
            self.org_email = self.form_org_email
            self.save_org_success = "Enregistré."
        except Exception as e:
            self.save_org_error = f"Erreur : {e}"
        finally:
            self.is_saving_org = False

    @rx.event
    async def set_color_theme(self, theme: str):
        """Set and immediately persist the color theme."""
        self.color_theme = theme
        self.save_theme_success = ""
        self.save_theme_error = ""
        self.is_saving_theme = True
        try:
            with await self.authenticate_user() as auth_user:
                user_id = str(auth_user.id)
                from gws_care.user.user_app_config_service import UserAppConfigService
                UserAppConfigService.save_color_theme(user_id, theme)
            self.save_theme_success = "Enregistré."
        except Exception as e:
            self.save_theme_error = f"Erreur : {e}"
        finally:
            self.is_saving_theme = False
