"""Per-user application configuration model."""

from gws_core import Model
from peewee import CharField, IntegerField

from gws_care.core.care_db_manager import CareDbManager


class UserAppConfig(Model):
    """One row per user, storing personal app preferences (page size, color theme)."""

    user_id: str = CharField(max_length=36, index=True, unique=True)
    page_size: int = IntegerField(default=50)
    color_theme: str = CharField(max_length=20, default="green")

    class Meta:
        table_name = "gws_care_user_app_config"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
