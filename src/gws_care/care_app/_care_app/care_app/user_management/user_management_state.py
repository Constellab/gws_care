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
    specialty: str = ""


class UserFormDTO(BaseModel):
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    role: str = ""
    is_active: bool = True
    linked_account_id: str = ""
    specialty: str = ""


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
    edit_user_id: str = ""
    form: UserFormDTO = UserFormDTO()
    form_error: str = ""
    is_saving: bool = False
    # Account options for enterprise user selection
    account_options: list[AccountOptionDTO] = []

    # Confirm révocation rôles
    confirm_revoke_open: bool = False
    confirm_revoke_user_id: str = ""
    confirm_revoke_user_email: str = ""
    confirm_revoke_motif: str = ""

    _PSC_ROLES = ["SUPER_ADMIN_PSC", "ADMIN_PSC", "OPERATEUR_TERRAIN", "OPERATEUR_LABO", "MEDECIN_PSC"]
    _ENTERPRISE_ROLES = ["MEDECIN_ENTREPRISE", "RH_ENTREPRISE"]

    # ── Grouped @rx.var for the staff directory ─────────────────────────────

    @rx.var
    def medecin_psc_users(self) -> list[UserRowDTO]:
        return [u for u in self.users if "MEDECIN_PSC" in u.roles]

    @rx.var
    def medecin_enterprise_users(self) -> list[UserRowDTO]:
        return [u for u in self.users if "MEDECIN_ENTREPRISE" in u.roles]

    @rx.var
    def admin_users(self) -> list[UserRowDTO]:
        _admin = {"SUPER_ADMIN_PSC", "ADMIN_PSC", "DIRECTEUR_PSC"}
        return [u for u in self.users if any(r in _admin for r in u.roles)]

    @rx.var
    def operator_users(self) -> list[UserRowDTO]:
        _ops = {"OPERATEUR_TERRAIN", "OPERATEUR_LABO"}
        return [u for u in self.users if any(r in _ops for r in u.roles)]

    @rx.var
    def rh_users(self) -> list[UserRowDTO]:
        return [u for u in self.users if "RH_ENTREPRISE" in u.roles]

    @rx.var
    def specialty_suggestions(self) -> list[str]:
        """Distinct specialties from already-loaded users (doctors only)."""
        seen: set[str] = set()
        for u in self.users:
            sp = u.specialty
            if sp and sp.strip():
                seen.add(sp.strip())
        return sorted(seen)

    @rx.var
    def psc_tab_users(self) -> list[UserRowDTO]:
        """All PSC-side users: admins, operators, PSC doctors."""
        _psc = {"SUPER_ADMIN_PSC", "ADMIN_PSC", "DIRECTEUR_PSC", "OPERATEUR_TERRAIN", "OPERATEUR_LABO", "MEDECIN_PSC"}
        return [u for u in self.users if any(r in _psc for r in u.roles)]

    @rx.var
    def enterprise_tab_users(self) -> list[UserRowDTO]:
        """All enterprise-side users: enterprise doctors + HR."""
        _ent = {"MEDECIN_ENTREPRISE", "RH_ENTREPRISE"}
        return [u for u in self.users if any(r in _ent for r in u.roles)]

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
        self.edit_user_id = ""
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
        clean = v if v and v != "_none_" else ""
        self.form = UserFormDTO(**{**self.form.dict(), "linked_account_id": clean})

    @rx.event
    def set_specialty(self, v: str):
        self.form = UserFormDTO(**{**self.form.dict(), "specialty": v})

    @rx.event
    async def open_edit_dialog(self, user_id: str):
        """Open the form pre-filled with the user's current specialty and role."""
        user = next((u for u in self.users if u.id == user_id), None)
        if user is None:
            return
        self.form = UserFormDTO(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            role=user.roles[0] if user.roles else "",
            is_active=user.is_active,
            linked_account_id=user.linked_account_id or "",
            specialty=user.specialty or "",
        )
        self.form_error = ""
        self.is_editing = True
        self.edit_user_id = user_id
        await self._load_account_options()
        self.dialog_open = True

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
                    except Exception as exc:
                        print(f"[user_mgmt] Erreur sync gws_core→care_user {email}: {exc}")
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
                        if role != CareRole.PATIENT:
                            raise ValueError("Cet utilisateur a déjà des rôles assignés dans Constellab Care.")
                        # For PATIENT role: allow adding to existing users, but prevent duplicate patient role
                        if role in existing_roles:
                            raise ValueError("Cet utilisateur a déjà le rôle Patient.")

                # 4. Assign Care role
                role = CareRole(self.form.role)
                linked_account = self.form.linked_account_id or None

                if role == CareRole.PATIENT:
                    # Auto-create a Patient record and link it
                    from datetime import date
                    from gws_care.patient.patient_service import PatientService
                    from gws_care.patient.patient_dto import SavePatientDTO
                    patient = PatientService.create_patient(SavePatientDTO(
                        last_name=last_name or email,
                        first_name=first_name or "",
                        date_of_birth=date(2000, 1, 1),  # placeholder — edit in patient list
                        gender="Other",
                        email=email or None,
                    ))
                    UserRoleService.assign_role_with_link(
                        user_id=user_id,
                        role=role,
                        linked_patient_id=str(patient.id),
                    )
                else:
                    UserRoleService.assign_role_with_link(
                        user_id=user_id,
                        role=role,
                        linked_account_id=linked_account,
                        linked_patient_id=None,
                        specialty=self.form.specialty.strip() or None,
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
        self.confirm_revoke_motif = ""
        self.confirm_revoke_open = True

    @rx.event
    def dismiss_confirm_revoke(self):
        self.confirm_revoke_open = False
        self.confirm_revoke_user_id = ""
        self.confirm_revoke_user_email = ""
        self.confirm_revoke_motif = ""

    @rx.event
    def set_confirm_revoke_motif(self, v: str):
        self.confirm_revoke_motif = v

    @rx.event
    async def confirmed_revoke(self):
        if not self.confirm_revoke_motif.strip():
            self.error = "Le motif de suppression est obligatoire."
            return
        user_id = self.confirm_revoke_user_id
        motif = self.confirm_revoke_motif.strip()
        self.confirm_revoke_open = False
        self.confirm_revoke_user_id = ""
        self.confirm_revoke_user_email = ""
        self.confirm_revoke_motif = ""
        try:
            with await self.authenticate_user():
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_role_service import UserRoleService
                roles = UserRoleService.get_roles_for_user(user_id)
                for role in roles:
                    UserRoleService.revoke_role(user_id, role)
                # Log motif in console / audit trail
                from gws_core.core.utils.logger import Logger
                Logger.info(f"[user_mgmt] Suppression utilisateur {user_id} — motif : {motif}")
            await self._load_users()
        except Exception as e:
            self.error = str(e)

    async def _load_users(self):
        self.is_loading = True
        self.error = ""
        try:
            with await self.authenticate_user():
                from gws_care.role.care_role import CareRole
                from gws_care.role.user_role_service import UserRoleService
                from gws_care.role.user_care_role import UserCareRole
                from gws_care.user.user import User

                # Load all users that have at least one care role
                rows = UserRoleService.list_users_with_roles()

                # Batch-preload all referenced account names (1 SELECT, avoids N+1)
                acct_ids = {row.get("linked_account_id") for row in rows if row.get("linked_account_id")}
                acct_names_cache: dict[str, str] = {}
                if acct_ids:
                    from gws_care.account.account import Account
                    for a in Account.select(Account.id, Account.name).where(Account.id.in_(acct_ids)):
                        acct_names_cache[str(a.id)] = a.name

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
                    linked_acc_name = acct_names_cache.get(str(linked_acc_id)) if linked_acc_id else None

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
                        specialty=row.get("specialty", "") or "",
                    ))
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_loading = False

    @rx.event
    async def preview_user(self, user_id: str):
        """Switch the sidebar to preview the nav as this user would see it."""
        # Security: only admins may preview other users' navigation
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.role.user_role_service import UserRoleService
                roles = [r.value for r in UserRoleService.get_roles_for_user(str(auth_user.id))]
                _admin_roles = {"SUPER_ADMIN_PSC", "ADMIN_PSC", "DIRECTEUR_PSC"}
                if not any(r in _admin_roles for r in roles):
                    return
        except Exception as exc:
            return
        for u in self.users:
            if u.id == user_id:
                from ..common.nav_role_state import NavRoleState
                display_name = f"{u.last_name} {u.first_name}".strip() or u.email
                yield NavRoleState.start_preview(u.roles, display_name)
                return

    async def _load_account_options(self):
        try:
            with await self.authenticate_user():
                from gws_care.account.account import Account
                accounts = Account.select().where(Account.is_active == True).order_by(Account.name)
                self.account_options = [
                    AccountOptionDTO(id=str(a.id), name=a.name) for a in accounts
                ]
        except Exception as exc:
            print(f"[user_mgmt] Erreur chargement options comptes: {exc}")
            self.account_options = []
