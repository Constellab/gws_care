"""PatientNote — free-form doctor notes attached to a patient's dossier."""

from datetime import datetime

from gws_core import Model
from peewee import CharField, DateTimeField, ForeignKeyField, TextField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.patient.patient import Patient


class PatientNote(Model):
    """A free-form note written by a doctor about a patient.

    Notes are dossier-level (not tied to a specific exam or campaign).
    `author_name` stores the doctor's display name as a plain string so
    notes remain readable even after a user account is removed.
    """

    patient: Patient = ForeignKeyField(Patient, null=False, backref="notes", on_delete="CASCADE")
    author_name: str = CharField(max_length=255, null=True)
    content: str = TextField(null=False)
    created_at: datetime = DateTimeField(default=datetime.now, null=False)

    class Meta:
        table_name = "gws_care_patient_note"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
