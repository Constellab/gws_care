import json
import uuid
from datetime import date

from gws_core import BadRequestException, NotFoundException

from gws_care.account.account import Account
from gws_care.patient.patient import Patient
from gws_care.patient.patient_account import PatientAccount
from gws_care.patient.patient_dto import SavePatientDTO


class PatientService:
    """CRUD service for Patient."""

    VALID_GENDERS = {"M", "F", "Other"}

    @classmethod
    def get_patient(cls, patient_id: str) -> Patient:
        patient = Patient.get_or_none(Patient.id == patient_id)
        if patient is None:
            raise NotFoundException(f"Patient '{patient_id}' not found")
        return patient

    @classmethod
    def get_patient_by_number(cls, patient_number: str) -> Patient:
        patient = Patient.get_or_none(Patient.patient_number == patient_number)
        if patient is None:
            raise NotFoundException(f"Patient number '{patient_number}' not found")
        return patient

    @classmethod
    def search_patients(
        cls,
        name: str | None = None,
        search: str | None = None,
        patient_number: str | None = None,
        patient_number_prefix: str | None = None,
        phone: str | None = None,
        account_id: str | None = None,
        dob_from: str | None = None,
        dob_to: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Patient]:
        query = Patient.select()
        if patient_number:
            query = query.where(Patient.patient_number == patient_number)
        if patient_number_prefix:
            query = query.where(Patient.patient_number.startswith(patient_number_prefix))
        if phone:
            query = query.where(Patient.phone == phone)
        term = search or name
        if term:
            query = query.where(
                Patient.last_name.contains(term)
                | Patient.first_name.contains(term)
            )
        if account_id:
            from peewee import JOIN
            query = (
                query
                .join(PatientAccount, JOIN.INNER, on=(PatientAccount.patient_id == Patient.id))
                .where(PatientAccount.account_id == account_id)
            )
        if dob_from:
            from datetime import date as date_type
            query = query.where(Patient.date_of_birth >= date_type.fromisoformat(dob_from))
        if dob_to:
            from datetime import date as date_type
            query = query.where(Patient.date_of_birth <= date_type.fromisoformat(dob_to))
        query = query.order_by(Patient.last_name, Patient.first_name)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return list(query)

    @classmethod
    def list_patients_for_account(cls, account_id: str) -> list[Patient]:
        """Return all patients linked to the given account."""
        from peewee import JOIN
        return list(
            Patient.select()
            .join(PatientAccount, JOIN.INNER, on=(PatientAccount.patient_id == Patient.id))
            .where(PatientAccount.account_id == account_id)
            .order_by(Patient.last_name, Patient.first_name)
        )

    @classmethod
    def add_account(cls, patient_id: str, account_id: str) -> None:
        """Link a patient to a billing account (many-to-many)."""
        patient = cls.get_patient(patient_id)
        account = Account.get_or_none(Account.id == account_id)
        if account is None:
            raise NotFoundException(f"Account '{account_id}' not found")
        # get_or_create avoids duplicate-key error if already linked
        PatientAccount.get_or_create(patient=patient, account=account)

    @classmethod
    def remove_account(cls, patient_id: str, account_id: str) -> None:
        """Remove the link between a patient and a billing account."""
        PatientAccount.delete().where(
            (PatientAccount.patient_id == patient_id)
            & (PatientAccount.account_id == account_id)
        ).execute()

    @classmethod
    def create_patient(cls, dto: SavePatientDTO) -> Patient:
        cls._validate(dto)
        patient = Patient()
        patient.patient_number = cls._generate_patient_number()
        cls._apply_dto(patient, dto)
        # Generate QR code on creation (encode patient_number)
        try:
            from gws_care.qr_code import generate_patient_qr_data_uri
            patient.qr_code = generate_patient_qr_data_uri(patient.patient_number)
        except Exception:
            patient.qr_code = None  # non-fatal
        patient.save()
        # Link to account if provided
        if dto.account_id:
            account = Account.get_or_none(Account.id == dto.account_id)
            if account is not None:
                PatientAccount.get_or_create(patient=patient, account=account)
        return patient

    @classmethod
    def get_qr_code(cls, patient_id: str) -> str | None:
        """Return the patient's QR code data URI, generating it if absent.

        Returns None if the patient doesn't exist.
        """
        patient = Patient.get_or_none(Patient.id == patient_id)
        if patient is None:
            return None
        if not patient.qr_code:
            try:
                from gws_care.qr_code import generate_patient_qr_data_uri
                patient.qr_code = generate_patient_qr_data_uri(patient.patient_number)
                patient.save()
            except Exception:
                return None
        return patient.qr_code

    @classmethod
    def update_patient(cls, patient_id: str, dto: SavePatientDTO) -> Patient:
        cls._validate(dto)
        patient = cls.get_patient(patient_id)
        cls._apply_dto(patient, dto)
        patient.save()
        # Update account link if provided
        if dto.account_id:
            account = Account.get_or_none(Account.id == dto.account_id)
            if account is not None:
                PatientAccount.get_or_create(patient=patient, account=account)
        return patient

    @classmethod
    def _validate(cls, dto: SavePatientDTO) -> None:
        if not dto.last_name or not dto.last_name.strip():
            raise BadRequestException("Last name is required")
        if not dto.first_name or not dto.first_name.strip():
            raise BadRequestException("First name is required")
        if dto.gender not in cls.VALID_GENDERS:
            raise BadRequestException(f"Gender must be one of: {', '.join(cls.VALID_GENDERS)}")
        if dto.date_of_birth > date.today():
            raise BadRequestException("Date of birth cannot be in the future")

    @classmethod
    def _apply_dto(cls, patient: Patient, dto: SavePatientDTO) -> None:
        patient.last_name = dto.last_name.strip().upper()
        patient.first_name = dto.first_name.strip()
        patient.birth_name = dto.birth_name
        patient.date_of_birth = dto.date_of_birth
        patient.gender = dto.gender
        patient.photo = dto.photo
        patient.address = dto.address
        patient.postal_code = dto.postal_code
        patient.city = dto.city
        patient.phone = dto.phone
        patient.email = dto.email
        patient.primary_physician_name = dto.primary_physician_name
        patient.primary_physician_phone = dto.primary_physician_phone
        patient.social_security_number = dto.social_security_number
        patient.weight = dto.weight
        patient.height = dto.height
        patient.sex = dto.sex if dto.sex in ("M", "F", "Autre") else None
        patient.notification_preferences = (
            json.dumps(dto.notification_preferences) if dto.notification_preferences else None
        )

    @classmethod
    def _generate_patient_number(cls) -> str:
        """Generate a unique patient number in the format PAT-XXXXXXXX."""
        while True:
            number = f"PAT-{uuid.uuid4().hex[:8].upper()}"
            if not Patient.get_or_none(Patient.patient_number == number):
                return number
