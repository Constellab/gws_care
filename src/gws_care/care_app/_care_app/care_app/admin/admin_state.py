"""State for the Admin panel — user role management."""

import reflex as rx
from pydantic import BaseModel

from ..common.role_state import RoleState


class UserRoleRowDTO(BaseModel):
    """Represents a user with their assigned role list for the admin panel."""

    id: str
    full_name: str
    email: str
    roles: list[str]   # list of CareRole values
    linked_account_id: str = ""
    linked_patient_id: str = ""

    @property
    def is_admin(self) -> bool:
        return "SUPER_ADMIN_PSC" in self.roles or "ADMIN_PSC" in self.roles

    @property
    def is_doctor(self) -> bool:
        return "MEDECIN_PSC" in self.roles

    @property
    def is_operator(self) -> bool:
        return "OPERATEUR_TERRAIN" in self.roles or "OPERATEUR_LABO" in self.roles

    @property
    def is_account_admin(self) -> bool:
        return "RH_ENTREPRISE" in self.roles or "MEDECIN_ENTREPRISE" in self.roles

    @property
    def is_patient_user(self) -> bool:
        return "PATIENT" in self.roles


class EntityOption(BaseModel):
    id: str
    label: str


class StaffContactDTO(BaseModel):
    """One staff member shown in the Annuaire directory tab."""

    id: str
    full_name: str
    email: str
    role: str
    role_label: str
    linked_account_name: str = ""


class AdminState(RoleState):
    """State for the /admin page."""

    users: list[UserRoleRowDTO] = []
    staff_contacts: list[StaffContactDTO] = []
    is_loading: bool = False
    error_message: str = ""
    success_message: str = ""

    # Options for the linked-entity selectors
    account_options: list[EntityOption] = []
    patient_options: list[EntityOption] = []

    # Per-user pending link selections (user_id → entity_id)
    _pending_account_links: dict[str, str] = {}
    _pending_patient_links: dict[str, str] = {}

    @rx.event
    async def on_load(self):
        await self._load_roles()
        await self._load_users()
        await self._load_entity_options()
        await self._load_staff_contacts()

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
        """Save the linked account for a RH_ENTREPRISE or MEDECIN_ENTREPRISE user."""
        self.error_message = ""
        self.success_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_role_service import UserRoleService
                roles = UserRoleService.get_roles_for_user(user_id)
                # Link for whichever company role the user has
                for role in (CareRole.RH_ENTREPRISE, CareRole.MEDECIN_ENTREPRISE):
                    if role in roles:
                        UserRoleService.assign_role_with_link(
                            user_id, role, linked_account_id=account_id or None
                        )
                self.success_message = "Compte lié enregistré."
            await self._load_users()
        except Exception as e:
            self.error_message = f"Erreur lors de la liaison compte : {e}"

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
                self.users = [
                    UserRoleRowDTO(
                        id=r["id"],
                        full_name=r["full_name"],
                        email=r["email"],
                        roles=r["roles"],
                        linked_account_id=r.get("linked_account_id") or "",
                        linked_patient_id=r.get("linked_patient_id") or "",
                    )
                    for r in rows
                ]
        except Exception as e:
            self.error_message = f"Error loading users: {e}"
        finally:
            self.is_loading = False

    async def _load_entity_options(self):
        """Load account and patient lists for the link selectors."""
        try:
            with await self.authenticate_user():
                from gws_care.account.account_service import AccountService
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
        except Exception:
            pass

    async def _load_staff_contacts(self):
        """Load all staff members with medical/HR roles, grouped for the Annuaire tab."""
        try:
            with await self.authenticate_user():
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_role_service import UserRoleService
                from gws_care.account.account_service import AccountService
                from gws_care.user.user import User
                from gws_care.role.user_care_role import UserCareRole

                _role_labels = {
                    CareRole.MEDECIN_PSC: "Médecin PSC",
                    CareRole.MEDECIN_ENTREPRISE: "Médecin Entreprise",
                    CareRole.RH_ENTREPRISE: "RH Entreprise",
                }

                contacts: list[StaffContactDTO] = []
                # Get all UserCareRole rows for the staff roles we care about
                rows = list(
                    UserCareRole.select(UserCareRole, User)
                    .join(User)
                    .where(UserCareRole.role.in_(list(_role_labels.keys())))
                    .order_by(User.last_name)
                )

                for row in rows:
                    user = row.user
                    role_label = _role_labels.get(row.role, row.role)
                    acct_name = ""
                    if row.linked_account_id:
                        try:
                            a = AccountService.get_account(row.linked_account_id)
                            acct_name = a.name
                        except Exception:
                            pass
                    # role may be a CareRole enum or a plain string depending on Peewee version
                    raw_role = row.role
                    role_key = raw_role if isinstance(raw_role, CareRole) else CareRole(raw_role)
                    role_label = _role_labels.get(role_key, str(raw_role))
                    contacts.append(StaffContactDTO(
                        id=str(user.id),
                        full_name=f"{user.first_name} {user.last_name}",
                        email=user.email,
                        role=role_key.value,
                        role_label=role_label,
                        linked_account_name=acct_name,
                    ))
                self.staff_contacts = contacts
        except Exception:
            pass
