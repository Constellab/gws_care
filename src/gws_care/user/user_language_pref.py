"""Per-user language preference model."""

from gws_core import Model
from peewee import CharField

from gws_care.core.care_db_manager import CareDbManager


class UserLanguagePref(Model):
    """Stores the display language preference for a single user."""

    user_id: str = CharField(max_length=36, unique=True, null=False, index=True)
    language: str = CharField(max_length=10, default="en", null=False)

    class Meta:
        table_name = "gws_care_user_language_pref"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
