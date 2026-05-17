"""Singleton application configuration model."""

from gws_core import Model
from peewee import IntegerField

from gws_care.core.care_db_manager import CareDbManager


class CareAppConfig(Model):
    """One-row singleton storing app-wide configuration (e.g. list page size)."""

    list_page_size: int = IntegerField(default=50, null=False)

    class Meta:
        table_name = "gws_care_app_config"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
