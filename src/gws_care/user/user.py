from gws_core import EnumField, Model, UserDTO, UserGroup
from gws_core import User as GwsCoreUser
from peewee import BooleanField, CharField

from gws_care.core.care_db_manager import CareDbManager


class User(Model):
    email: str = CharField()
    first_name: str = CharField()
    last_name: str = CharField()
    group: UserGroup = EnumField(choices=UserGroup, default=UserGroup.USER)
    is_active = BooleanField(default=True)
    photo: str = CharField(null=True)

    def to_dto(self) -> UserDTO:
        return UserDTO(
            id=self.id,
            email=self.email,
            first_name=self.first_name,
            last_name=self.last_name,
            photo=self.photo,
        )

    @classmethod
    def get_real_users(cls) -> list["User"]:
        """Get all non-system active users, ordered alphabetically by first then last name.

        :return: List of real users (excludes SYSUSER group)
        :rtype: list[User]
        """
        return list(
            User.select()
            .where(User.group != UserGroup.SYSUSER)
            .order_by(User.first_name, User.last_name)
        )

    @classmethod
    def from_gws_core_user(cls, gws_core_user: GwsCoreUser) -> "User":
        return User(
            id=gws_core_user.id,
            email=gws_core_user.email,
            first_name=gws_core_user.first_name,
            last_name=gws_core_user.last_name,
            group=gws_core_user.group,
            is_active=gws_core_user.is_active,
            photo=gws_core_user.photo,
            created_at=gws_core_user.created_at,
            last_modified_at=gws_core_user.last_modified_at,
        )

    class Meta:
        table_name = "gws_care_user"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
