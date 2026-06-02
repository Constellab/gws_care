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
    # Preview mode: simulate the nav as seen by another user
    preview_roles: list[str] = []
    preview_user_name: str = ""
    # True when the gws_core user belongs to the ADMIN group (system bootstrap)
    is_platform_admin: bool = False

    @rx.event
    async def on_load(self):
        """Load current user's roles. No-op if already loaded (session cache)."""
        if self.current_roles or self.is_platform_admin:
            return
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.role.user_role_service import UserRoleService
                from gws_core import UserGroup
                roles = UserRoleService.get_roles_for_user(str(auth_user.id))
                self.current_roles = [r.value for r in roles]
                # Detect platform-level admin using gws_core auth object directly
                # (avoids dependency on local gws_care_user table which may not be populated)
                self.is_platform_admin = auth_user.group == UserGroup.ADMIN
        except Exception as exc:
            print(f"[nav_role] Erreur chargement rôles: {exc}")
            self.current_roles = []
            self.is_platform_admin = False

    @rx.event
    async def reload(self):
        """Force reload roles (e.g. after role change in admin panel)."""
        self.current_roles = []
        await self.on_load()  # type: ignore[misc]

    # ── Role shortcuts — used in page_layout.py via rx.cond ─────────────────

    @rx.var
    def effective_roles(self) -> list[str]:
        """Preview mode: use simulated roles; otherwise current user's own roles."""
        return self.preview_roles if self.preview_roles else self.current_roles

    @rx.var
    def preview_active(self) -> bool:
        """True when the admin is previewing another user's nav."""
        return len(self.preview_roles) > 0

    @rx.var
    def no_role_assigned(self) -> bool:
        """True when user has no Care role AND is not a platform admin.

        Platform admins (gws_core ADMIN group) get full access for bootstrapping.
        Regular users with no role should see the 'pending access' screen.
        """
        return len(self.effective_roles) == 0

    @rx.var
    def pending_role_access(self) -> bool:
        """True for regular users who have no role yet (not a platform admin)."""
        return self.no_role_assigned and not self.is_platform_admin

    @rx.var
    def is_super_admin(self) -> bool:
        return "SUPER_ADMIN_PSC" in self.effective_roles

    @rx.var
    def is_directeur(self) -> bool:
        return "DIRECTEUR_PSC" in self.effective_roles

    @rx.var
    def is_admin_psc(self) -> bool:
        return "ADMIN_PSC" in self.effective_roles

    @rx.var
    def is_operateur_terrain(self) -> bool:
        return "OPERATEUR_TERRAIN" in self.effective_roles

    @rx.var
    def is_operateur_labo(self) -> bool:
        return "OPERATEUR_LABO" in self.effective_roles

    @rx.var
    def is_medecin_psc(self) -> bool:
        return "MEDECIN_PSC" in self.effective_roles

    @rx.var
    def is_medecin_entreprise(self) -> bool:
        return "MEDECIN_ENTREPRISE" in self.effective_roles

    @rx.var
    def is_rh_entreprise(self) -> bool:
        return "RH_ENTREPRISE" in self.effective_roles

    @rx.var
    def is_patient_user(self) -> bool:
        return "PATIENT" in self.effective_roles

    # ── Grouped shortcuts ────────────────────────────────────────────────────

    @rx.var
    def is_psc_staff(self) -> bool:
        """Any PSC internal role."""
        psc = {
            "SUPER_ADMIN_PSC", "DIRECTEUR_PSC", "ADMIN_PSC",
            "OPERATEUR_TERRAIN", "OPERATEUR_LABO", "MEDECIN_PSC",
        }
        return any(r in self.effective_roles for r in psc)

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
            or (self.no_role_assigned and self.is_platform_admin)
        )

    @rx.var
    def can_see_patients(self) -> bool:
        return (
            self.is_super_admin or self.is_admin_psc
            or self.is_operateur_terrain or self.is_operateur_labo
            or self.is_medecin_psc
            or (self.no_role_assigned and self.is_platform_admin)
        )

    @rx.var
    def can_see_accounts(self) -> bool:
        return (
            self.is_super_admin or self.is_admin_psc or self.is_directeur
            or (self.no_role_assigned and self.is_platform_admin)
        )

    @rx.var
    def can_see_appointments(self) -> bool:
        return (
            self.is_super_admin or self.is_admin_psc
            or self.is_operateur_terrain
            or (self.no_role_assigned and self.is_platform_admin)
        )

    @rx.var
    def can_see_exam_types(self) -> bool:
        # Tout le personnel PSC peut consulter le référentiel examens
        return self.is_psc_staff or (self.no_role_assigned and self.is_platform_admin)

    @rx.var
    def can_see_medecin_psc(self) -> bool:
        return (
            self.is_super_admin or self.is_admin_psc or self.is_medecin_psc
            or (self.no_role_assigned and self.is_platform_admin)
        )

    @rx.var
    def can_see_medecin_entreprise(self) -> bool:
        return (
            self.is_super_admin or self.is_admin_psc or self.is_medecin_entreprise
            or (self.no_role_assigned and self.is_platform_admin)
        )

    @rx.var
    def can_see_dossiers_medicaux(self) -> bool:
        """Page unifiée Dossiers médicaux (ex doctor_psc + doctor_enterprise)."""
        return self.can_see_medecin_psc or self.can_see_medecin_entreprise

    @rx.var
    def can_see_rh(self) -> bool:
        return (
            self.is_super_admin or self.is_admin_psc or self.is_rh_entreprise
            or (self.no_role_assigned and self.is_platform_admin)
        )

    @rx.var
    def can_see_notifications(self) -> bool:
        return self.is_psc_staff or self.is_upper_admin or (self.no_role_assigned and self.is_platform_admin)

    @rx.var
    def can_see_companies(self) -> bool:
        return (
            self.is_super_admin or self.is_admin_psc or self.is_directeur
            or (self.no_role_assigned and self.is_platform_admin)
        )

    @rx.var
    def can_see_settings(self) -> bool:
        return (
            self.is_super_admin or self.is_admin_psc or self.is_directeur
            or (self.no_role_assigned and self.is_platform_admin)
        )

    @rx.var
    def can_see_consultations(self) -> bool:
        """Consultations privées : médecins + admins PSC (pas les opérateurs)."""
        return (
            self.is_super_admin or self.is_admin_psc or self.is_directeur
            or self.is_medecin_psc or self.is_medecin_entreprise
            or (self.no_role_assigned and self.is_platform_admin)
        )

    @rx.var
    def can_see_prescriptions(self) -> bool:
        """Ordonnances : médecins + admins PSC."""
        return (
            self.is_super_admin or self.is_admin_psc or self.is_directeur
            or self.is_medecin_psc or self.is_medecin_entreprise
            or (self.no_role_assigned and self.is_platform_admin)
        )

    @rx.var
    def can_see_certificates(self) -> bool:
        """Certificats médicaux : médecins + admins PSC."""
        return (
            self.is_super_admin or self.is_admin_psc or self.is_directeur
            or self.is_medecin_psc or self.is_medecin_entreprise
            or (self.no_role_assigned and self.is_platform_admin)
        )

    @rx.var
    def can_see_corrections(self) -> bool:
        """Corrections : médecins + admins PSC."""
        return (
            self.is_super_admin or self.is_admin_psc or self.is_directeur
            or self.is_medecin_psc
            or (self.no_role_assigned and self.is_platform_admin)
        )

    @rx.var
    def can_see_doctor_schedule(self) -> bool:
        """Agenda médecins : médecins PSC + admins PSC."""
        return (
            self.is_super_admin or self.is_admin_psc or self.is_directeur
            or self.is_medecin_psc
            or (self.no_role_assigned and self.is_platform_admin)
        )

    @rx.var
    def can_see_invoices(self) -> bool:
        """Factures patients : admins + directeur."""
        return (
            self.is_super_admin or self.is_admin_psc or self.is_directeur
            or (self.no_role_assigned and self.is_platform_admin)
        )

    @rx.var
    def can_see_messages(self) -> bool:
        """Messagerie directe : médecins + patients + admins PSC."""
        return (
            self.is_super_admin or self.is_admin_psc
            or self.is_medecin_psc or self.is_medecin_entreprise
            or self.is_patient_user
            or (self.no_role_assigned and self.is_platform_admin)
        )

    @rx.var
    def can_see_patient_portal(self) -> bool:
        """Espace patient : uniquement les utilisateurs avec rôle PATIENT."""
        return self.is_patient_user

    @rx.var
    def can_see_samples(self) -> bool:
        """Prélèvements : admins PSC, directeur, opérateur terrain/labo."""
        return (
            self.is_super_admin or self.is_admin_psc or self.is_directeur
            or self.is_operateur_terrain or self.is_operateur_labo
            or (self.no_role_assigned and self.is_platform_admin)
        )

    @rx.var
    def can_see_interpretation(self) -> bool:
        """Interprétation médicale : médecins + admins PSC + directeur."""
        return (
            self.is_super_admin or self.is_admin_psc or self.is_directeur
            or self.is_medecin_psc or self.is_medecin_entreprise
            or (self.no_role_assigned and self.is_platform_admin)
        )

    @rx.var
    def can_see_lab_queue(self) -> bool:
        """File d'attente labo : opérateur labo + admins PSC."""
        return (
            self.is_super_admin or self.is_admin_psc or self.is_directeur
            or self.is_operateur_labo
            or (self.no_role_assigned and self.is_platform_admin)
        )

    @rx.var
    def can_see_any_admin(self) -> bool:
        """True if the user has access to at least one admin sub-section."""
        return self.can_see_admin_section or self.can_see_exam_types or self.can_see_settings

    @rx.var
    def is_pure_patient(self) -> bool:
        """True when PATIENT is the ONLY role — no staff or enterprise role."""
        return (
            self.is_patient_user
            and not self.is_psc_staff
            and not self.is_upper_admin
            and not self.is_rh_entreprise
            and not self.is_medecin_entreprise
        )

    @rx.var
    def can_see_dashboard(self) -> bool:
        """Dashboard: hidden for pure-patient users who belong only to the patient portal."""
        return not self.is_pure_patient

    @rx.var
    def role_badge_label(self) -> str:
        """Human-readable label for the current user's primary role."""
        if self.preview_active:
            return self.preview_user_name
        if self.is_super_admin:
            return "Super Administrateur"
        if self.is_admin_psc:
            return "Administrateur PSC"
        if self.is_directeur:
            return "Directeur"
        if self.is_medecin_psc:
            return "Médecin PSC"
        if self.is_medecin_entreprise:
            return "Médecin Entreprise"
        if self.is_rh_entreprise:
            return "RH Entreprise"
        if self.is_operateur_terrain:
            return "Opérateur Terrain"
        if self.is_operateur_labo:
            return "Opérateur Labo"
        if self.is_patient_user:
            return "Patient"
        return "Aucun rôle"

    @rx.var
    def role_color_scheme(self) -> str:
        """Radix color scheme for the role badge."""
        if self.preview_active:
            return "amber"
        if self.is_super_admin or self.is_admin_psc:
            return "violet"
        if self.is_directeur:
            return "indigo"
        if self.is_medecin_psc or self.is_medecin_entreprise:
            return "crimson"
        if self.is_rh_entreprise:
            return "green"
        if self.is_operateur_terrain:
            return "orange"
        if self.is_operateur_labo:
            return "blue"
        if self.is_patient_user:
            return "teal"
        return "gray"

    # ── Simulation / preview events ──────────────────────────────────────────

    @rx.event
    def start_preview(self, roles: list[str], user_name: str):
        """Switch the sidebar to preview what <user_name> (with <roles>) would see."""
        self.preview_roles = roles
        self.preview_user_name = user_name

    @rx.event
    def stop_preview(self):
        """Exit preview mode and return to the current admin's own nav."""
        self.preview_roles = []
        self.preview_user_name = ""

    @rx.event
    def simulate_any_role(self, role_value: str):
        """Admin-only: preview the app as if the current user had any given role."""
        if not (self.is_super_admin or self.is_admin_psc or self.is_directeur):
            return
        if not role_value or role_value == "__reset__":
            self.preview_roles = []
            self.preview_user_name = ""
            return
        label_map = {
            "SUPER_ADMIN_PSC": "Super Administrateur",
            "ADMIN_PSC": "Administrateur PSC",
            "DIRECTEUR_PSC": "Directeur",
            "MEDECIN_PSC": "Médecin PSC",
            "MEDECIN_ENTREPRISE": "Médecin Entreprise",
            "RH_ENTREPRISE": "RH Entreprise",
            "OPERATEUR_TERRAIN": "Opérateur Terrain",
            "OPERATEUR_LABO": "Opérateur Labo",
            "PATIENT": "Patient",
        }
        self.preview_roles = [role_value]
        self.preview_user_name = f"Vue : {label_map.get(role_value, role_value)}"

    @rx.event
    async def switch_active_role(self, role_value: str):
        """Let a multi-role user activate a single role view.

        Empty string or __reset__ restores the full multi-role view.
        """
        if not role_value or role_value == "__reset__":
            self.preview_roles = []
            self.preview_user_name = ""
            # Reload dashboard with full roles
            from ..dashboard.dashboard_state import DashboardState
            yield DashboardState.on_load()
            return
        # Map role value to human label for the preview banner
        label_map = {
            "SUPER_ADMIN_PSC": "Super Administrateur",
            "ADMIN_PSC": "Administrateur PSC",
            "DIRECTEUR_PSC": "Directeur",
            "MEDECIN_PSC": "Médecin PSC",
            "MEDECIN_ENTREPRISE": "Médecin Entreprise",
            "RH_ENTREPRISE": "RH Entreprise",
            "OPERATEUR_TERRAIN": "Opérateur Terrain",
            "OPERATEUR_LABO": "Opérateur Labo",
            "PATIENT": "Patient",
        }
        # Only allow switching to one of the user's own roles
        if role_value in self.current_roles:
            self.preview_roles = [role_value]
            self.preview_user_name = label_map.get(role_value, role_value)
            # Reload dashboard to reflect the newly selected role context
            from ..dashboard.dashboard_state import DashboardState
            yield DashboardState.on_load()

    # ── Role options for the multi-role switcher ──────────────────────────────

    @rx.var
    def has_multiple_roles(self) -> bool:
        """True when the user holds more than one role (switcher becomes visible)."""
        return len(self.current_roles) > 1

    @rx.var
    def role_switch_options(self) -> list[list[str]]:
        """[['MEDECIN_PSC', 'Médecin PSC'], ...] pour affichage dans le sélecteur."""
        label_map = {
            "SUPER_ADMIN_PSC": "Super Administrateur",
            "ADMIN_PSC": "Administrateur PSC",
            "DIRECTEUR_PSC": "Directeur",
            "MEDECIN_PSC": "Médecin PSC",
            "MEDECIN_ENTREPRISE": "Médecin Entreprise",
            "RH_ENTREPRISE": "RH Entreprise",
            "OPERATEUR_TERRAIN": "Opérateur Terrain",
            "OPERATEUR_LABO": "Opérateur Labo",
            "PATIENT": "Patient",
        }
        return [[r, label_map.get(r, r)] for r in self.current_roles]

    # ── Home route — redirects user to their role-appropriate landing page ───

    @rx.var
    def home_route(self) -> str:
        """Return the most appropriate home page for the current user's role."""
        if self.no_role_assigned:
            return "/dashboard"
        if self.is_super_admin or self.is_admin_psc or self.is_directeur:
            return "/dashboard"
        if self.is_operateur_labo:
            return "/lab-queue"
        if self.is_operateur_terrain:
            return "/campaigns"
        if self.is_medecin_psc or self.is_medecin_entreprise:
            return "/doctor-psc"
        if self.is_rh_entreprise:
            return "/hr"
        if self.is_patient_user:
            return "/patient-portal"
        return "/dashboard"
