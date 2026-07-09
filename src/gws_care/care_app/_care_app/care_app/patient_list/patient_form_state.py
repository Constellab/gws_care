"""State for the patient create / edit form dialog."""

import traceback
from typing import AsyncGenerator

import reflex as rx
from gws_reflex_base import FormDialogState
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class _FormValidationError(Exception):
    """Sentinel: validation failed — keeps the dialog open."""

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


class AccountOption(BaseModel):
    id: str
    name: str
    account_type: str = ""
    city: str = ""


class PatientFormState(FormDialogState, rx.State):
    """Manages the create / update patient dialog (demographics only).

    Doctor and account links are managed from the patient detail tabs.
    """

    form_last_name: str = ""
    form_first_name: str = ""
    form_birth_name: str = ""
    form_date_of_birth: str = ""
    form_gender: str = "M"
    form_phone: str = ""
    form_email: str = ""
    # ── Address fields ─────────────────────────────────────────────────────────
    form_country: str = "France"
    form_address: str = ""
    form_address_complement: str = ""
    form_postal_code: str = ""
    form_city: str = ""
    address_manual_mode: bool = False
    address_suggestions: list[AddressSuggestion] = []
    show_address_suggestions: bool = False
    is_fetching_suggestions: bool = False
    # ── Other fields ───────────────────────────────────────────────────────────
    form_social_security_number: str = ""
    form_weight: str = ""
    form_height: str = ""
    form_sex: str = ""
    form_nationality: str = ""
    form_phone_dial_code: str = "+33"
    form_notif_email: bool = False
    form_notif_sms: bool = False
    form_notif_whatsapp: bool = False
    form_error: str = ""
    # ── Country options + autocomplete ───────────────────────────────────────
    country_options: list[str] = list(_DEFAULT_COUNTRY_OPTIONS)
    dial_code_options: list[DialCodeOption] = list(_DEFAULT_DIAL_CODE_OPTIONS)
    country_filter: str = ""
    filtered_countries: list[str] = []
    show_country_suggestions: bool = False
    # ── Phone dial code combobox ───────────────────────────────────────────────
    dial_code_filter: str = "🇫🇷 +33"
    filtered_dial_codes: list[DialCodeOption] = []
    show_dial_code_suggestions: bool = False
    # ── Account linking (creation and draft-edit) ─────────────────────────────
    form_account_id: str = ""
    selected_account_label: str = ""
    selected_account_type: str = ""
    selected_account_contact_last_name: str = ""
    selected_account_contact_first_name: str = ""
    selected_account_address: str = ""
    selected_account_postal_code: str = ""
    selected_account_city: str = ""
    selected_account_phone: str = ""
    selected_account_email: str = ""
    account_options: list[AccountOption] = []
    account_filter: str = ""
    is_loading_accounts: bool = False
    show_account_picker: bool = False
    editing_is_draft: bool = False

    _editing_patient_id: str = ""
    _link_to_account_id: str = ""

    @rx.var
    def show_account_section(self) -> bool:
        """Always show account picker — both create and edit modes."""
        return True

    # ── Setters ───────────────────────────────────────────────────────────────

    @rx.event
    def set_form_last_name(self, value: str):
        self.form_last_name = value

    @rx.event
    def set_form_first_name(self, value: str):
        self.form_first_name = value

    @rx.event
    def set_form_birth_name(self, value: str):
        self.form_birth_name = value

    @rx.event
    def set_form_date_of_birth(self, value: str):
        self.form_date_of_birth = value

    @rx.event
    def set_form_gender(self, value: str):
        self.form_gender = value

    @rx.event
    def set_form_phone(self, value: str):
        self.form_phone = value

    @rx.event
    def set_form_email(self, value: str):
        self.form_email = value

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
    def set_form_social_security_number(self, value: str):
        self.form_social_security_number = value

    @rx.event
    def set_form_weight(self, value: str):
        self.form_weight = value

    @rx.event
    def set_form_height(self, value: str):
        self.form_height = value

    @rx.event
    def set_form_sex(self, value: str):
        self.form_sex = value

    @rx.event
    def set_form_nationality(self, value: str):
        self.form_nationality = value

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

    @rx.event
    def set_form_notif_email(self, value: bool):
        self.form_notif_email = value

    @rx.event
    def set_form_notif_sms(self, value: bool):
        self.form_notif_sms = value

    @rx.event
    def set_form_notif_whatsapp(self, value: bool):
        self.form_notif_whatsapp = value

    # ── Country / address mode ─────────────────────────────────────────────────

    @rx.event
    def set_form_country(self, value: str):
        self.form_country = value
        if value not in _FRANCE_COUNTRIES:
            self.address_manual_mode = True
            self.address_suggestions = []
            self.show_address_suggestions = False
        else:
            self.address_manual_mode = False

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
    def hide_country_suggestions(self):
        self.show_country_suggestions = False

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

    @rx.event
    def hide_address_suggestions(self):
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

    # ── Account picker (optional, create mode only) ────────────────────────────

    @rx.event
    def toggle_account_picker(self):
        self.show_account_picker = not self.show_account_picker
        if self.show_account_picker:
            yield PatientFormState.load_account_options

    @rx.event
    async def load_account_options(self):
        self.is_loading_accounts = True
        try:
            _main = await self.get_state(ReflexMainState)
            with await _main.authenticate_user():
                from gws_care.account.account_service import AccountService
                accounts = AccountService.list_accounts(
                    active_only=True,
                    name=self.account_filter.strip() or None,
                )
            self.account_options = [
                AccountOption(
                    id=str(a.id),
                    name=a.name or "",
                    account_type=a.account_type or "COMPANY",
                    city=a.city or "",
                )
                for a in accounts
            ]
        except Exception:
            self.account_options = []
        finally:
            self.is_loading_accounts = False

    @rx.event
    async def set_account_filter(self, value: str):
        self.account_filter = value
        await self.load_account_options()

    @rx.event
    def select_account(self, account_id: str, name: str):
        self.form_account_id = account_id
        self.selected_account_label = name
        self.show_account_picker = False
        self.selected_account_type = ""
        self.selected_account_contact_last_name = ""
        self.selected_account_contact_first_name = ""
        self.selected_account_address = ""
        self.selected_account_postal_code = ""
        self.selected_account_city = ""
        self.selected_account_phone = ""
        self.selected_account_email = ""
        if not account_id:
            return
        try:
            from gws_care.account.account_service import AccountService
            account = AccountService.get_account(account_id)
            self.selected_account_type = account.account_type or ""
            self.selected_account_contact_last_name = account.contact_last_name or ""
            self.selected_account_contact_first_name = account.contact_first_name or ""
            self.selected_account_address = account.address or ""
            self.selected_account_postal_code = account.postal_code or ""
            self.selected_account_city = account.city or ""
            self.selected_account_phone = account.phone or ""
            self.selected_account_email = account.email or ""
            if account.account_type == "INDIVIDUAL":
                if account.contact_last_name and not self.form_last_name.strip():
                    self.form_last_name = account.contact_last_name.strip().upper()
                if account.contact_first_name and not self.form_first_name.strip():
                    self.form_first_name = account.contact_first_name.strip()
                if account.phone and not self.form_phone.strip():
                    self.form_phone = account.phone or ""
                if account.email and not self.form_email.strip():
                    self.form_email = account.email or ""
                if account.address and not self.form_address.strip():
                    self.form_address = account.address or ""
                if account.postal_code and not self.form_postal_code.strip():
                    self.form_postal_code = account.postal_code or ""
                if account.city and not self.form_city.strip():
                    self.form_city = account.city or ""
        except Exception:
            pass

    @rx.event
    def clear_account_selection(self):
        self.form_account_id = ""
        self.selected_account_label = ""
        self.selected_account_type = ""
        self.selected_account_contact_last_name = ""
        self.selected_account_contact_first_name = ""
        self.selected_account_address = ""
        self.selected_account_postal_code = ""
        self.selected_account_city = ""
        self.selected_account_phone = ""
        self.selected_account_email = ""
        self.account_filter = ""
        self.account_options = []

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

    # ── Dialog lifecycle ──────────────────────────────────────────────────────

    @rx.event(background=True)  # type: ignore
    async def trigger_account_create(self):
        """Open account creation dialog pre-filled with current patient form data.

        Reads own state vars inside async with self (background task pattern),
        then dispatches the account form open event with captured Python values.
        Both dialogs stay open simultaneously — Radix UI handles z-index stacking.
        """
        from ..account_list.account_form_state import AccountFormState

        async with self:
            last = self.form_last_name
            first = self.form_first_name
            phone = self.form_phone
            email = self.form_email
            address = self.form_address
            postal_code = self.form_postal_code
            city = self.form_city

        yield AccountFormState.open_with_prefilled_data(
            last, first, phone, email, address, postal_code, city
        )

    @rx.event(background=True)  # type: ignore
    async def submit_form(self, form_data: dict):
        """Override: show validation errors inline without closing the dialog."""
        async with self:
            self.is_loading = True
            self.form_error = ""
        try:
            if self.is_update_mode:
                async for event in self._update(form_data):
                    yield event
            else:
                async for event in self._create(form_data):
                    yield event
        except _FormValidationError as e:
            async with self:
                self.form_error = str(e)
            return
        except Exception as e:
            traceback.print_exc()
            async with self:
                self.form_error = str(e)
            return
        finally:
            async with self:
                self.is_loading = False
        async with self:
            await self.close_dialog()
        from ..patient_list.patient_list_state import PatientListState
        yield PatientListState.on_load()

    @rx.event
    async def open_create_dialog(self):
        self.is_update_mode = False
        self._editing_patient_id = ""
        self._link_to_account_id = ""
        await self._clear_form_state()
        self.dialog_opened = True
        yield PatientFormState.fetch_countries

    @rx.event
    async def open_create_dialog_for_account(self, account_id: str):
        """Open patient creation dialog; auto-link to account_id on save."""
        self.is_update_mode = False
        self._editing_patient_id = ""
        await self._clear_form_state()
        self._link_to_account_id = account_id  # set AFTER clear so it's not wiped
        self.dialog_opened = True
        yield PatientFormState.fetch_countries

    @rx.event
    async def open_edit_dialog(self, patient_id: str):
        self.is_update_mode = True
        self._editing_patient_id = patient_id
        _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            from gws_care.patient.patient_service import PatientService
            p = PatientService.get_patient(patient_id)
            self.form_last_name = p.last_name or ""
            self.form_first_name = p.first_name or ""
            self.form_birth_name = p.birth_name or ""
            self.form_date_of_birth = p.date_of_birth.isoformat() if p.date_of_birth else ""
            self.form_gender = p.gender or "M"
            self.form_phone = p.phone or ""
            self.form_email = p.email or ""
            self.form_country = getattr(p, "country", None) or "France"
            self.country_filter = self.form_country
            self.filtered_countries = []
            self.show_country_suggestions = False
            self.form_address = p.address or ""
            self.form_address_complement = getattr(p, "address_complement", None) or ""
            self.form_postal_code = p.postal_code or ""
            self.form_city = p.city or ""
            self.address_manual_mode = (self.form_country not in _FRANCE_COUNTRIES)
            self.address_suggestions = []
            self.show_address_suggestions = False
            self.form_social_security_number = p.social_security_number or ""
            self.form_weight = str(p.weight) if p.weight is not None else ""
            self.form_height = str(p.height) if p.height is not None else ""
            self.form_sex = p.sex or ""
            self.form_nationality = p.nationality or ""
            phone_code = p.phone_country or "+33"
            self.form_phone_dial_code = phone_code
            m = next((d for d in self.dial_code_options if d.code == phone_code), None)
            self.dial_code_filter = f"{m.flag} {m.code}" if m else phone_code
            notif = p.notification_preferences or {}
            if isinstance(notif, str):
                import json as _json
                try:
                    notif = _json.loads(notif)
                except Exception:
                    notif = {}
            self.form_notif_email = bool(notif.get("email", False))
            self.form_notif_sms = bool(notif.get("sms", False))
            self.form_notif_whatsapp = bool(notif.get("whatsapp", False))
            self.editing_is_draft = bool(getattr(p, "is_draft", False))
            # Always load existing account so the picker shows the current link
            from gws_care.patient.patient_account import PatientAccount
            from gws_care.account.account import Account
            from peewee import JOIN
            rows = list(
                PatientAccount.select(PatientAccount.patient, Account.id, Account.name)
                .join(Account, JOIN.INNER, on=(PatientAccount.account == Account.id))
                .where(PatientAccount.patient == patient_id)
                .tuples()
            )
            if rows:
                _, acc_id, acc_name = rows[0]
                self.form_account_id = str(acc_id)
                self.selected_account_label = acc_name
            else:
                self.form_account_id = ""
                self.selected_account_label = ""
        self.dialog_opened = True
        yield PatientFormState.fetch_countries

    # ── FormDialogState abstract method implementations ───────────────────────

    async def _clear_form_state(self) -> None:
        self.form_last_name = ""
        self.form_first_name = ""
        self.form_birth_name = ""
        self.form_date_of_birth = ""
        self.form_gender = "M"
        self.form_phone = ""
        self.form_email = ""
        self.form_country = "France"
        self.country_filter = "France"
        self.filtered_countries = []
        self.show_country_suggestions = False
        self.form_address = ""
        self.form_address_complement = ""
        self.form_postal_code = ""
        self.form_city = ""
        self.address_manual_mode = False
        self.address_suggestions = []
        self.show_address_suggestions = False
        self.is_fetching_suggestions = False
        self.form_social_security_number = ""
        self.form_weight = ""
        self.form_height = ""
        self.form_sex = ""
        self.form_nationality = ""
        self.form_phone_dial_code = "+33"
        self.dial_code_filter = "🇫🇷 +33"
        self.filtered_dial_codes = []
        self.show_dial_code_suggestions = False
        self.form_error = ""
        self.form_notif_email = False
        self.form_notif_sms = False
        self.form_notif_whatsapp = False
        self.form_account_id = ""
        self.selected_account_label = ""
        self.selected_account_type = ""
        self.selected_account_contact_last_name = ""
        self.selected_account_contact_first_name = ""
        self.selected_account_address = ""
        self.selected_account_postal_code = ""
        self.selected_account_city = ""
        self.selected_account_phone = ""
        self.selected_account_email = ""
        self.account_options = []
        self.account_filter = ""
        self.show_account_picker = False
        self.editing_is_draft = False
        self._editing_patient_id = ""
        self._link_to_account_id = ""
        self.is_update_mode = False

    async def _create(self, form_data: dict) -> AsyncGenerator:
        from datetime import date as date_type
        from gws_care.patient.patient_dto import SavePatientDTO
        from gws_care.patient.patient_service import PatientService

        import re
        last_name = self.form_last_name.strip()
        first_name = self.form_first_name.strip()
        if not last_name:
            raise _FormValidationError("Nom de famille requis")
        if not first_name:
            raise _FormValidationError("Prénom requis")
        if not self.form_date_of_birth:
            raise _FormValidationError("Date de naissance requise")
        if self.form_gender not in ("M", "F"):
            raise _FormValidationError("Le sexe est obligatoire (Masculin ou Féminin)")
        if self.form_email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", self.form_email.strip()):
            raise _FormValidationError("Format d'e-mail incorrect — vérifiez le champ « E-mail »")
        nir_error = self._validate_nir(self.form_social_security_number, self.form_country)
        if nir_error:
            raise _FormValidationError(nir_error)
        if not self._link_to_account_id and not self.form_account_id:
            raise _FormValidationError("Veuillez associer le patient à un compte de facturation (requis)")

        # Resolve country: if France mode without explicit manual flag, store "France"
        country_to_save = self.form_country if self.form_country and self.form_country != "France" else (
            "France" if self.form_country == "France" else None
        )

        dto = SavePatientDTO(
            last_name=last_name,
            first_name=first_name,
            birth_name=self.form_birth_name or None,
            date_of_birth=date_type.fromisoformat(self.form_date_of_birth),
            gender=self.form_gender,
            phone=self.form_phone or None,
            email=self.form_email.strip() or None,
            country=self.form_country or None,
            address=self.form_address or None,
            address_complement=self.form_address_complement or None,
            postal_code=self.form_postal_code or None,
            city=self.form_city or None,
            social_security_number=self.form_social_security_number or None,
            weight=float(self.form_weight) if self.form_weight.strip() else None,
            height=float(self.form_height) if self.form_height.strip() else None,
            sex=self.form_sex or None,
            nationality=self.form_nationality or None,
            phone_country=self.form_phone_dial_code if self.form_phone_dial_code and self.form_phone_dial_code != "other" else None,
        )

        async with self:
            _main = await self.get_state(ReflexMainState)
            _link_to_account = self._link_to_account_id
            link_account = _link_to_account or self.form_account_id
        dto.account_id = link_account or None
        with await _main.authenticate_user():
            patient = PatientService.create_patient(dto)

        yield rx.toast.success(f"Patient {patient.patient_number} créé")
        from ..patient_list.patient_list_state import PatientListState
        if _link_to_account:
            from ..account_detail.account_detail_state import AccountDetailState
            yield AccountDetailState.on_load()
        yield PatientListState.on_load()

    async def _update(self, form_data: dict) -> AsyncGenerator:
        from datetime import date as date_type
        from gws_care.patient.patient_dto import SavePatientDTO
        from gws_care.patient.patient_service import PatientService

        import re
        last_name = self.form_last_name.strip()
        first_name = self.form_first_name.strip()
        if not last_name:
            raise _FormValidationError("Nom de famille requis")
        if not first_name:
            raise _FormValidationError("Prénom requis")
        if not self.form_date_of_birth:
            raise _FormValidationError("Date de naissance requise")
        if self.form_gender not in ("M", "F"):
            raise _FormValidationError("Le sexe est obligatoire (Masculin ou Féminin)")
        if self.form_email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", self.form_email.strip()):
            raise _FormValidationError("Format d'e-mail incorrect — vérifiez le champ « E-mail »")
        nir_error = self._validate_nir(self.form_social_security_number, self.form_country)
        if nir_error:
            raise _FormValidationError(nir_error)

        dto = SavePatientDTO(
            last_name=last_name,
            first_name=first_name,
            birth_name=self.form_birth_name or None,
            date_of_birth=date_type.fromisoformat(self.form_date_of_birth),
            gender=self.form_gender,
            phone=self.form_phone or None,
            email=self.form_email.strip() or None,
            country=self.form_country or None,
            address=self.form_address or None,
            address_complement=self.form_address_complement or None,
            postal_code=self.form_postal_code or None,
            city=self.form_city or None,
            social_security_number=self.form_social_security_number or None,
            weight=float(self.form_weight) if self.form_weight.strip() else None,
            height=float(self.form_height) if self.form_height.strip() else None,
            sex=self.form_sex or None,
            nationality=self.form_nationality or None,
            phone_country=self.form_phone_dial_code if self.form_phone_dial_code and self.form_phone_dial_code != "other" else None,
            notification_preferences={
                "email": self.form_notif_email,
                "sms": self.form_notif_sms,
                "whatsapp": self.form_notif_whatsapp,
            },
        )

        async with self:
            _main = await self.get_state(ReflexMainState)
            account_to_link = self.form_account_id
            patient_id = self._editing_patient_id
        with await _main.authenticate_user():
            PatientService.update_patient(patient_id, dto)
            if account_to_link:
                from gws_care.patient.patient_account import PatientAccount
                PatientAccount.delete().where(PatientAccount.patient == patient_id).execute()
                PatientService.add_account(patient_id, account_to_link)

        yield rx.toast.success("Patient mis à jour")
        from ..patient_detail.patient_detail_state import PatientDetailState
        from ..patient_list.patient_list_state import PatientListState
        yield PatientDetailState.on_load()
        yield PatientListState.on_load()

    # ── Draft save ────────────────────────────────────────────────────────────

    @rx.event(background=True)  # type: ignore
    async def save_as_draft(self):
        """Save with minimal validation — only last_name required (draft mode)."""
        from datetime import date as date_type
        from gws_care.patient.patient_dto import SavePatientDTO
        from gws_care.patient.patient_service import PatientService

        async with self:
            self.is_loading = True
            self.form_error = ""
        try:
            last_name = self.form_last_name.strip()
            if not last_name:
                async with self:
                    self.form_error = "Nom de famille requis même pour un brouillon"
                return
            dob = date_type.fromisoformat(self.form_date_of_birth) if self.form_date_of_birth else date_type.today()
            dto = SavePatientDTO(
                last_name=last_name,
                first_name=self.form_first_name.strip() or "—",
                date_of_birth=dob,
                gender=self.form_gender or "M",
                phone=self.form_phone or None,
                email=self.form_email.strip() or None,
                country=self.form_country or None,
                address=self.form_address or None,
                address_complement=self.form_address_complement or None,
                postal_code=self.form_postal_code or None,
                city=self.form_city or None,
                social_security_number=self.form_social_security_number or None,
                sex=self.form_sex or None,
                nationality=self.form_nationality or None,
                phone_country=self.form_phone_dial_code if self.form_phone_dial_code and self.form_phone_dial_code != "other" else None,
                is_draft=True,
            )
            async with self:
                _main = await self.get_state(ReflexMainState)
                _link_to_account = self._link_to_account_id
                link_account = _link_to_account or self.form_account_id
            dto.account_id = link_account or None
            with await _main.authenticate_user():
                patient = PatientService.create_patient(dto)
            yield rx.toast.success(f"Brouillon sauvegardé ({patient.patient_number}) — à compléter ultérieurement")
            from ..patient_list.patient_list_state import PatientListState
            if _link_to_account:
                from ..account_detail.account_detail_state import AccountDetailState
                yield AccountDetailState.on_load()
            yield PatientListState.on_load()
        except Exception as e:
            traceback.print_exc()
            async with self:
                self.form_error = str(e)
            return
        finally:
            async with self:
                self.is_loading = False
        async with self:
            await self.close_dialog()
        from ..patient_list.patient_list_state import PatientListState
        yield PatientListState.on_load()

    # ── NIR validation ─────────────────────────────────────────────────────────

    def _validate_nir(self, nir: str, country: str) -> str | None:
        """Return an error message if NIR is invalid, None otherwise."""
        if not nir or not nir.strip():
            return None
        nir_clean = nir.replace(" ", "").replace("-", "")
        if country == "France" or not country:
            if not nir_clean.isdigit():
                return "Le NIR doit contenir uniquement des chiffres"
            if len(nir_clean) != 15:
                return f"Le NIR français doit contenir 15 chiffres ({len(nir_clean)} saisis)"
            if nir_clean[0] not in ("1", "2", "7", "8"):
                return "Le NIR français doit commencer par 1, 2, 7 ou 8"
        elif country == "Côte d'Ivoire":
            if not nir_clean.isdigit():
                return "Le numéro de sécurité sociale doit contenir uniquement des chiffres"
            if len(nir_clean) != 13:
                return f"Le NIR ivoirien doit contenir 13 chiffres ({len(nir_clean)} saisis)"
            if not nir_clean.startswith("384"):
                return "Le NIR ivoirien doit commencer par 384"
        return None
