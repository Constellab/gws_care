"""State for the user management page (US-001, US-002)."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from pydantic import BaseModel


class UserRowDTO(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    is_active: bool
    roles: list[str] = []
    role_labels: list[str] = []
    linked_account_id: str | None = None
    linked_account_name: str | None = None


class UserFormDTO(BaseModel):
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    role: str = ""
    is_active: bool = True
    linked_account_id: str | None = None


class AccountOptionDTO(BaseModel):
    id: str
    name: str


class UserManagementState(ReflexMainState):
    users: list[UserRowDTO] = []
    is_loading: bool = False
    error: str = ""
    # Tabs: psc / enterprise
    active_tab: str = "psc"
    # Dialog
    dialog_open: bool = False
    is_editing: bool = False
    edit_user_id: str | None = None
    form: UserFormDTO = UserFormDTO()
    form_error: str = ""
    is_saving: bool = False
    # Account options for enterprise user selection
    account_options: list[AccountOptionDTO] = []

    # Confirm révocation rôles
    confirm_revoke_open: bool = False
    confirm_revoke_user_id: str = ""
    confirm_revoke_user_email: str = ""

    _PSC_ROLES = ["SUPER_ADMIN_PSC", "ADMIN_PSC", "OPERATEUR_TERRAIN", "OPERATEUR_LABO", "MEDECIN_PSC"]
    _ENTERPRISE_ROLES = ["MEDECIN_ENTREPRISE", "RH_ENTREPRISE"]

    @rx.event
    async def on_load(self):
        await self._load_users()

    @rx.event
    def set_tab(self, tab: str):
        self.active_tab = tab

    @rx.event
    async def open_create_dialog(self):
        self.form = UserFormDTO()
        self.form_error = ""
        self.is_editing = False
        self.edit_user_id = None
        await self._load_account_options()
        self.dialog_open = True

    @rx.event
    def close_dialog(self):
        self.dialog_open = False
        self.form_error = ""

    @rx.event
    def set_first_name(self, v: str):
        self.form = UserFormDTO(**{**self.form.dict(), "first_name": v})

    @rx.event
    def set_last_name(self, v: str):
        self.form = UserFormDTO(**{**self.form.dict(), "last_name": v})

    @rx.event
    def set_email(self, v: str):
        self.form = UserFormDTO(**{**self.form.dict(), "email": v})

    @rx.event
    def set_role(self, v: str):
        self.form = UserFormDTO(**{**self.form.dict(), "role": v})

    @rx.event
    def set_is_active(self, v: bool):
        self.form = UserFormDTO(**{**self.form.dict(), "is_active": v})

    @rx.event
    def set_linked_account(self, v: str):
        # "_none_" is the sentinel value for the "— Aucun —" select item (empty string is forbidden)
        clean = v if v and v != "_none_" else None
        self.form = UserFormDTO(**{**self.form.dict(), "linked_account_id": clean})

    @rx.event
    async def save_user(self):
        if not self.form.email.strip():
            self.form_error = "L'email est obligatoire."
            return
        if not self.form.role:
            self.form_error = "Le rôle est obligatoire."
            return
        self.is_saving = True
        self.form_error = ""
        try:
            with await self.authenticate_user():
                import uuid as _uuid
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_role_service import UserRoleService
                from gws_care.user.user import User

                email = self.form.email.strip()
                first_name = self.form.first_name.strip()
                last_name = self.form.last_name.strip()

                # Find existing Care user by email, or create one directly
                care_user = User.get_or_none(User.email == email)
                if care_user is None:
                    # Also check in gws_core and sync if found
                    try:
                        from gws_core.user.user_service import UserService as GwsCoreUserService
                        core_user = GwsCoreUserService.get_user_by_email(email)
                        if core_user is not None:
                            # Sync the gws_core user into gws_care_user
                            from gws_care.user.care_user_sync_service import CareUserSyncService
                            CareUserSyncService().sync_user(core_user)
                            care_user = User.get_or_none(User.email == email)
                    except Exception:
                        pass

                if care_user is None:
                    # Create directly in gws_care_user (no gws_core account needed)
                    care_user = User()
                    care_user.id = str(_uuid.uuid4())
                    care_user.email = email
                    care_user.first_name = first_name or email.split("@")[0]
                    care_user.last_name = last_name or ""
                    care_user.is_active = self.form.is_active
                    care_user.save(force_insert=True)
                else:
                    # Update name if explicitly provided
                    changed = False
                    if first_name and care_user.first_name != first_name:
                        care_user.first_name = first_name
                        changed = True
                    if last_name and care_user.last_name != last_name:
                        care_user.last_name = last_name
                        changed = True
                    if changed:
                        care_user.save()

                user_id = str(care_user.id)

                # Check duplicate roles (on create only)
                if not self.is_editing:
                    existing_roles = UserRoleService.get_roles_for_user(user_id)
                    if existing_roles:
                        raise ValueError("Cet utilisateur a déjà des rôles assignés dans Constellab Care.")

                # 4. Assign Care role
                role = CareRole(self.form.role)
                linked_account = self.form.linked_account_id or None
                UserRoleService.assign_role_with_link(
                    user_id=user_id,
                    role=role,
                    linked_account_id=linked_account,
                    linked_patient_id=None,
                )
                if not self.form.is_active:
                    care_user.is_active = False
                    care_user.save()
            self.dialog_open = False
            await self._load_users()
        except Exception as e:
            self.form_error = str(e)
        finally:
            self.is_saving = False

    @rx.event
    async def toggle_active(self, user_id: str):
        try:
            with await self.authenticate_user():
                from gws_care.user.user import User
                user = User.get_by_id_and_check(user_id)
                user.is_active = not user.is_active
                user.save()
            await self._load_users()
        except Exception as e:
            self.error = str(e)

    @rx.event
    def open_confirm_revoke(self, user_id: str, email: str):
        self.confirm_revoke_user_id = user_id
        self.confirm_revoke_user_email = email
        self.confirm_revoke_open = True

    @rx.event
    def dismiss_confirm_revoke(self):
        self.confirm_revoke_open = False
        self.confirm_revoke_user_id = ""
        self.confirm_revoke_user_email = ""

    @rx.event
    async def confirmed_revoke(self):
        user_id = self.confirm_revoke_user_id
        self.confirm_revoke_open = False
        self.confirm_revoke_user_id = ""
        self.confirm_revoke_user_email = ""
        try:
            with await self.authenticate_user():
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_role_service import UserRoleService
                roles = UserRoleService.get_roles_for_user(user_id)
                for role in roles:
                    UserRoleService.revoke_role(user_id, role)
            await self._load_users()
        except Exception as e:
            self.error = str(e)

    async def _load_users(self):
        try:
            with await self.authenticate_user():
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_role_service import UserRoleService
                from gws_care.role.user_care_role import UserCareRole
                from gws_care.user.user import User

                # Load all users that have at least one care role
                rows = UserRoleService.list_users_with_roles()
                self.users = []
                for row in rows:
                    role_values = row.get("roles", [])
                    role_labels = []
                    for rv in role_values:
                        try:
                            role_labels.append(CareRole(rv).get_label())
                        except ValueError:
                            role_labels.append(rv)

                    linked_acc_id = row.get("linked_account_id") or None
                    linked_acc_name = None
                    if linked_acc_id:
                        try:
                            from gws_care.account.account import Account
                            acc = Account.get_by_id(linked_acc_id)
                            linked_acc_name = acc.name if acc else None
                        except Exception:
                            pass

                    # Also pick up linked_account_id from any RH/MEDECIN_ENTREPRISE row
                    if not linked_acc_id:
                        try:
                            linked_acc_id = UserRoleService.get_linked_account_id(row["id"]) or None
                            if linked_acc_id:
                                from gws_care.account.account import Account
                                acc = Account.get_by_id(linked_acc_id)
                                linked_acc_name = acc.name if acc else None
                        except Exception:
                            pass

                    # full_name split
                    full_name = row.get("full_name", "")
                    parts = full_name.strip().split(" ", 1)
                    first = parts[0] if parts else ""
                    last = parts[1] if len(parts) > 1 else ""

                    self.users.append(UserRowDTO(
                        id=row["id"],
                        email=row.get("email", ""),
                        first_name=first,
                        last_name=last,
                        is_active=True,
                        roles=role_values,
                        role_labels=role_labels,
                        linked_account_id=linked_acc_id,
                        linked_account_name=linked_acc_name,
                    ))
        except Exception as e:
            self.error = str(e)

    async def _load_account_options(self):
        try:
            with await self.authenticate_user():
                from gws_care.account.account import Account
                accounts = Account.select().where(Account.is_active == True).order_by(Account.name)
                self.account_options = [
                    AccountOptionDTO(id=str(a.id), name=a.name) for a in accounts
                ]
        except Exception:
            self.account_options = []
