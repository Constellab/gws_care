"""ExamFile model — stores metadata for files attached to an exam."""

from gws_core import Model
from peewee import CharField, ForeignKeyField, IntegerField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.exam.exam import Exam


class ExamFile(Model):
    """A file attachment linked to an exam session.

    `stored_filename` is the UUID-prefixed name saved in the Reflex upload dir
    (used for in-app preview/download via rx.get_upload_url).
    `resource_id` is the gws_core ResourceModel id (so the file appears as a
    Resource in Constellab). Nullable for backward compatibility.
    `document_type` is the DocumentType enum value (string, nullable).
    """

    exam: Exam = ForeignKeyField(Exam, null=False, backref="files", on_delete="CASCADE")
    original_name: str = CharField(null=False)
    stored_filename: str = CharField(null=False)
    mime_type: str = CharField(null=True)
    file_size: int = IntegerField(null=True)
    resource_id: str = CharField(null=True)
    document_type: str = CharField(null=True)

    class Meta:
        table_name = "gws_care_exam_file"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
