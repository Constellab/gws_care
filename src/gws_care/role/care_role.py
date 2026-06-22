"""Care-specific user role enum — V2 extended roles."""

from enum import Enum


class CareRole(str, Enum):
    """Application-level roles for gws_care (V2).

    Roles are independent of gws_core's UserGroup.
    A user can hold multiple CareRoles simultaneously.

    PSC internal roles
    ------------------
    SUPER_ADMIN_PSC  : Full access — user management, configuration, all data
    ADMIN_PSC        : Operational management of PSC, can validate campaigns
    OPERATEUR_TERRAIN: Field operator — campaigns, QR codes, presence, samples
    OPERATEUR_LABO   : Lab operator — result entry and lab validation
    MEDECIN_PSC      : PSC doctor — interpretation and medical validation

    External / company roles
    ------------------------
    MEDECIN_ENTREPRISE: Company doctor — sees validated results for their company
    RH_ENTREPRISE     : HR — administrative tracking only (no medical data)
    PATIENT           : Patient/employee — own appointments and published results

    System
    ------
    SYSTEME          : Automated notifications, status transitions, audit

    Backward-compatible aliases
    ---------------------------
    ADMIN        → SUPER_ADMIN_PSC
    DOCTOR       → MEDECIN_PSC
    OPERATOR     → OPERATEUR_TERRAIN
    ACCOUNT_ADMIN→ RH_ENTREPRISE
    """

    # PSC staff
    SUPER_ADMIN_PSC = "SUPER_ADMIN_PSC"
    DIRECTEUR_PSC = "DIRECTEUR_PSC"
    ADMIN_PSC = "ADMIN_PSC"
    OPERATEUR_TERRAIN = "OPERATEUR_TERRAIN"
    OPERATEUR_LABO = "OPERATEUR_LABO"
    MEDECIN_PSC = "MEDECIN_PSC"

    # Company / external
    MEDECIN_ENTREPRISE = "MEDECIN_ENTREPRISE"
    RH_ENTREPRISE = "RH_ENTREPRISE"
    PATIENT = "PATIENT"

    # System
    SYSTEME = "SYSTEME"

    # ── Backward-compatible Python aliases (CareRole.ADMIN → SUPER_ADMIN_PSC) ─
    ADMIN = "SUPER_ADMIN_PSC"
    DOCTOR = "MEDECIN_PSC"
    OPERATOR = "OPERATEUR_TERRAIN"
    ACCOUNT_ADMIN = "RH_ENTREPRISE"

    @classmethod
    def _missing_(cls, value: object):
        """Map legacy DB strings ('ADMIN', 'DOCTOR', …) to current members."""
        _legacy = {
            "ADMIN": cls.SUPER_ADMIN_PSC,
            "DOCTOR": cls.MEDECIN_PSC,
            "OPERATOR": cls.OPERATEUR_TERRAIN,
            "ACCOUNT_ADMIN": cls.RH_ENTREPRISE,
        }
        return _legacy.get(value)

    def get_label(self) -> str:
        labels = {
            CareRole.SUPER_ADMIN_PSC: "Super Admin PSC",
            CareRole.DIRECTEUR_PSC: "Directeur PSC",
            CareRole.ADMIN_PSC: "Admin PSC",
            CareRole.OPERATEUR_TERRAIN: "Opérateur terrain PSC",
            CareRole.OPERATEUR_LABO: "Opérateur labo PSC",
            CareRole.MEDECIN_PSC: "Médecin PSC",
            CareRole.MEDECIN_ENTREPRISE: "Médecin entreprise",
            CareRole.RH_ENTREPRISE: "RH entreprise",
            CareRole.PATIENT: "Patient / Employé",
            CareRole.SYSTEME: "Système",
        }
        return labels.get(self, self.value)

    def is_psc_staff(self) -> bool:
        """True for PSC internal roles that have broad data access."""
        return self in (
            CareRole.SUPER_ADMIN_PSC,
            CareRole.DIRECTEUR_PSC,
            CareRole.ADMIN_PSC,
            CareRole.OPERATEUR_TERRAIN,
            CareRole.OPERATEUR_LABO,
            CareRole.MEDECIN_PSC,
        )

    def can_see_medical_data(self) -> bool:
        """True for roles authorised to see individual medical results."""
        return self in (
            CareRole.SUPER_ADMIN_PSC,
            CareRole.ADMIN_PSC,
            CareRole.OPERATEUR_LABO,
            CareRole.MEDECIN_PSC,
            CareRole.MEDECIN_ENTREPRISE,
        )
