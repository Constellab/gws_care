"""RoleState — mixin providing role-based computed vars for any Reflex state.

Usage:
    class MyPageState(RoleState):
        ...

    # In component:
    rx.cond(MyPageState.is_doctor, doctor_only_section(), rx.fragment())
"""

import reflex as rx
from gws_reflex_main import ReflexMainState


class RoleState(ReflexMainState):
    """Mixin that loads the current user's CareRoles and exposes helper vars.

    Keeps a list of role values (strings) in state so Reflex can react to them.
    Call `await self._load_roles()` inside any `on_load` handler.
    """

    _care_roles: list[str] = []   # private — backend use only
    _is_platform_admin: bool = False  # private — True when gws_core UserGroup is ADMIN
    _linked_account_ids: list[str] = []  # private — account IDs for ACCOUNT_ADMIN
    _doctor_all_patients: bool = True   # private — True when doctor has global patient access
    _doctor_patient_ids: list[str] = []  # private — patient IDs for scoped DOCTOR
    _linked_patient_id: str = ""  # private — set for PATIENT role
    _linked_doctor_id: str = ""  # private — MedicalDoctor.id for users with DOCTOR role
    _active_role_override: str = ""  # private — set when user manually switches role view

    # public — displayed in the user menu button
    user_full_name: str = ""
    user_photo: str = ""      # URL from Constellab Space, empty when not set
    user_initials: str = ""   # fallback: first letter of first + last name

    # ── Computed role shortcuts (public — read by frontend) ───────────────────

    @rx.var
    def is_admin(self) -> bool:
        """True for the platform super-admin or any user with the ADMIN care role."""
        if self._active_role_override:
            return self._active_role_override == "ADMIN"
        return self._is_platform_admin or "ADMIN" in self._care_roles

    @rx.var
    def is_doctor(self) -> bool:
        """True for Clinic Doctor PSC (DOCTOR role) or ADMIN."""
        if self._active_role_override:
            return self._active_role_override in ("ADMIN", "DOCTOR")
        return self.is_admin or "DOCTOR" in self._care_roles

    @rx.var
    def is_operator(self) -> bool:
        """True for HQ Operator PSC (OPERATOR role) or ADMIN."""
        if self._active_role_override:
            return self._active_role_override in ("ADMIN", "OPERATOR")
        return self.is_admin or "OPERATOR" in self._care_roles

    @rx.var
    def is_account_admin(self) -> bool:
        """True for Company Doctor / Responsable RH (ACCOUNT_ADMIN role) or ADMIN."""
        if self._active_role_override:
            return self._active_role_override in ("ADMIN", "ACCOUNT_ADMIN")
        return self.is_admin or "ACCOUNT_ADMIN" in self._care_roles

    @rx.var
    def is_rh(self) -> bool:
        """Alias for is_account_admin — used in RH / company-doctor context."""
        return self.is_account_admin

    @rx.var
    def is_work_doctor(self) -> bool:
        """True for Médecin Entreprise (MEDECIN_ENTREPRISE role) or ADMIN."""
        if self._active_role_override:
            return self._active_role_override in ("ADMIN", "MEDECIN_ENTREPRISE")
        return self.is_admin or "MEDECIN_ENTREPRISE" in self._care_roles

    @rx.var
    def is_patient_user(self) -> bool:
        """True when the user is a linked patient (PATIENT role).

        Without an explicit role override, returns False when the user also
        holds a higher-priority role (ADMIN / DOCTOR / OPERATOR / ACCOUNT_ADMIN)
        so the admin interface is shown by default instead of the patient portal.
        """
        if self._active_role_override:
            return self._active_role_override == "PATIENT"
        # If the user has any higher-priority role, don't activate patient UI
        has_higher_role = self._is_platform_admin or any(
            r in self._care_roles for r in ("ADMIN", "DOCTOR", "OPERATOR", "ACCOUNT_ADMIN")
        )
        if has_higher_role:
            return False
        return "PATIENT" in self._care_roles

    @rx.var
    def has_any_role(self) -> bool:
        """True when the user has at least one CareRole (or is platform admin)."""
        return self._is_platform_admin or len(self._care_roles) > 0

    @rx.var
    def linked_account_ids(self) -> list[str]:
        """Account IDs the current ACCOUNT_ADMIN user is linked to."""
        return self._linked_account_ids

    @rx.var
    def doctor_all_patients(self) -> bool:
        """True when the current DOCTOR user has global access to all patients."""
        return self._doctor_all_patients

    @rx.var
    def doctor_patient_ids(self) -> list[str]:
        """Patient IDs the current DOCTOR is restricted to (when not all_patients)."""
        return self._doctor_patient_ids

    @rx.var
    def linked_patient_id(self) -> str:
        return self._linked_patient_id

    @rx.var
    def linked_doctor_id(self) -> str:
        """MedicalDoctor ID for the logged-in DOCTOR-role user (empty if none)."""
        return self._linked_doctor_id

    @rx.var
    def active_role_display(self) -> str:
        """Label of the currently active role (override or highest actual role)."""
        labels = {
            "ADMIN": "Admin",
            "DOCTOR": "Doctor",
            "OPERATOR": "Operator",
            "ACCOUNT_ADMIN": "Account Admin",
            "PATIENT": "Patient",
        }
        if self._active_role_override:
            return labels.get(self._active_role_override, self._active_role_override)
        # Show the highest role
        for role in ("ADMIN", "DOCTOR", "OPERATOR", "ACCOUNT_ADMIN", "PATIENT"):
            if role == "ADMIN" and (self._is_platform_admin or "ADMIN" in self._care_roles):
                return labels["ADMIN"]
            if role in self._care_roles:
                return labels[role]
        return ""

    @rx.var
    def active_role_key(self) -> str:
        """Raw role key of the currently active role (e.g. 'ADMIN', 'DOCTOR')."""
        if self._active_role_override:
            return self._active_role_override
        for role in ("ADMIN", "DOCTOR", "OPERATOR", "ACCOUNT_ADMIN", "PATIENT"):
            if role == "ADMIN" and (self._is_platform_admin or "ADMIN" in self._care_roles):
                return "ADMIN"
            if role in self._care_roles:
                return role
        return ""

    @rx.var
    def switchable_roles(self) -> list[str]:
        """Ordered list of role values the current user can switch to.

        Platform admins and ADMIN-role users can simulate any role so they can
        test the app from different perspectives.
        Other users can only switch between their explicitly assigned roles.
        """
        is_admin_user = self._is_platform_admin or "ADMIN" in self._care_roles
        if is_admin_user:
            # Admins can simulate every role
            return list(("ADMIN", "OPERATOR", "DOCTOR", "ACCOUNT_ADMIN", "PATIENT"))
        available: set[str] = set(self._care_roles)
        return [r for r in ("ADMIN", "OPERATOR", "DOCTOR", "ACCOUNT_ADMIN", "PATIENT") if r in available]

    # ── Role-switch event ─────────────────────────────────────────────────────

    @rx.event
    def switch_role(self, role: str):
        """Switch the UI to view the app as the given role."""
        self._active_role_override = role
        return rx.redirect("/dashboard")

    # ── Internal loader ───────────────────────────────────────────────────────

    async def _load_roles(self) -> None:
        """Fetch the current user's roles from DB.

        Must be called from within an authenticate_user() context.
        Also detects platform-level admins (gws_core UserGroup.ADMIN) to allow
        bootstrapping role assignments on a fresh install.
        """
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.role.user_role_service import UserRoleService
                from gws_care.user.user import User
                from gws_core import UserGroup
                from gws_core.user.user import User as GwsCoreUser

                effective_user = auth_user

                # In dev mode the framework returns the sysuser when no
                # dev_user_email is configured.  Automatically substitute the
                # first real platform-admin so the developer works under their
                # own identity without modifying any static config file.
                if self.is_dev_mode():
                    try:
                        sysuser = GwsCoreUser.get_and_check_sysuser()
                        if str(auth_user.id) == str(sysuser.id):
                            real_admin = (
                                GwsCoreUser
                                .select()
                                .where(GwsCoreUser.group == UserGroup.ADMIN)
                                .first()
                            )
                            if real_admin is not None:
                                effective_user = real_admin
                    except Exception:
                        pass

                user_id = str(effective_user.id)
                from gws_care.role.care_role import CareRole
                roles = UserRoleService.get_roles_for_user(user_id)
                self._care_roles = [r.value for r in roles]
                # Linked account IDs for ACCOUNT_ADMIN
                self._linked_account_ids = UserRoleService.get_linked_account_ids(user_id, CareRole.ACCOUNT_ADMIN)
                # Doctor patient scope
                self._doctor_all_patients = UserRoleService.get_doctor_all_patients(user_id)
                self._doctor_patient_ids = UserRoleService.get_linked_account_ids(user_id, CareRole.DOCTOR)
                self._linked_patient_id = UserRoleService.get_linked_patient_id(user_id) or ""
                # Resolve display name from the effective user
                try:
                    self.user_full_name = (
                        f"{effective_user.first_name or ''} {effective_user.last_name or ''}".strip()
                        or effective_user.email
                        or ""
                    )
                except Exception:
                    self.user_full_name = ""
                # Check if the user is a gws_core platform admin; also read photo
                try:
                    local_user = User.get_by_id(user_id)
                    if local_user is not None:
                        self._is_platform_admin = local_user.group == UserGroup.ADMIN
                        self.user_photo = local_user.photo or ""
                except Exception:
                    self._is_platform_admin = False
                    self.user_photo = ""
                first = (effective_user.first_name or "")[:1].upper()
                last = (effective_user.last_name or "")[:1].upper()
                self.user_initials = (first + last) or "?"
                # Resolve linked MedicalDoctor (for DOCTOR-role scoping)
                try:
                    from gws_care.doctor.medical_doctor import MedicalDoctor
                    doctor = MedicalDoctor.get_or_none(MedicalDoctor.user == user_id)
                    self._linked_doctor_id = str(doctor.id) if doctor else ""
                except Exception:
                    self._linked_doctor_id = ""
        except Exception:
            self._care_roles = []
            self._linked_account_ids = []
            self._doctor_all_patients = True
            self._doctor_patient_ids = []
            self._linked_patient_id = ""
            self._linked_doctor_id = ""
            self._is_platform_admin = False
            self.user_photo = ""
            self.user_initials = "?"

    async def _require_any_of(self, *role_checks: bool, redirect_to: str = "/dashboard"):
        """Redirect to *redirect_to* if none of the given role conditions are True.

        Call this **after** ``await self._load_roles()`` inside ``on_load``.

        Example::

            await self._load_roles()
            yield await self._require_any_of(self.is_operator, self.is_doctor)
        """
        if not any(role_checks):
            # User has no role at all — send to no-access page to avoid redirect loops.
            if not self.has_any_role:
                return rx.redirect("/no-access")
            return rx.redirect(redirect_to)
        return None
