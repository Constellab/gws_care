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
                    self.success_message = f"Rôle '{care_role.get_label()}' retiré."
                else:
                    if care_role == CareRole.PATIENT:
                        # Auto-create a Patient record from the user's info and link it
                        from datetime import date
                        from gws_care.user.user import User
                        from gws_care.patient.patient_service import PatientService
                        from gws_care.patient.patient_dto import SavePatientDTO
                        user_obj = User.get_by_id(user_id)
                        patient = PatientService.create_patient(SavePatientDTO(
                            last_name=user_obj.last_name or user_obj.email,
                            first_name=user_obj.first_name or "",
                            date_of_birth=date(2000, 1, 1),  # placeholder — edit in patient list
                            gender="Other",
                            email=user_obj.email or None,
                        ))
                        UserRoleService.assign_role(user_id, care_role)
                        UserRoleService.assign_role_with_link(
                            user_id, care_role, linked_patient_id=str(patient.id)
                        )
                        self.success_message = (
                            f"Rôle patient assigné et dossier créé ({patient.patient_number}). "
                            "Pensez à compléter la date de naissance dans la liste patients."
                        )
                    else:
                        UserRoleService.assign_role(user_id, care_role)
                        self.success_message = f"Rôle '{care_role.get_label()}' assigné."
            await self._load_users()
            await self._load_entity_options()
        except Exception as e:
            self.error_message = f"Erreur : {e}"

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
        except Exception as exc:
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

                # Batch-load linked account names (avoids N+1)
                acct_ids_needed = {row.linked_account_id for row in rows if row.linked_account_id}
                acct_names_map: dict[str, str] = {}
                if acct_ids_needed:
                    from gws_care.account.account import Account
                    for a in Account.select(Account.id, Account.name).where(Account.id.in_(acct_ids_needed)):
                        acct_names_map[str(a.id)] = a.name

                for row in rows:
                    user = row.user
                    raw_role = row.role
                    role_key = raw_role if isinstance(raw_role, CareRole) else CareRole(raw_role)
                    role_label = _role_labels.get(role_key, str(raw_role))
                    acct_name = acct_names_map.get(str(row.linked_account_id), "") if row.linked_account_id else ""
                    contacts.append(StaffContactDTO(
                        id=str(user.id),
                        full_name=f"{user.first_name} {user.last_name}",
                        email=user.email,
                        role=role_key.value,
                        role_label=role_label,
                        linked_account_name=acct_name,
                    ))
                self.staff_contacts = contacts
        except Exception as exc:
            pass

    # ── Reset data ────────────────────────────────────────────────────────────

    show_reset_confirm: bool = False
    reset_confirm_input: str = ""
    is_resetting: bool = False
    reset_error: str = ""
    reset_success: str = ""

    @rx.event
    def open_reset_confirm(self):
        self.show_reset_confirm = True
        self.reset_confirm_input = ""
        self.reset_error = ""
        self.reset_success = ""

    @rx.event
    def close_reset_confirm(self):
        self.show_reset_confirm = False
        self.reset_confirm_input = ""

    @rx.event
    def set_reset_confirm_input(self, v: str):
        self.reset_confirm_input = v

    @rx.event
    async def execute_reset(self):
        """Delete all data except exam type referentials (gws_care_exam_type_ref, gws_care_exam_parameter)."""
        if self.reset_confirm_input != "SUPPRIMER":
            self.reset_error = "Tapez exactement SUPPRIMER pour confirmer."
            return
        self.is_resetting = True
        self.reset_error = ""
        self.reset_success = ""
        try:
            with await self.authenticate_user():
                from gws_care.core.care_db_manager import CareDbManager
                db = CareDbManager.get_instance().db
                tables_to_clear = [
                    "gws_care_exam_parameter_result",
                    "gws_care_exam_result",
                    "gws_care_exam_file",
                    "gws_care_exam",
                    "gws_care_campaign_patient",
                    "gws_care_campaign_exam",
                    "gws_care_campaign",
                    "gws_care_correction_request",
                    "gws_care_audit_log",
                    "gws_care_patient_deletion_log",
                    "gws_care_patient_document",
                    "gws_care_patient_note",
                    "gws_care_patient_account",
                    "gws_care_patient_consent",
                    "gws_care_patient_message",
                    "gws_care_patient_invoice_line",
                    "gws_care_patient_invoice",
                    "gws_care_medical_certificate",
                    "gws_care_prescription_line",
                    "gws_care_prescription",
                    "gws_care_consultation",
                    "gws_care_appointment",
                    "gws_care_tube_qr",
                    "gws_care_prebilling_line",
                    "gws_care_invoice",
                    "gws_care_prebilling",
                    "gws_care_notification_bell",
                    "gws_care_notification_log",
                    "gws_care_dashboard_snapshot",
                    "gws_care_doctor_schedule",
                    "gws_care_patient",
                    "gws_care_company",
                    "gws_care_price_list",
                    "gws_care_account",
                    "gws_care_user_role",
                    "gws_care_user_language_pref",
                ]
                db.execute_sql("SET FOREIGN_KEY_CHECKS = 0")
                for table in tables_to_clear:
                    try:
                        db.execute_sql(f"DELETE FROM `{table}`")
                    except Exception:
                        pass  # table may not exist yet
                db.execute_sql("SET FOREIGN_KEY_CHECKS = 1")
                self.reset_success = "Remise à zéro effectuée. Toutes les données ont été supprimées sauf les référentiels d'examens."
                self.show_reset_confirm = False
                self.reset_confirm_input = ""
        except Exception as e:
            self.reset_error = f"Erreur lors de la remise à zéro : {e}"
        finally:
            self.is_resetting = False
