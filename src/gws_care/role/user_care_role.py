"""UserCareRole model — join table linking a local User to a CareRole."""

from gws_core import EnumField, Model
from peewee import ForeignKeyField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.role.care_role import CareRole
from gws_care.user.user import User


class UserCareRole(Model):
    """Associates a CareRole with a local User.

    One row per (user, role) pair — a user may hold multiple roles.
    """

    user: User = ForeignKeyField(User, null=False, backref="care_roles", on_delete="CASCADE")
    role: CareRole = EnumField(choices=CareRole, null=False)

    class Meta:
        table_name = "gws_care_user_role"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
        indexes = (
            (("user", "role"), True),   # unique constraint: one role per user
        )
