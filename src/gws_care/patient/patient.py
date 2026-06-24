import json
from datetime import date

from peewee import BooleanField, CharField, DateField, DecimalField, ForeignKeyField, TextField

from gws_care.core.care_db_manager import CareDbManager
from gws_care.core.model_with_user import ModelWithUser

from .patient_dto import PatientDTO


class Patient(ModelWithUser):
    """
    Patient file. The patient_number is auto-generated and unique.
    """

    patient_number: str = CharField(max_length=50, unique=True, null=False, index=True)
    last_name: str = CharField(max_length=150, null=False)
    first_name: str = CharField(max_length=150, null=False)
    birth_name: str = CharField(max_length=150, null=True)
    date_of_birth: date = DateField(null=False)
    # M / F / Other
    gender: str = CharField(max_length=10, null=False)
    sex: str = CharField(max_length=10, null=True)  # M / F / Autre (used on patient card)
    nationality: str = CharField(max_length=100, null=True)
    photo: str = TextField(null=True)
    address: str = TextField(null=True)
    address_complement: str = TextField(null=True)
    postal_code: str = CharField(max_length=20, null=True)
    city: str = CharField(max_length=100, null=True)
    country: str = CharField(max_length=100, null=True)
    # Phone stored as "<country_code>|<number>", e.g. "+33|0612345678"
    phone: str = CharField(max_length=50, null=True)
    phone_country: str = CharField(max_length=10, null=True)
    email: str = CharField(max_length=255, null=True)
    social_security_number: str = CharField(max_length=30, null=True)
    weight = DecimalField(null=True, decimal_places=2, max_digits=6)  # kg
    height = DecimalField(null=True, decimal_places=2, max_digits=5)  # cm
    # JSON: {"email": bool, "sms": bool, "whatsapp": bool}
    notification_preferences: str = TextField(null=True)
    # QR code stored as base64 PNG string (data:image/png;base64,...)
    qr_code: str = TextField(null=True)
    # Permanent token for QR identity
    qr_token: str = CharField(max_length=12, unique=True, null=True, index=True)

    # Primary physician info
    primary_physician_name: str = CharField(max_length=255, null=True)
    primary_physician_phone: str = CharField(max_length=50, null=True)

    # Billing account FK
    from gws_care.account.account import Account
    billing_account: Account = ForeignKeyField(Account, null=True, backref="patients", on_delete="SET NULL")

    # company_id: plain string FK — column managed via migration
    company_id: str = CharField(max_length=36, null=True)

    # Draft flag: True = patient record is incomplete, to be completed later
    is_draft: bool = BooleanField(default=False, null=False)

    # Archive flag
    is_archived: bool = BooleanField(default=False, null=False)
    archived_reason: str = TextField(null=True)
    archived_at: str = CharField(max_length=50, null=True)

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def get_age(self) -> int:
        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - (
                (today.month, today.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )
        )

    def to_dto(self) -> PatientDTO:
        notif_prefs = None
        if self.notification_preferences:
            try:
                notif_prefs = json.loads(self.notification_preferences)
            except Exception:
                notif_prefs = None
        from gws_care.patient.patient_account import PatientAccount
        account_ids = [
            str(pa.account_id)
            for pa in PatientAccount.select().where(PatientAccount.patient == self.id)
        ]
        return PatientDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            patient_number=self.patient_number,
            last_name=self.last_name,
            first_name=self.first_name,
            birth_name=self.birth_name,
            date_of_birth=self.date_of_birth,
            gender=self.gender,
            sex=self.sex,
            nationality=self.nationality,
            photo=self.photo,
            address=self.address,
            address_complement=self.address_complement,
            postal_code=self.postal_code,
            city=self.city,
            country=self.country,
            phone=self.phone,
            phone_country=self.phone_country,
            email=self.email,
            primary_physician_name=self.primary_physician_name,
            primary_physician_phone=self.primary_physician_phone,
            account_ids=account_ids,
            company_id=self.company_id or None,
            social_security_number=self.social_security_number,
            weight=float(self.weight) if self.weight is not None else None,
            height=float(self.height) if self.height is not None else None,
            notification_preferences=notif_prefs,
            is_draft=bool(self.is_draft),
        )

    class Meta:
        table_name = "gws_care_patient"
        database = CareDbManager.get_instance().db
        is_table = True
        db_manager = CareDbManager.get_instance()
