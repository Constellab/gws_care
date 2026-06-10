"""UploadedDocument model — standalone document upload, not tied to any Exam."""

from datetime import date

from peewee import CharField, DateField, ForeignKeyField, TextField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser
from gws_care.patient.patient import Patient


class UploadedDocument(ModelWithUser):
    """A document uploaded directly by staff (not linked to an Exam).

    The file is stored in the gws_core file store (resource_id).
    ``doc_type`` / ``doc_date`` / ``description`` are the user-confirmed values.
    """

    patient: Patient = ForeignKeyField(
        Patient, null=True, backref="uploaded_documents", on_delete="SET NULL"
    )
    doc_type: str = CharField(max_length=80, null=True)
    doc_date: date = DateField(null=True)
    description: str = TextField(null=True)
    notes: str = TextField(null=True)
    original_name: str = CharField(max_length=500, null=False, default="")
    resource_id: str = CharField(max_length=36, null=True)

    class Meta:
        table_name = "gws_care_uploaded_document"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
