"""PermissionService — central, declarative access-control layer.

Based on the access matrix defined in SPEC_CONSTELLAB_CARE_v2.md Section 4.

Role summary
============
ADMIN          → Super Admin PSC — full access (platform admin also counts)
OPERATOR       → HQ Operator PSC — lab data entry and lab validation
DOCTOR         → Clinic Doctor PSC — medical interpretation and clinic validation
ACCOUNT_ADMIN  → Company Doctor / Responsable RH — scoped to one account
PATIENT        → Employé — read-only access to own data

Usage
=====
# In a service method:
from gws_care.role.permission_service import PermissionService
from gws_care.role.care_action import CareAction

PermissionService.require(user, CareAction.VISIT_VALIDATE_LAB)
# raises ForbiddenException if the user lacks the required role.

# Soft check (returns bool):
if not PermissionService.can(user, CareAction.CAMPAIGN_VALIDATE_CLINIC):
    ...
"""

from __future__ import annotations

from gws_core import ForbiddenException

from gws_care.role.care_action import CareAction
from gws_care.role.care_role import CareRole

# Map action → set of roles that may perform it (ADMIN is always implicitly allowed)
_PERMISSION_MAP: dict[CareAction, frozenset[CareRole]] = {
    # ── MedicalProgram ─────────────────────────────────────────────────────────────
    CareAction.CAMPAIGN_CREATE:         frozenset({CareRole.OPERATOR}),
    CareAction.CAMPAIGN_UPDATE:         frozenset({CareRole.OPERATOR}),
    CareAction.CAMPAIGN_VALIDATE_INITIAL: frozenset({CareRole.DOCTOR}),
    CareAction.CAMPAIGN_START:          frozenset({CareRole.OPERATOR}),
    CareAction.CAMPAIGN_VALIDATE_LAB:   frozenset({CareRole.OPERATOR}),
    CareAction.CAMPAIGN_VALIDATE_CLINIC: frozenset({CareRole.DOCTOR}),
    CareAction.CAMPAIGN_ARCHIVE:        frozenset({CareRole.OPERATOR, CareRole.DOCTOR}),

    # ── Visit ────────────────────────────────────────────────────────────────
    CareAction.VISIT_READ:              frozenset({CareRole.OPERATOR, CareRole.DOCTOR, CareRole.ACCOUNT_ADMIN}),
    CareAction.VISIT_MARK_TERRAIN_DONE: frozenset({CareRole.OPERATOR}),
    CareAction.VISIT_MARK_RESULTS_ENTERED: frozenset({CareRole.OPERATOR}),
    CareAction.VISIT_VALIDATE_LAB:      frozenset({CareRole.OPERATOR}),
    CareAction.VISIT_VALIDATE_CLINIC:   frozenset({CareRole.DOCTOR}),
    CareAction.VISIT_VALIDATE_COMPANY:  frozenset({CareRole.ACCOUNT_ADMIN}),

    # ── Exam results ─────────────────────────────────────────────────────────
    CareAction.EXAM_RESULT_WRITE:       frozenset({CareRole.OPERATOR}),
    CareAction.EXAM_APPRECIATION_OVERRIDE: frozenset({CareRole.DOCTOR}),
    CareAction.EXAM_INTERPRET:          frozenset({CareRole.DOCTOR}),

    # ── Patient data ─────────────────────────────────────────────────────────
    CareAction.PATIENT_READ:            frozenset({CareRole.OPERATOR, CareRole.DOCTOR, CareRole.ACCOUNT_ADMIN}),
    CareAction.PATIENT_READ_OWN:        frozenset({CareRole.PATIENT}),
    CareAction.PATIENT_WRITE:           frozenset({CareRole.OPERATOR}),

    # ── Account data ─────────────────────────────────────────────────────────
    CareAction.ACCOUNT_READ:            frozenset({CareRole.OPERATOR, CareRole.DOCTOR, CareRole.ACCOUNT_ADMIN}),
    CareAction.ACCOUNT_WRITE:           frozenset({CareRole.OPERATOR}),

    # ── Certificate ──────────────────────────────────────────────────────────
    CareAction.CERTIFICATE_GENERATE:    frozenset({CareRole.ACCOUNT_ADMIN}),

    # ── Notifications ─────────────────────────────────────────────────────────
    CareAction.NOTIFICATION_SEND:       frozenset({CareRole.OPERATOR, CareRole.DOCTOR, CareRole.ACCOUNT_ADMIN}),

    # ── Administration ────────────────────────────────────────────────────────
    CareAction.USER_MANAGE:             frozenset(),  # ADMIN only
    CareAction.EXAM_TYPE_MANAGE:        frozenset(),  # ADMIN only
}


