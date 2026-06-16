"""State for the Database admin tab — dev-mode only DB flush."""

import reflex as rx

from ..common.role_state import RoleState

FLUSH_CONFIRM_PHRASE = (
    "I am in dev mode, I want to flush the database, "
    "and I know that all data will be definitively lost"
)


class DatabaseState(RoleState):

    db_flush_open: bool = False
    db_flush_confirm_text: str = ""
    db_flush_is_flushing: bool = False
    db_flush_error: str = ""
    db_flush_success: str = ""

    @rx.var
    def is_dev_mode(self) -> bool:
        from gws_core import Settings
        return Settings.is_dev_mode()

    @rx.var
    def flush_confirm_valid(self) -> bool:
        return self.db_flush_confirm_text == FLUSH_CONFIRM_PHRASE

    @rx.event
    def open_flush_dialog(self):
        self.db_flush_confirm_text = ""
        self.db_flush_error = ""
        self.db_flush_success = ""
        self.db_flush_open = True

    @rx.event
    def close_flush_dialog(self):
        self.db_flush_open = False
        self.db_flush_confirm_text = ""
        self.db_flush_error = ""

    @rx.event
    def set_flush_confirm_text(self, value: str):
        self.db_flush_confirm_text = value

    @rx.event
    async def flush_database(self):
        if self.db_flush_confirm_text != FLUSH_CONFIRM_PHRASE:
            self.db_flush_error = "Confirmation phrase does not match."
            return
        self.db_flush_is_flushing = True
        self.db_flush_error = ""
        db = None
        try:
            with await self.authenticate_user():
                from gws_care.core.care_db_manager import CareDbManager
                db = CareDbManager.get_instance().db
                cursor = db.execute_sql("SHOW TABLES")
                tables = [row[0] for row in cursor.fetchall()]
                db.execute_sql("SET FOREIGN_KEY_CHECKS = 0")
                for table in tables:
                    db.execute_sql(f"TRUNCATE TABLE `{table}`")
                db.execute_sql("SET FOREIGN_KEY_CHECKS = 1")
                count = len(tables)
            self.db_flush_success = f"Done — {count} table(s) cleared."
            self.db_flush_open = False
        except Exception as e:
            self.db_flush_error = str(e)
            if db is not None:
                try:
                    db.execute_sql("SET FOREIGN_KEY_CHECKS = 1")
                except Exception:
                    pass
        finally:
            self.db_flush_is_flushing = False
