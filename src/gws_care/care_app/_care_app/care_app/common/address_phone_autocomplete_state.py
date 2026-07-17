"""Shared mixin state for the address (IGN autocomplete) + phone (dial-code) form fields.

Pairs with common/shared_address_phone_components.py's address_section()/phone_input_field().
Any form state that renders those components should inherit this mixin alongside its own
base class, e.g.:

    class MyFormState(FormDialogState, AddressPhoneAutocompleteState, rx.State):
        ...
"""

import reflex as rx
from pydantic import BaseModel

_IGN_SEARCH_URL = "https://data.geopf.fr/geocodage/search"
_COUNTRIES_CDN_URL = "https://cdn.jsdelivr.net/npm/world-countries/countries.json"
_FRANCE_COUNTRIES = {"France"}
_DEFAULT_COUNTRY_OPTIONS = [
    "France", "Côte d'Ivoire", "Maroc", "Algérie", "Tunisie",
    "Sénégal", "Belgique", "Suisse", "Canada", "Autre",
]

_PRIORITY_DIAL = ["France", "Côte d'Ivoire", "Maroc", "Algérie", "Tunisie",
                  "Sénégal", "Belgique", "Suisse", "Canada"]


class AddressSuggestion(BaseModel):
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


class AddressPhoneAutocompleteState(rx.State, mixin=True):
    """Mixin: address (IGN autocomplete) + phone (dial-code combobox) fields and events."""

    form_phone: str = ""
    form_country: str = "France"
    form_address: str = ""
    form_address_complement: str = ""
    form_postal_code: str = ""
    form_city: str = ""
    address_manual_mode: bool = False
    address_suggestions: list[AddressSuggestion] = []
    show_address_suggestions: bool = False
    is_fetching_suggestions: bool = False
    form_phone_dial_code: str = "+33"

    country_options: list[str] = list(_DEFAULT_COUNTRY_OPTIONS)
    dial_code_options: list[DialCodeOption] = list(_DEFAULT_DIAL_CODE_OPTIONS)
    country_filter: str = ""
    filtered_countries: list[str] = []
    show_country_suggestions: bool = False

    dial_code_filter: str = "🇫🇷 +33"
    filtered_dial_codes: list[DialCodeOption] = []
    show_dial_code_suggestions: bool = False

    # ── Setters ───────────────────────────────────────────────────────────────

    @rx.event
    def set_form_phone(self, value: str):
        self.form_phone = value

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
    def set_form_phone_dial_code(self, value: str):
        self.form_phone_dial_code = value

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

    # ── Country autocomplete ───────────────────────────────────────────────────

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
    def close_autocomplete_dropdowns(self):
        self.show_country_suggestions = False
        self.show_address_suggestions = False
        self.show_dial_code_suggestions = False

    @rx.event
    def toggle_address_manual_mode(self):
        self.address_manual_mode = not self.address_manual_mode
        if self.address_manual_mode:
            self.address_suggestions = []
            self.show_address_suggestions = False

    # ── Address autocomplete (IGN Géoplateforme) ───────────────────────────────

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
                # "name" already contains "housenumber street" combined
                street = props.get("name", "")
                if not street:
                    hn = props.get("housenumber", "")
                    sn = props.get("street", "")
                    street = f"{hn} {sn}".strip() if hn or sn else fulltext.split(",")[0]
                suggestions.append(AddressSuggestion(
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

    # ── Countries from REST Countries API ─────────────────────────────────────

    @rx.event
    async def fetch_countries(self):
        try:
            import httpx
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(_COUNTRIES_CDN_URL, follow_redirects=True)
                data = resp.json()
            names: list[str] = []
            raw_dial: list[DialCodeOption] = []
            for country in data:
                fr_name = (
                    (country.get("translations") or {}).get("fra", {}).get("common")
                    or country.get("name", {}).get("common")
                    or ""
                )
                if not fr_name:
                    continue
                names.append(fr_name)
                idd = country.get("idd") or {}
                root = idd.get("root", "")
                suffixes = idd.get("suffixes") or []
                if root:
                    # Single short suffix → append (e.g. France "+3"+"3"="+33")
                    # Multiple suffixes or long suffix → area codes, use root only (e.g. Canada "+1")
                    if len(suffixes) == 1 and len(suffixes[0]) <= 2:
                        code = root + suffixes[0]
                    else:
                        code = root
                    if len(code) >= 2:
                        raw_dial.append(DialCodeOption(
                            flag=country.get("flag", "🌐"),
                            code=code,
                            name=fr_name,
                        ))
            # Country list: France first, then alphabetically
            others = sorted(n for n in names if n != "France")
            self.country_options = ["France"] + others
            # Dial codes: priority countries first, then alphabetically
            priority = {n: i for i, n in enumerate(_PRIORITY_DIAL)}
            def _dial_key(opt: DialCodeOption):
                idx = priority.get(opt.name)
                return (0, idx) if idx is not None else (1, opt.name)
            self.dial_code_options = sorted(raw_dial, key=_dial_key)
        except Exception:
            pass
