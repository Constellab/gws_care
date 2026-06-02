"""PatientDeletionLog — audit trail for patient deletions."""

from datetime import datetime

from gws_core import Model
from peewee import CharField, DateTimeField

from gws_care.core.care_db_manager import CareDbManager


class PatientDeletionLog(Model):
    """Audit log entry created whenever a patient is permanently deleted.

    The patient FK is intentionally stored as a plain string (patient_db_id) so
    the log remains readable after the patient row has been deleted.
    """

    patient_db_id: str = CharField(max_length=36, null=False)
    patient_number: str = CharField(max_length=50, null=False)
    patient_name: str = CharField(max_length=300, null=False)
    reason: str = CharField(max_length=2000, null=False)
    deleted_by: str = CharField(max_length=255, null=True)
    deleted_at: datetime = DateTimeField(default=datetime.now, null=False)

    class Meta:
        table_name = "gws_care_patient_deletion_log"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
