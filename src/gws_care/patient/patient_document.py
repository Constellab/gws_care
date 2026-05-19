"""PatientDocument — files uploaded to a patient's dossier (independent of any exam)."""

from datetime import datetime

from gws_core import Model
from peewee import CharField, DateTimeField, ForeignKeyField, IntegerField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.patient.patient import Patient

# Human-readable labels for each document type code
PATIENT_DOCUMENT_TYPE_LABELS: dict[str, str] = {
    "identite": "Pièce d'identité",
    "ordonnance": "Ordonnance",
    "resultat_anterieur": "Résultats antérieurs",
    "radio": "Radiographie",
    "scanner": "Scanner / IRM",
    "certificat": "Certificat médical",
    "autre": "Autre",
}


class PatientDocument(Model):
    """A file attached directly to a patient's dossier (not to a specific exam).

    `stored_filename` is the UUID-prefixed name saved in the Reflex upload dir.
    `document_type` is one of the PATIENT_DOCUMENT_TYPE_LABELS keys.
    `uploaded_by_name` stores the author's display name as a plain string.
    """

    patient: Patient = ForeignKeyField(Patient, null=False, backref="documents", on_delete="CASCADE")
    original_name: str = CharField(max_length=500, null=False)
    stored_filename: str = CharField(max_length=500, null=False)
    mime_type: str = CharField(max_length=200, null=True)
    file_size: int = IntegerField(null=True)
    document_type: str = CharField(max_length=100, null=True)
    uploaded_by_name: str = CharField(max_length=255, null=True)
    created_at: datetime = DateTimeField(default=datetime.now, null=False)

    def get_type_label(self) -> str:
        if not self.document_type:
            return "Autre"
        return PATIENT_DOCUMENT_TYPE_LABELS.get(self.document_type, self.document_type)

    class Meta:
        table_name = "gws_care_patient_document"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
