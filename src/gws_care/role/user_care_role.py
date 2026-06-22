"""UserCareRole model — join table linking a local User to a CareRole."""

from gws_core import EnumField, Model
from peewee import BooleanField, CharField, ForeignKeyField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.role.care_role import CareRole
from gws_care.user.user import User


class UserCareRole(Model):
    """Associates a CareRole with a local User.

    One row per (user, role) pair — a user may hold multiple roles.

    Scoping rules:
      - For DOCTOR: ``all_patients=True`` means global access to all patients
        (default). When False, access is restricted to the patients listed in
        ``UserCareRoleAccount`` for this user/role pair.
      - For ACCOUNT_ADMIN: access restricted to accounts in ``UserCareRoleAccount``
        (``all_patients`` is ignored).
      - For PATIENT: ``linked_patient_id`` still holds the single patient link.
    """

    user: User = ForeignKeyField(User, null=False, backref="care_roles", on_delete="CASCADE")
    role: CareRole = EnumField(choices=CareRole, null=False)
    # Kept for PATIENT role only (single patient link)
    linked_patient_id: str = CharField(max_length=36, null=True)
    # For DOCTOR role: link to a registered MedicalDoctor profile
    linked_doctor_id: str = CharField(max_length=36, null=True)
    # For DOCTOR role: True = global patient access, False = scoped to UserCareRoleAccount entries
    all_patients: bool = BooleanField(default=True, null=False)

    class Meta:
        table_name = "gws_care_user_role"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
        indexes = (
            (("user", "role"), True),   # unique constraint: one role per user
        )
