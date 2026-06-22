"""UserCareRoleAccount — many-to-many between (User, CareRole) and a linked entity.

The ``account_id`` column is a generic entity-ID field:
  - For DOCTOR rows      : stores **patient IDs** (one row per allowed patient).
    When ``UserCareRole.all_patients=True`` this table is ignored (global access).
  - For ACCOUNT_ADMIN rows: stores **account IDs** (one row per administered account).
"""

from gws_core import EnumField, Model
from peewee import CharField, ForeignKeyField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.role.care_role import CareRole
from gws_care.user.user import User


class UserCareRoleAccount(Model):
    """Links a (user, role) pair to a specific account ID."""

    user: User = ForeignKeyField(User, null=False, backref="role_accounts", on_delete="CASCADE")
    role: CareRole = EnumField(choices=CareRole, null=False)
    account_id: str = CharField(max_length=36, null=False)

    class Meta:
        table_name = "gws_care_user_role_account"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
        indexes = (
            (("user", "role", "account_id"), True),  # unique per (user, role, account)
        )
