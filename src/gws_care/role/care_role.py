"""Care-specific user role enum — V3 simplified roles."""

from enum import Enum


class CareRole(str, Enum):
    """Application-level roles for gws_care (V3).

    Roles are independent of gws_core's UserGroup.
    A user can hold multiple CareRoles simultaneously.

    Internal roles
    ---------------
    ADMIN     : Full access — user management, configuration, all data, campaign validation
    OPERATEUR : Field and lab operator — campaigns, QR codes, presence, samples, result entry
    MEDECIN   : Doctor — medical interpretation and validation. Whether a given doctor sees
                raw (first-interpretation) or validated-only data for a campaign is decided
                per-campaign by their assignment (see CampaignService.get_doctor_scope_for_campaign),
                not by a separate role.

    External / company roles
    ------------------------
    RH_ENTREPRISE: HR — administrative tracking only (no medical data)
    PATIENT      : Patient/employee — own appointments and published results

    System
    ------
    SYSTEME : Automated notifications, status transitions, audit

    Retired tier names (V2, merged into the roles above — kept as aliases so any
    reference missed during the V2→V3 sweep still resolves instead of raising)
    -------------------------------------------------------------------------
    SUPER_ADMIN_PSC / DIRECTEUR_PSC / ADMIN_PSC → ADMIN
    OPERATEUR_TERRAIN / OPERATEUR_LABO          → OPERATEUR
    MEDECIN_PSC / MEDECIN_ENTREPRISE            → MEDECIN

    Backward-compatible generic aliases (pre-V2 naming)
    ----------------------------------------------------
    DOCTOR       → MEDECIN
    OPERATOR     → OPERATEUR
    ACCOUNT_ADMIN→ RH_ENTREPRISE
    """

    ADMIN = "ADMIN"
    OPERATEUR = "OPERATEUR"
    MEDECIN = "MEDECIN"

    RH_ENTREPRISE = "RH_ENTREPRISE"
    PATIENT = "PATIENT"

    SYSTEME = "SYSTEME"

    # ── Retired V2 tier names — aliases to the merged V3 role ────────────────
    SUPER_ADMIN_PSC = "ADMIN"
    DIRECTEUR_PSC = "ADMIN"
    ADMIN_PSC = "ADMIN"
    OPERATEUR_TERRAIN = "OPERATEUR"
    OPERATEUR_LABO = "OPERATEUR"
    MEDECIN_PSC = "MEDECIN"
    MEDECIN_ENTREPRISE = "MEDECIN"

    # ── Backward-compatible pre-V2 aliases ────────────────────────────────────
    DOCTOR = "MEDECIN"
    OPERATOR = "OPERATEUR"
    ACCOUNT_ADMIN = "RH_ENTREPRISE"

    @classmethod
    def _missing_(cls, value: object):
        """Map raw DB strings from older schemas (pre-V2 and retired V2 tier
        names) to the current V3 members. Safety net for any row not yet
        touched by the V2→V3 migration — normal member values are matched
        before this is ever called.
        """
        _legacy = {
            # Pre-V2 raw DB values
            "DOCTOR": cls.MEDECIN,
            "OPERATOR": cls.OPERATEUR,
            "ACCOUNT_ADMIN": cls.RH_ENTREPRISE,
            # Retired V2 tier names
            "SUPER_ADMIN_PSC": cls.ADMIN,
            "DIRECTEUR_PSC": cls.ADMIN,
            "ADMIN_PSC": cls.ADMIN,
            "OPERATEUR_TERRAIN": cls.OPERATEUR,
            "OPERATEUR_LABO": cls.OPERATEUR,
            "MEDECIN_PSC": cls.MEDECIN,
            "MEDECIN_ENTREPRISE": cls.MEDECIN,
        }
        return _legacy.get(value)

    def get_label(self) -> str:
        labels = {
            CareRole.ADMIN: "Admin",
            CareRole.OPERATEUR: "Opérateur",
            CareRole.MEDECIN: "Médecin",
            CareRole.RH_ENTREPRISE: "RH entreprise",
            CareRole.PATIENT: "Patient / Employé",
            CareRole.SYSTEME: "Système",
        }
        return labels.get(self, self.value)

    def is_psc_staff(self) -> bool:
        """True for internal staff roles that have broad data access."""
        return self in (
            CareRole.ADMIN,
            CareRole.OPERATEUR,
            CareRole.MEDECIN,
        )

    def can_see_medical_data(self) -> bool:
        """True for roles authorised to see individual medical results."""
        return self in (
            CareRole.ADMIN,
            CareRole.OPERATEUR,
            CareRole.MEDECIN,
        )