class PermissionService:
    """Central access control service.

    All checks are performed against the `UserCareRole` table for the given user.
    ADMIN role and gws_core platform admin users bypass all checks.
    """

    @classmethod
    def _get_user_roles(cls, user: "User") -> list[CareRole]:  # noqa: F821
        """Load the user's CareRoles from the DB (cached pattern not needed here)."""
        from gws_care.role.user_role_service import UserRoleService
        return UserRoleService.get_roles_for_user(str(user.id))

    @classmethod
    def _is_platform_admin(cls, user: "User") -> bool:  # noqa: F821
        """Return True if the user has gws_core ADMIN group."""
        try:
            from gws_core import UserGroup
            return getattr(user, "group", None) == UserGroup.ADMIN
        except Exception:
            return False

    @classmethod
    def can(cls, user: "User", action: CareAction) -> bool:  # noqa: F821
        """Return True if the user is allowed to perform *action*.

        ADMIN role and platform admins bypass all restrictions.
        """
        if cls._is_platform_admin(user):
            return True

        roles = cls._get_user_roles(user)

        if CareRole.ADMIN in roles:
            return True

        allowed_roles = _PERMISSION_MAP.get(action, frozenset())
        return bool(allowed_roles.intersection(roles))

    @classmethod
    def require(cls, user: "User", action: CareAction) -> None:  # noqa: F821
        """Raise ``ForbiddenException`` if the user may NOT perform *action*.

        Use this as a guard at the top of service methods.

        Example::

            PermissionService.require(user, CareAction.VISIT_VALIDATE_LAB)
        """
        if not cls.can(user, action):
            raise ForbiddenException(
                f"You do not have permission to perform '{action.value}'. "
                "Contact your administrator to request access."
            )

    @classmethod
    def require_own_account(cls, user: "User", account_id: str) -> None:  # noqa: F821
        """Require that an ACCOUNT_ADMIN user's linked account matches *account_id*.

        ADMIN / platform admins bypass this check.
        """
        if cls._is_platform_admin(user):
            return
        roles = cls._get_user_roles(user)
        if CareRole.ADMIN in roles:
            return
        # OPERATOR or DOCTOR have unrestricted account visibility
        if CareRole.OPERATOR in roles or CareRole.DOCTOR in roles:
            return
        if CareRole.ACCOUNT_ADMIN in roles:
            from gws_care.role.user_role_service import UserRoleService
            linked = UserRoleService.get_linked_account_id(str(user.id))
            if linked and linked == account_id:
                return
            raise ForbiddenException(
                "You can only access data belonging to your own account."
            )
        raise ForbiddenException(
            "You do not have permission to access this account's data."
        )

    @classmethod
    def require_own_patient(cls, user: "User", patient_id: str) -> None:  # noqa: F821
        """Require that a PATIENT user's linked patient ID matches *patient_id*.

        ADMIN / platform admins bypass; OPERATOR and DOCTOR have full access.
        """
        if cls._is_platform_admin(user):
            return
        roles = cls._get_user_roles(user)
        if CareRole.ADMIN in roles or CareRole.OPERATOR in roles or CareRole.DOCTOR in roles:
            return
        if CareRole.ACCOUNT_ADMIN in roles:
            # Account admins can read patients of their account — deeper check
            # is done at the service level with require_own_account.
            return
        if CareRole.PATIENT in roles:
            from gws_care.role.user_role_service import UserRoleService
            linked = UserRoleService.get_linked_patient_id(str(user.id))
            if linked and linked == patient_id:
                return
            raise ForbiddenException(
                "You can only access your own patient data."
            )
        raise ForbiddenException(
            "You do not have permission to access this patient's data."
        )
