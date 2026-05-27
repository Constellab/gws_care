"""State for the Admin panel — user role management."""

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


class EntityOption(BaseModel):
    id: str = ""
    label: str = ""


class UserRoleRowDTO(BaseModel):
    """Represents a user with their assigned role list for the admin panel."""

    id: str
    full_name: str
    email: str
    roles: list[str]   # list of CareRole values
    linked_patient_id: str = ""
    linked_doctor_id: str = ""
    account_admin_accounts: list[EntityOption] = []


class AdminState(RoleState):
    """State for the /admin page."""

    users: list[UserRoleRowDTO] = []
    is_loading: bool = False
    error_message: str = ""
    success_message: str = ""

    # Filter for the user roles table
    user_name_filter: str = ""

    # Options for the linked-entity selectors
    account_options: list[EntityOption] = []
    patient_options: list[EntityOption] = []
    doctor_options: list[EntityOption] = []

    @rx.event
    def set_user_name_filter(self, value: str):
        self.user_name_filter = value

    @rx.var
    def filtered_users(self) -> list[UserRoleRowDTO]:
        """Users filtered by name (case-insensitive)."""
        if not self.user_name_filter:
            return self.users
        needle = self.user_name_filter.lower()
        return [
            u for u in self.users
            if needle in u.full_name.lower() or needle in u.email.lower()
        ]

    # Per-user pending link selections (user_id → entity_id)
    _pending_account_links: dict[str, str] = {}
    _pending_patient_links: dict[str, str] = {}

    @rx.event
    async def on_load(self):
        await self._load_roles()
        redirect = await self._require_any_of(self.is_admin)
        if redirect:
            return redirect
        # Load options first so labels are available for chip resolution in _load_users
        await self._load_entity_options()
        await self._load_users()

    @rx.event
    async def toggle_role(self, user_id: str, role: str):
        """Toggle a CareRole for a user (assign if missing, revoke if present)."""
        self.error_message = ""
        self.success_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_role_service import UserRoleService

                care_role = CareRole(role)
                if UserRoleService.has_role(user_id, care_role):
                    UserRoleService.revoke_role(user_id, care_role)
                    self.success_message = f"Role '{care_role.get_label()}' revoked."
                else:
                    # For ACCOUNT_ADMIN / PATIENT, assign without link first;
                    # user can set the link via the selector that appears.
                    UserRoleService.assign_role(user_id, care_role)
                    self.success_message = f"Role '{care_role.get_label()}' assigned."
            await self._load_users()
        except Exception as e:
            self.error_message = f"Error updating role: {e}"

    @rx.event
    async def set_account_link(self, user_id: str, account_id: str):
        """Save the linked account for an ACCOUNT_ADMIN user (legacy, replaced by add/remove)."""
        await self._add_account_link(user_id, "ACCOUNT_ADMIN", account_id)

    @rx.event
    async def add_account_link(self, user_id: str, role: str, account_id: str):
        """Add an account link for ACCOUNT_ADMIN or DOCTOR role."""
        self.error_message = ""
        self.success_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_role_service import UserRoleService
                UserRoleService.add_account_link(user_id, CareRole(role), account_id)
                self.success_message = "Account added."
            await self._load_users()
        except Exception as e:
            self.error_message = f"Error adding account: {e}"

    @rx.event
    async def remove_account_link(self, user_id: str, role: str, account_id: str):
        """Remove an account link for ACCOUNT_ADMIN or DOCTOR role."""
        self.error_message = ""
        self.success_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_role_service import UserRoleService
                UserRoleService.remove_account_link(user_id, CareRole(role), account_id)
                self.success_message = "Account removed."
            await self._load_users()
        except Exception as e:
            self.error_message = f"Error removing account: {e}"

    @rx.event
    async def set_doctor_link(self, user_id: str, doctor_id: str):
        """Link a user with the DOCTOR role to a registered MedicalDoctor profile."""
        self.error_message = ""
        self.success_message = ""
        effective_id = None if (not doctor_id or doctor_id == "__none__") else doctor_id
        try:
            with await self.authenticate_user():
                from gws_care.role.user_role_service import UserRoleService
                UserRoleService.set_doctor_link(user_id, effective_id)
                self.success_message = "Doctor link updated."
            await self._load_users()
        except Exception as e:
            self.error_message = f"Error updating doctor link: {e}"

    async def _add_account_link(self, user_id: str, role: str, account_id: str):
        try:
            with await self.authenticate_user():
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_role_service import UserRoleService
                UserRoleService.add_account_link(user_id, CareRole(role), account_id)
            await self._load_users()
        except Exception as e:
            self.error_message = f"Error saving account link: {e}"

    @rx.event
    async def set_patient_link(self, user_id: str, patient_id: str):
        """Save the linked patient for a PATIENT user."""
        self.error_message = ""
        self.success_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_role_service import UserRoleService
                UserRoleService.assign_role_with_link(
                    user_id, CareRole.PATIENT, linked_patient_id=patient_id or None
                )
                self.success_message = "Patient link saved."
            await self._load_users()
        except Exception as e:
            self.error_message = f"Error saving patient link: {e}"

    async def _load_users(self):
        if not await self.check_authentication():
            return
        self.is_loading = True
        try:
            with await self.authenticate_user():
                from gws_care.role.user_role_service import UserRoleService
                rows = UserRoleService.list_users_with_roles()
                # Build id→label lookup maps from already-loaded options
                patient_map = {opt.id: opt.label for opt in self.patient_options}
                account_map = {opt.id: opt.label for opt in self.account_options}
                self.users = [
                    UserRoleRowDTO(
                        id=r["id"],
                        full_name=r["full_name"],
                        email=r["email"],
                        roles=r["roles"],
                        linked_patient_id=r.get("linked_patient_id") or "",
                        linked_doctor_id=r.get("linked_doctor_id") or "",
                        account_admin_accounts=[
                            EntityOption(id=aid, label=account_map.get(aid, aid))
                            for aid in (r.get("account_admin_account_ids") or [])
                        ],
                    )
                    for r in rows
                ]
        except Exception as e:
            self.error_message = f"Error loading users: {e}"
        finally:
            self.is_loading = False

    async def _load_entity_options(self):
        """Load account, patient and doctor lists for the link selectors."""
        try:
            with await self.authenticate_user():
                from gws_care.account.account_service import AccountService
                from gws_care.doctor.medical_doctor_service import MedicalDoctorService
                from gws_care.patient.patient_service import PatientService

                accounts = AccountService.list_accounts()
                self.account_options = [
                    EntityOption(id=str(a.id), label=a.name)
                    for a in accounts
                ]
                patients = PatientService.search_patients()
                self.patient_options = [
                    EntityOption(
                        id=str(p.id),
                        label=f"{p.last_name} {p.first_name} ({p.patient_number})",
                    )
                    for p in patients
                ]
                doctors = MedicalDoctorService.list_doctors(active_only=True)
                self.doctor_options = [
                    EntityOption(id=d.id, label=d.full_name)
                    for d in doctors
                ]
        except Exception:
            pass
