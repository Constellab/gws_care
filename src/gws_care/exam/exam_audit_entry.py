"""ExamAuditEntry — immutable per-exam action log.

Tracks unusual actions performed on an exam's tests (add / remove a test,
modify an already-recorded value, transmit to the lab) separately from
``Exam.interpretation``, which is reserved for the doctor's free-text medical
interpretation.
"""

from __future__ import annotations

from enum import Enum

from peewee import CharField, ForeignKeyField, TextField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.exam.exam import Exam


class ExamAuditAction(str, Enum):
    ADD_TEST = "ADD_TEST"
    REMOVE_TEST = "REMOVE_TEST"
    MODIFY_VALUE = "MODIFY_VALUE"
    TRANSMIT_TO_LAB = "TRANSMIT_TO_LAB"

    def get_label(self) -> str:
        return {
            "ADD_TEST": "Ajout de test",
            "REMOVE_TEST": "Suppression de test",
            "MODIFY_VALUE": "Modification de valeur",
            "TRANSMIT_TO_LAB": "Transmission au labo",
        }[self.value]


class ExamAuditEntry(ModelWithUser):
    """One immutable audit entry for an unusual action performed on an exam.

    ``created_by`` (from ``ModelWithUser``) and ``created_at`` (from ``Model``)
    are auto-populated on insert from the authenticated user context.
    """

    exam: Exam = ForeignKeyField(
        Exam, null=False, backref="audit_entries", on_delete="CASCADE", index=True
    )
    action: str = CharField(max_length=30, null=False)
    details: str = TextField(null=True)

    class Meta:
        table_name = "gws_care_exam_audit_entry"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
