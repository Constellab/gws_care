"""NavRoleState — dedicated navigation state for role-based sidebar menu.

Follows the same pattern as BellState: direct child of ReflexMainState,
loaded on every page, independent of page-level substates.
"""

import reflex as rx
from gws_reflex_main import ReflexMainState


class NavRoleState(ReflexMainState):
    """Exposes the current user's CareRoles as reactive computed vars
    that page_layout.py can use to conditionally show/hide nav items.

    Load via: on_load=[..., NavRoleState.on_load]
    """

    current_roles: list[str] = []   # reactive public var — populated on load

    @rx.event
    async def on_load(self):
        """Load current user's roles. No-op if already loaded (session cache)."""
        if self.current_roles:
            return
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.role.user_role_service import UserRoleService
                roles = UserRoleService.get_roles_for_user(str(auth_user.id))
                self.current_roles = [r.value for r in roles]
        except Exception:
            self.current_roles = []

    @rx.event
    async def reload(self):
        """Force reload roles (e.g. after role change in admin panel)."""
        self.current_roles = []
        await self.on_load()  # type: ignore[misc]

    # ── Role shortcuts — used in page_layout.py via rx.cond ─────────────────

    @rx.var
    def no_role_assigned(self) -> bool:
        """True on a fresh install or before any role is assigned → show all nav."""
        return len(self.current_roles) == 0

    @rx.var
    def is_super_admin(self) -> bool:
        return "SUPER_ADMIN_PSC" in self.current_roles

    @rx.var
    def is_directeur(self) -> bool:
        return "DIRECTEUR_PSC" in self.current_roles

    @rx.var
    def is_admin_psc(self) -> bool:
        return "ADMIN_PSC" in self.current_roles

    @rx.var
    def is_operateur_terrain(self) -> bool:
        return "OPERATEUR_TERRAIN" in self.current_roles

    @rx.var
    def is_operateur_labo(self) -> bool:
        return "OPERATEUR_LABO" in self.current_roles

    @rx.var
    def is_medecin_psc(self) -> bool:
        return "MEDECIN_PSC" in self.current_roles

    @rx.var
    def is_medecin_entreprise(self) -> bool:
        return "MEDECIN_ENTREPRISE" in self.current_roles

    @rx.var
    def is_rh_entreprise(self) -> bool:
        return "RH_ENTREPRISE" in self.current_roles

    @rx.var
    def is_patient_user(self) -> bool:
        return "PATIENT" in self.current_roles

    # ── Grouped shortcuts ────────────────────────────────────────────────────

    @rx.var
    def is_psc_staff(self) -> bool:
        """Any PSC internal role."""
        psc = {
            "SUPER_ADMIN_PSC", "DIRECTEUR_PSC", "ADMIN_PSC",
            "OPERATEUR_TERRAIN", "OPERATEUR_LABO", "MEDECIN_PSC",
        }
        return any(r in self.current_roles for r in psc)

    @rx.var
    def is_upper_admin(self) -> bool:
        """Super Admin or Admin PSC — full operational access."""
        return self.is_super_admin or self.is_admin_psc

    @rx.var
    def can_see_admin_section(self) -> bool:
        """Who can see Users/Audit/Prebilling menus."""
        return self.is_super_admin or self.is_admin_psc or self.is_directeur

    @rx.var
    def can_see_campaigns(self) -> bool:
        return (
            self.is_super_admin or self.is_admin_psc or self.is_directeur
            or self.is_operateur_terrain or self.is_operateur_labo
            or self.is_medecin_psc
            or self.no_role_assigned
        )

    @rx.var
    def can_see_patients(self) -> bool:
        return (
            self.is_super_admin or self.is_admin_psc
            or self.is_operateur_terrain or self.is_operateur_labo
            or self.is_medecin_psc
            or self.no_role_assigned
        )

    @rx.var
    def can_see_accounts(self) -> bool:
        return self.is_super_admin or self.is_admin_psc or self.is_directeur or self.no_role_assigned

    @rx.var
    def can_see_appointments(self) -> bool:
        return (
            self.is_super_admin or self.is_admin_psc
            or self.is_operateur_terrain or self.no_role_assigned
        )

    @rx.var
    def can_see_exam_types(self) -> bool:
        # Tout le personnel PSC peut consulter le référentiel examens
        return self.is_psc_staff or self.no_role_assigned

    @rx.var
    def can_see_medecin_psc(self) -> bool:
        return self.is_super_admin or self.is_admin_psc or self.is_medecin_psc or self.no_role_assigned

    @rx.var
    def can_see_medecin_entreprise(self) -> bool:
        return self.is_super_admin or self.is_admin_psc or self.is_medecin_entreprise or self.no_role_assigned

    @rx.var
    def can_see_rh(self) -> bool:
        return self.is_super_admin or self.is_admin_psc or self.is_rh_entreprise or self.no_role_assigned

    @rx.var
    def can_see_notifications(self) -> bool:
        return self.is_psc_staff or self.is_upper_admin or self.no_role_assigned

    @rx.var
    def can_see_companies(self) -> bool:
        return self.is_super_admin or self.is_admin_psc or self.is_directeur or self.no_role_assigned

    @rx.var
    def can_see_settings(self) -> bool:
        return self.is_super_admin or self.is_admin_psc or self.is_directeur or self.no_role_assigned

    # ── Home route — redirects user to their role-appropriate landing page ───

    @rx.var
    def home_route(self) -> str:
        """Return the most appropriate home page for the current user's role."""
        if self.no_role_assigned:
            return "/dashboard"
        if self.is_super_admin or self.is_admin_psc or self.is_directeur:
            return "/dashboard"
        if self.is_operateur_terrain or self.is_operateur_labo:
            return "/campaigns"
        if self.is_medecin_psc:
            return "/doctor-psc"
        if self.is_medecin_entreprise:
            return "/doctor-enterprise"
        if self.is_rh_entreprise:
            return "/hr"
        if self.is_patient_user:
            return "/patient-portal"
        return "/dashboard"
