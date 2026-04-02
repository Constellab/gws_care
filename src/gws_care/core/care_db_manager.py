from typing import Optional

from gws_core import LazyAbstractDbManager
from peewee import DatabaseProxy


class CareDbManager(LazyAbstractDbManager):
    """
    DbManager for the gws_care brick.
    """

    db = DatabaseProxy()

    _instance: Optional['CareDbManager'] = None

    @classmethod
    def get_instance(cls) -> 'CareDbManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_name(self) -> str:
        return 'db'

    def get_brick_name(self) -> str:
        return 'gws_care'
