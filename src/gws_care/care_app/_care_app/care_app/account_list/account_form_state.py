"""State for the account create / edit form dialog."""

import traceback
from typing import AsyncGenerator

import reflex as rx
from gws_reflex_base import FormDialogState
from gws_reflex_main import ReflexMainState
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


class PatientFillOption(BaseModel):
    id: str
    display: str        # "First Last"
    patient_number: str = ""
    date_of_birth: str = ""
    gender: str = ""


class CompanyOption(BaseModel):
    id: str
    name: str


class AccountFormState(FormDialogState, rx.State):
    """Manages the create / update account dialog."""

    # Account type: "COMPANY" or "INDIVIDUAL"
    form_account_type: str = "COMPANY"

    # Linked company (when account type is COMPANY)
    form_company_id: str = ""
    company_options: list[CompanyOption] = []

    # Form fields (public — bound to inputs in the UI)
    form_name: str = ""
    form_registration_number: str = ""
    form_phone: str = ""
    form_phone_dial_code: str = "+33"
    form_email: str = ""
    form_contact_first_name: str = ""
    form_contact_last_name: str = ""
    form_contact_name: str = ""  # kept for backward compat, auto-computed
    form_error: str = ""
    # ── Address autocomplete ───────────────────────────────────────────────────
    form_country: str = "France"
    country_filter: str = "France"
    country_options: list[str] = list(_DEFAULT_COUNTRY_OPTIONS)
    filtered_countries: list[str] = []
    show_country_suggestions: bool = False
    dial_code_options: list[DialCodeOption] = list(_DEFAULT_DIAL_CODE_OPTIONS)
    dial_code_filter: str = "🇫🇷 +33"
    filtered_dial_codes: list[DialCodeOption] = []
    show_dial_code_suggestions: bool = False
    form_address: str = ""
    form_postal_code: str = ""
    form_city: str = ""
    address_suggestions: list[AddressSuggestion] = []
    show_address_suggestions: bool = False
    address_manual_mode: bool = False
    is_fetching_suggestions: bool = False

    # Fill-from-patient
    patient_fill_options: list[PatientFillOption] = []
    selected_patient_fill: str = ""
    patient_fill_selected_label: str = ""
    patient_fill_filter_name: str = ""
    patient_fill_filter_number: str = ""
    patient_fill_is_loading: bool = False

    # Set when editing an existing account
    _editing_account_id: str = ""
    # True when dialog was opened from the patient creation form
    _from_patient_form: bool = False

    # ── Setters ───────────────────────────────────────────────────────────────

    @rx.event
    def set_form_account_type(self, value: str):
        self.form_account_type = value

    @rx.event
    def set_form_company_id(self, value: str):
        self.form_company_id = "" if value == "none" else value
        # Auto-fill form name from company if empty
        if self.form_company_id and not self.form_name.strip():
            for c in self.company_options:
                if c.id == self.form_company_id:
                    self.form_name = c.name
                    break

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
    def set_form_phone(self, value: str):
        self.form_phone = value

    @rx.event
    def set_form_email(self, value: str):
        self.form_email = value

    @rx.event
    def set_form_contact_first_name(self, value: str):
        self.form_contact_first_name = value
        self.form_contact_name = f"{self.form_contact_first_name} {self.form_contact_last_name}".strip()
        if self.form_account_type == "INDIVIDUAL":
            self.form_name = f"{self.form_contact_last_name} {self.form_contact_first_name}".strip()

    @rx.event
    def set_form_contact_last_name(self, value: str):
        self.form_contact_last_name = value
        self.form_contact_name = f"{self.form_contact_first_name} {self.form_contact_last_name}".strip()
        if self.form_account_type == "INDIVIDUAL":
            self.form_name = f"{self.form_contact_last_name} {self.form_contact_first_name}".strip()

    @rx.event
    def set_form_contact_name(self, value: str):
        self.form_contact_name = value

    @rx.event
    def select_patient_fill(self, patient_id: str, label: str):
        """Select a patient from the table and pre-fill the form with their contact details."""
        self.selected_patient_fill = patient_id
        self.patient_fill_selected_label = label
        if not patient_id:
            return
        try:
            from gws_care.patient.patient_service import PatientService
            patient = PatientService.get_patient(patient_id)
            self.form_name = patient.get_full_name()
            self.form_address = patient.address or ""
            self.form_postal_code = patient.postal_code or ""
            self.form_city = patient.city or ""
            self.form_phone = patient.phone or ""
            self.form_email = patient.email or ""
        except Exception as exc:
            pass

    @rx.event
    async def set_patient_fill_filter_name(self, value: str):
        self.patient_fill_filter_name = value
        await self._load_patient_fill_options()

    @rx.event
    async def set_patient_fill_filter_number(self, value: str):
        self.patient_fill_filter_number = value
        await self._load_patient_fill_options()

    @rx.event
    async def clear_patient_fill_filters(self):
        self.patient_fill_filter_name = ""
        self.patient_fill_filter_number = ""
        await self._load_patient_fill_options()

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
            others = sorted(n for n in names if n != "France")
            self.country_options = ["France"] + others
            priority = {n: i for i, n in enumerate(_PRIORITY_DIAL)}
            def _dial_key(opt: DialCodeOption):
                idx = priority.get(opt.name)
                return (0, idx) if idx is not None else (1, opt.name)
            self.dial_code_options = sorted(raw_dial, key=_dial_key)
        except Exception:
            pass

    # ── Internal loaders ─────────────────────────────────────────────────────

    async def _load_patient_fill_options(self) -> None:
        """Load patients into the fill selector, applying current filters."""
        self.patient_fill_is_loading = True
        try:
            from gws_care.patient.patient_service import PatientService
            name_term = self.patient_fill_filter_name.strip() or None
            raw_pn = self.patient_fill_filter_number.strip()
            if raw_pn.upper().startswith("PAT-"):
                raw_pn = raw_pn[4:]
            pn_prefix = f"PAT-{raw_pn}" if raw_pn else None
            patients = PatientService.search_patients(
                search=name_term,
                patient_number_prefix=pn_prefix,
                limit=50,
            )
            self.patient_fill_options = [
                PatientFillOption(
                    id=str(p.id),
                    display=p.get_full_name(),
                    patient_number=p.patient_number,
                    date_of_birth=p.date_of_birth.isoformat() if p.date_of_birth else "",
                    gender=p.gender or "",
                )
                for p in patients
            ]
        except Exception:
            pass
        finally:
            self.patient_fill_is_loading = False

    async def _load_company_options(self) -> None:
        """Load list of active companies for the company selector."""
        from gws_care.company.company_service import CompanyService
        companies = CompanyService.list_companies(active_only=True)
        self.company_options = [
            CompanyOption(id=str(c.id), name=c.name)
            for c in companies
        ]

    # ── Dialog open helpers ───────────────────────────────────────────────────

    @rx.event
    async def open_create_dialog(self):
        """Open the dialog in create mode."""
        self.is_update_mode = False
        self._editing_account_id = ""
        await self._clear_form_state()
        await self._load_patient_fill_options()
        await self._load_company_options()
        self.dialog_opened = True
        yield AccountFormState.fetch_countries

    @rx.event
    async def open_with_prefilled_data(
        self,
        last: str,
        first: str,
        phone: str,
        email: str,
        address: str,
        postal_code: str,
        city: str,
    ):
        """Open account creation dialog pre-filled with patient data.

        Called from PatientFormState.trigger_account_create which has already
        closed the patient form dialog before dispatching this event.
        """
        self.is_update_mode = False
        self._editing_account_id = ""
        await self._clear_form_state()
        await self._load_company_options()
        self._from_patient_form = True
        self.form_account_type = "INDIVIDUAL"
        if last:
            self.form_contact_last_name = last
        if first:
            self.form_contact_first_name = first
        if last or first:
            self.form_name = f"{last} {first}".strip()
        if phone:
            self.form_phone = phone
        if email:
            self.form_email = email
        if address:
            self.form_address = address
        if postal_code:
            self.form_postal_code = postal_code
        if city:
            self.form_city = city
        self.dialog_opened = True
        yield AccountFormState.fetch_countries

    @rx.event(background=True)
    async def open_create_dialog_from_patient(self):
        """Open account creation dialog from the patient form — keeps patient form open.

        Reads patient form data directly from PatientFormState via get_state.
        """
        from ..patient_list.patient_form_state import PatientFormState as PFS

        # get_state must be called inside async with self:
        async with self:
            patient_state = await self.get_state(PFS)

        last = (patient_state.form_last_name or "").strip()
        first = (patient_state.form_first_name or "").strip()
        phone = (patient_state.form_phone or "").strip()
        email = (patient_state.form_email or "").strip()
        address = (patient_state.form_address or "").strip()
        postal_code = (patient_state.form_postal_code or "").strip()
        city = (patient_state.form_city or "").strip()

        async with self:
            self.is_update_mode = False
            self._editing_account_id = ""
            await self._clear_form_state()
            await self._load_company_options()
            self._from_patient_form = True
            self.form_account_type = "INDIVIDUAL"
            if last:
                self.form_contact_last_name = last
            if first:
                self.form_contact_first_name = first
            if last or first:
                self.form_name = f"{last} {first}".strip()
            if phone:
                self.form_phone = phone
            if email:
                self.form_email = email
            if address:
                self.form_address = address
            if postal_code:
                self.form_postal_code = postal_code
            if city:
                self.form_city = city
            self.dialog_opened = True

        yield AccountFormState.fetch_countries

    @rx.event
    async def open_create_dialog_for_company(self, company_id: str, company_name: str):
        """Open account creation dialog pre-linked to a specific company."""
        self.is_update_mode = False
        self._editing_account_id = ""
        await self._clear_form_state()
        await self._load_company_options()
        self.form_company_id = company_id
        self.form_name = company_name
        self.form_account_type = "COMPANY"
        self.dialog_opened = True

    @rx.event
    async def open_edit_dialog(self, account_id: str):
        """Open the dialog in edit mode pre-filled with the account's data."""
        self.is_update_mode = True
        self._editing_account_id = account_id

        _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            from gws_care.account.account_service import AccountService
            a = AccountService.get_account(account_id)
            self.form_account_type = a.account_type or "COMPANY"
            self.form_company_id = a.company_id or ""
            self.form_name = a.name or ""
            self.form_registration_number = a.registration_number or ""
            self.form_address = a.address or ""
            self.form_postal_code = a.postal_code or ""
            self.form_city = a.city or ""
            self.form_phone = a.phone or ""
            self.form_email = a.email or ""
            self.form_contact_first_name = a.contact_first_name or ""
            self.form_contact_last_name = a.contact_last_name or ""
            self.form_contact_name = a.contact_name or ""
            self.form_country = "France"
            self.country_filter = "France"
            self.address_manual_mode = False
            self.address_suggestions = []
            self.show_address_suggestions = False
            self.show_country_suggestions = False

        await self._load_patient_fill_options()
        await self._load_company_options()
        self.dialog_opened = True
        yield AccountFormState.fetch_countries

    # ── FormDialogState abstract method implementations ───────────────────────

    async def _clear_form_state(self) -> None:
        self.form_account_type = "COMPANY"
        self.form_company_id = ""
        self.form_name = ""
        self.form_registration_number = ""
        self.form_address = ""
        self.form_postal_code = ""
        self.form_city = ""
        self.form_phone = ""
        self.form_phone_dial_code = "+33"
        self.dial_code_filter = "🇫🇷 +33"
        self.filtered_dial_codes = []
        self.show_dial_code_suggestions = False
        self.form_email = ""
        self.form_contact_first_name = ""
        self.form_contact_last_name = ""
        self.form_contact_name = ""
        self.form_country = "France"
        self.country_filter = "France"
        self.filtered_countries = []
        self.show_country_suggestions = False
        self.address_suggestions = []
        self.show_address_suggestions = False
        self.address_manual_mode = False
        self.is_fetching_suggestions = False
        self.selected_patient_fill = ""
        self.patient_fill_selected_label = ""
        self.patient_fill_filter_name = ""
        self.patient_fill_filter_number = ""
        self._editing_account_id = ""
        self.is_update_mode = False
        self.form_error = ""
        self._from_patient_form = False

    def _build_save_dto(self):
        from gws_care.account.account_dto import SaveAccountDTO
        name = self.form_name.strip()
        if not name and self.form_account_type == "INDIVIDUAL":
            name = f"{self.form_contact_last_name} {self.form_contact_first_name}".strip()
        return name, SaveAccountDTO(
            account_type=self.form_account_type,
            company_id=self.form_company_id or None,
            name=name,
            registration_number=self.form_registration_number or None,
            address=self.form_address or None,
            postal_code=self.form_postal_code or None,
            city=self.form_city or None,
            phone=self.form_phone or None,
            email=self.form_email or None,
            contact_first_name=self.form_contact_first_name or None,
            contact_last_name=self.form_contact_last_name or None,
            contact_name=self.form_contact_name or None,
        )

    async def _create(self, form_data: dict) -> AsyncGenerator:
        """Create a new account from form data."""
        from gws_care.account.account_service import AccountService

        async with self:
            self.form_error = ""
        name, dto = self._build_save_dto()
        if not name:
            async with self:
                self.form_error = "Account name is required"
            return

        async with self:
            _main = await self.get_state(ReflexMainState)
            patient_to_link = self.selected_patient_fill
            from_patient = self._from_patient_form
        with await _main.authenticate_user():
            account = AccountService.create_account(dto)
            if patient_to_link:
                from gws_care.patient.patient_service import PatientService
                try:
                    PatientService.add_account(patient_to_link, str(account.id))
                except Exception:
                    pass

        yield rx.toast.success(f"Account '{account.name}' created")

        if from_patient:
            from ..patient_list.patient_form_state import PatientFormState
            yield PatientFormState.select_account(str(account.id), account.name)
        else:
            from ..account_list.account_list_state import AccountListState
            yield AccountListState.on_load()

    async def _update(self, form_data: dict) -> AsyncGenerator:
        """Update an existing account from form data."""
        from gws_care.account.account_service import AccountService

        async with self:
            self.form_error = ""
        name, dto = self._build_save_dto()
        if not name:
            async with self:
                self.form_error = "Account name is required"
            return

        async with self:
            _main = await self.get_state(ReflexMainState)
            patient_to_link = self.selected_patient_fill
            account_id = self._editing_account_id
        with await _main.authenticate_user():
            AccountService.update_account(account_id, dto)
            if patient_to_link:
                from gws_care.patient.patient_service import PatientService
                try:
                    PatientService.add_account(patient_to_link, account_id)
                except Exception:
                    pass

        yield rx.toast.success("Account updated successfully")

        from ..account_list.account_list_state import AccountListState
        yield AccountListState.on_load()
        try:
            from ..account_detail.account_detail_state import AccountDetailState
            yield AccountDetailState.on_load()
        except Exception:
            pass
