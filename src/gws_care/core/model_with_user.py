from gws_core import CurrentUserService, Model
from peewee import ForeignKeyField

from gws_care.user.user import User


class ModelWithUser(Model):
    """
    Base model with created_by and last_modified_by columns.
    """

    created_by = ForeignKeyField(User, null=False, backref='+')
    last_modified_by = ForeignKeyField(User, null=False, backref='+')

    def _before_insert(self) -> None:
        super()._before_insert()
        current_user = CurrentUserService.get_and_check_current_user()
        self.created_by = current_user
        self.last_modified_by = current_user

    def _before_update(self) -> None:
        super()._before_update()
        current_user = CurrentUserService.get_and_check_current_user()
        self.last_modified_by = current_user
