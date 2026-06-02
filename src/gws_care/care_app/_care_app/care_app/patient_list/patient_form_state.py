"""State for the patient create / edit form dialog."""

from typing import AsyncGenerator

import reflex as rx
from pydantic import BaseModel
from gws_reflex_base import FormDialogState
from gws_reflex_main import ReflexMainState


class CompanyOption(BaseModel):
    """Lightweight company option for dropdown."""
    id: str
    name: str


class DoctorOption(BaseModel):
    """Doctor available for selection as primary physician."""
    user_id: str = ""
    name: str = ""
    role_label: str = ""


class PatientFormState(FormDialogState, rx.State):
    """Manages the create / update patient dialog.

    Inherits `FormDialogState` for dialog lifecycle and `submit_form` dispatch.
    """

    # Form fields (public — bound to inputs in the UI)
    form_last_name: str = ""
    form_first_name: str = ""
    form_birth_name: str = ""
    form_date_of_birth: str = ""
    form_gender: str = "M"
    form_phone: str = ""
    form_email: str = ""
    form_address: str = ""
    form_postal_code: str = ""
    form_city: str = ""
    form_primary_physician_name: str = ""
    form_primary_physician_phone: str = ""
    # Doctor directory dropdown
    doctor_options: list[DoctorOption] = []
    form_physician_user_id: str = ""  # "" = free text mode

    # Set when editing an existing patient
    _editing_patient_id: str = ""
    # Account id of the patient being edited (preserved across updates)
    _form_account_id: str = ""
    # When creating from an account detail page, pre-link to this account
    _context_account_id: str = ""
    # When creating from a company detail page, pre-link to this company
    _context_company_id: str = ""

    # Company dropdown (shown in standalone create dialog)
    form_company_id: str = ""
    company_options: list[CompanyOption] = []
    form_error: str = ""

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
    def set_form_postal_code(self, value: str):
        self.form_postal_code = value

    @rx.event
    def set_form_city(self, value: str):
        self.form_city = value

    @rx.event
    def set_form_primary_physician_name(self, value: str):
        self.form_primary_physician_name = value

    @rx.event
    def set_form_primary_physician_phone(self, value: str):
        self.form_primary_physician_phone = value

    @rx.event
    def select_physician_from_directory(self, user_id: str):
        """Select a doctor from the directory; populate name from stored options."""
        if user_id == "__other__":
            self.form_physician_user_id = "__other__"
            self.form_primary_physician_name = ""
            return
        for opt in self.doctor_options:
            if opt.user_id == user_id:
                self.form_physician_user_id = user_id
                self.form_primary_physician_name = opt.name
                return
        # Fallback
        self.form_physician_user_id = user_id
    @rx.event
    def set_form_company_id(self, value: str):
        self.form_company_id = "" if value == "__none__" else value
    # ── Dialog open helpers ───────────────────────────────────────────────────

    @rx.event
    async def open_create_dialog(self):
        """Open the dialog in create mode with blank fields."""
        self.is_update_mode = False
        self._editing_patient_id = ""
        self._context_account_id = ""
        await self._clear_form_state()
        # Load company options
        _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            from gws_care.company.company_service import CompanyService
            companies = CompanyService.list_companies(active_only=True)
            self.company_options = [
                CompanyOption(id=str(c.id), name=c.name)
                for c in sorted(companies, key=lambda c: c.name)
            ]
            await self._load_doctor_options(_main)
        self.dialog_opened = True

    @rx.event
    async def open_create_for_account(self, account_id: str):
        """Open the create dialog pre-linked to an account."""
        self.is_update_mode = False
        self._editing_patient_id = ""
        self._context_company_id = ""
        await self._clear_form_state()
        # Set AFTER _clear_form_state so it is not wiped
        self._context_account_id = account_id
        self.dialog_opened = True

    @rx.event
    async def open_create_for_company(self, company_id: str):
        """Open the create dialog pre-linked to a company."""
        self.is_update_mode = False
        self._editing_patient_id = ""
        self._context_account_id = ""
        await self._clear_form_state()
        # Set AFTER _clear_form_state so it is not wiped
        self._context_company_id = company_id
        _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            await self._load_doctor_options(_main)
        self.dialog_opened = True

    @rx.event
    async def open_edit_dialog(self, patient_id: str):
        """Open the dialog in edit mode pre-filled with the patient's data.

        :param patient_id: DB id of the patient to edit
        :type patient_id: str
        """
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
            self.form_address = p.address or ""
            self.form_postal_code = p.postal_code or ""
            self.form_city = p.city or ""
            self.form_primary_physician_name = p.primary_physician_name or ""
            self.form_primary_physician_phone = p.primary_physician_phone or ""
            self._form_account_id = str(p.billing_account_id) if p.billing_account_id else ""
            self.form_company_id = str(p.company_id) if p.company_id else ""
            self.form_physician_user_id = ""
            await self._load_doctor_options(_main)

        self.dialog_opened = True

    # ── FormDialogState abstract method implementations ───────────────────────

    async def _clear_form_state(self) -> None:
        self.form_last_name = ""
        self.form_first_name = ""
        self.form_birth_name = ""
        self.form_date_of_birth = ""
        self.form_gender = "M"
        self.form_phone = ""
        self.form_email = ""
        self.form_address = ""
        self.form_postal_code = ""
        self.form_city = ""
        self.form_primary_physician_name = ""
        self.form_primary_physician_phone = ""
        self.form_physician_user_id = ""
        self._editing_patient_id = ""
        self._form_account_id = ""
        self.form_company_id = ""
        self.is_update_mode = False
        self.form_error = ""
        # Note: _context_account_id and _context_company_id are NOT cleared here
        # — they are set by the open_create_for_* methods and must survive until _create runs.

    async def _load_doctor_options(self, _main=None) -> None:
        """Load all doctors from the staff directory for the physician dropdown."""
        try:
            from gws_care.role.care_role import CareRole
            from gws_care.role.user_role_service import UserRoleService

            rows = UserRoleService.list_users_with_roles()
            options: list[DoctorOption] = []
            doctor_roles = {CareRole.MEDECIN_PSC.value, CareRole.MEDECIN_ENTREPRISE.value}
            seen: set[str] = set()
            doctor_rows = [
                row for row in rows
                if any(r in doctor_roles for r in row.get("roles", []))
            ]
            for row in doctor_rows:
                uid = row["id"]
                if uid in seen:
                    continue
                seen.add(uid)
                full_name = row.get("full_name", "").strip()
                if not full_name:
                    full_name = row.get("email", "Médecin")
                role_label = ", ".join(
                    CareRole(r).get_label()
                    for r in row.get("roles", [])
                    if r in doctor_roles
                )
                specialty = row.get("specialty", "") or ""
                display = full_name
                if specialty:
                    display = f"{full_name} — {specialty}"
                options.append(DoctorOption(
                    user_id=uid,
                    name=display,
                    role_label=role_label,
                ))
            self.doctor_options = options
        except Exception as exc:
            from gws_core.core.utils.logger import Logger
            Logger.error(f"[patient_form] _load_doctor_options failed: {exc}")
            self.doctor_options = []

    async def _create(self, form_data: dict) -> AsyncGenerator:
        """Create a new patient from form data."""
        from datetime import date as date_type

        from gws_care.patient.patient_dto import SavePatientDTO
        from gws_care.patient.patient_service import PatientService

        async with self:
            self.form_error = ""
        last_name = self.form_last_name.strip()
        first_name = self.form_first_name.strip()

        if not last_name:
            async with self:
                self.form_error = "Last name is required"
            return
        if not first_name:
            async with self:
                self.form_error = "First name is required"
            return
        if not self.form_date_of_birth:
            async with self:
                self.form_error = "Date of birth is required"
            return
        if not self.form_email.strip():
            async with self:
                self.form_error = "L'adresse email est obligatoire"
            return

        dto = SavePatientDTO(
            last_name=last_name,
            first_name=first_name,
            birth_name=self.form_birth_name or None,
            date_of_birth=date_type.fromisoformat(self.form_date_of_birth),
            gender=self.form_gender,
            phone=self.form_phone or None,
            email=self.form_email.strip(),
            address=self.form_address or None,
            postal_code=self.form_postal_code or None,
            city=self.form_city or None,
            primary_physician_name=self.form_primary_physician_name or None,
            primary_physician_phone=self.form_primary_physician_phone or None,
            account_id=self._context_account_id or None,
        )

        # Capture context IDs into locals before any yield (state may be
        # cleared by _clear_form_state before the post-yield refresh logic).
        ctx_company_id = self._context_company_id
        ctx_account_id = self._context_account_id

        async with self:
            _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            patient = PatientService.create_patient(dto)
            company_id = ctx_company_id or self.form_company_id or None
            if company_id:
                PatientService.assign_company(str(patient.id), company_id)

        yield rx.toast.success(f"Patient {patient.patient_number} created")

        if ctx_company_id:
            from ..company_detail.company_detail_state import CompanyDetailState
            yield CompanyDetailState.on_load()
        elif ctx_account_id:
            from ..account_detail.account_detail_state import AccountDetailState
            yield AccountDetailState.on_load()
        else:
            from ..patient_list.patient_list_state import PatientListState
            yield PatientListState.on_load()

    async def _update(self, form_data: dict) -> AsyncGenerator:
        """Update an existing patient from form data."""
        from datetime import date as date_type

        from gws_care.patient.patient_dto import SavePatientDTO
        from gws_care.patient.patient_service import PatientService

        async with self:
            self.form_error = ""
        last_name = self.form_last_name.strip()
        first_name = self.form_first_name.strip()

        if not last_name:
            async with self:
                self.form_error = "Last name is required"
            return
        if not first_name:
            async with self:
                self.form_error = "First name is required"
            return
        if not self.form_date_of_birth:
            async with self:
                self.form_error = "Date of birth is required"
            return
        if not self.form_email.strip():
            async with self:
                self.form_error = "L'adresse email est obligatoire"
            return

        dto = SavePatientDTO(
            last_name=last_name,
            first_name=first_name,
            birth_name=self.form_birth_name or None,
            date_of_birth=date_type.fromisoformat(self.form_date_of_birth),
            gender=self.form_gender,
            phone=self.form_phone or None,
            email=self.form_email.strip(),
            address=self.form_address or None,
            postal_code=self.form_postal_code or None,
            city=self.form_city or None,
            primary_physician_name=self.form_primary_physician_name or None,
            primary_physician_phone=self.form_primary_physician_phone or None,
            account_id=self._form_account_id or None,
        )

        async with self:
            _main = await self.get_state(ReflexMainState)
        with await _main.authenticate_user():
            PatientService.update_patient(self._editing_patient_id, dto)
            company_id = self.form_company_id or None
            PatientService.assign_company(self._editing_patient_id, company_id)

        yield rx.toast.success("Patient updated successfully")

        from ..patient_detail.patient_detail_state import PatientDetailState
        yield PatientDetailState.on_load()
