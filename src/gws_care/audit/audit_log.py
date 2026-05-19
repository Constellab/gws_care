"""AuditLog model — immutable event journal (US-210)."""

from datetime import datetime
from enum import Enum

from peewee import CharField, DateTimeField, IntegerField, TextField

from gws_care.core.care_db_manager import CareDbManager
from gws_core import Model


class AuditAction(str, Enum):
    LOGIN = "LOGIN"
    VIEW_MEDICAL = "VIEW_MEDICAL"
    CREATE_PATIENT = "CREATE_PATIENT"
    UPDATE_PATIENT = "UPDATE_PATIENT"
    IMPORT_EMPLOYEES = "IMPORT_EMPLOYEES"
    VALIDATE = "VALIDATE"
    CORRECTION = "CORRECTION"
    EXPORT = "EXPORT"
    DOWNLOAD_PDF = "DOWNLOAD_PDF"
    ACCESS_DENIED = "ACCESS_DENIED"
    GENERATE_CERTIFICATE = "GENERATE_CERTIFICATE"
    MODIFY_RIGHTS = "MODIFY_RIGHTS"
    CREATE_CAMPAIGN = "CREATE_CAMPAIGN"
    CAMPAIGN_STATUS_CHANGE = "CAMPAIGN_STATUS_CHANGE"
    SEND_NOTIFICATION = "SEND_NOTIFICATION"
    PUBLISH_RESULTS = "PUBLISH_RESULTS"
    CREATE_PREBILLING = "CREATE_PREBILLING"

    def get_label(self) -> str:
        _labels = {
            "LOGIN": "Connexion",
            "VIEW_MEDICAL": "Consultation médicale",
            "CREATE_PATIENT": "Création patient",
            "UPDATE_PATIENT": "Modification patient",
            "IMPORT_EMPLOYEES": "Import employés",
            "VALIDATE": "Validation",
            "CORRECTION": "Correction",
            "EXPORT": "Export",
            "DOWNLOAD_PDF": "Téléchargement PDF",
            "ACCESS_DENIED": "Accès refusé",
            "GENERATE_CERTIFICATE": "Génération certificat",
            "MODIFY_RIGHTS": "Modification droits",
            "CREATE_CAMPAIGN": "Création campagne",
            "CAMPAIGN_STATUS_CHANGE": "Changement statut campagne",
            "SEND_NOTIFICATION": "Envoi notification",
            "PUBLISH_RESULTS": "Publication résultats",
            "CREATE_PREBILLING": "Création préfacturation",
        }
        return _labels.get(self.value, self.value)


class AuditLog(Model):
    """Immutable audit log entry. Never updated after creation."""

    user_id: int = IntegerField(null=True)
    user_email: str = CharField(max_length=255, null=True)
    action: str = CharField(max_length=50, null=False)
    resource_type: str = CharField(max_length=100, null=True)
    resource_id: int = IntegerField(null=True)
    details: str = TextField(null=True)
    ip_address: str = CharField(max_length=50, null=True)
    created_at: datetime = DateTimeField(default=datetime.now, null=False)

    class Meta:
        table_name = "gws_care_audit_log"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
