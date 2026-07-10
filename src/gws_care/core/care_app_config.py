"""Singleton application configuration model."""

from gws_core import Model
from peewee import CharField, IntegerField

from gws_care.core.care_db_manager import CareDbManager


class CareAppConfig(Model):
    """One-row singleton storing app-wide configuration (e.g. list page size, organization info)."""

    list_page_size: int = IntegerField(default=50, null=False)
    color_theme: str = CharField(max_length=20, default="green", null=False)

    # Organization identity — replaces hardcoded "PSC" throughout the UI
    org_name: str = CharField(max_length=200, default="", null=False)
    org_acronym: str = CharField(max_length=20, default="PSC", null=False)
    org_siret: str = CharField(max_length=50, default="", null=False)
    org_phone: str = CharField(max_length=50, default="", null=False)
    org_email: str = CharField(max_length=200, default="", null=False)
    # Address — split into structured fields (same pattern as Patient)
    org_address: str = CharField(max_length=500, default="", null=False)
    org_address_complement: str = CharField(max_length=500, default="", null=False)
    org_postal_code: str = CharField(max_length=20, default="", null=False)
    org_city: str = CharField(max_length=100, default="", null=False)
    org_country: str = CharField(max_length=100, default="France", null=False)

    class Meta:
        table_name = "gws_care_app_config"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
