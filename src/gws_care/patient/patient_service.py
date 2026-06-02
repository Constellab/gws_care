import uuid
from datetime import date

from peewee import JOIN
from gws_core import BadRequestException, NotFoundException

from gws_care.account.account import Account
from gws_care.patient.patient import Patient
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
    def count_patients(
        cls,
        name: str | None = None,
        patient_number: str | None = None,
        phone: str | None = None,
        account_id: str | None = None,
        dob_from: str | None = None,
        dob_to: str | None = None,
    ) -> int:
        """Return total count matching the given filters (for pagination)."""
        return cls._build_query(
            name=name, patient_number=patient_number, phone=phone,
            account_id=account_id, dob_from=dob_from, dob_to=dob_to,
        ).count()

    @classmethod
    def search_patients(
        cls,
        name: str | None = None,
        patient_number: str | None = None,
        phone: str | None = None,
        account_id: str | None = None,
        dob_from: str | None = None,
        dob_to: str | None = None,
        sort_column: str = "last_name",
        sort_ascending: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Patient]:
        query = cls._build_query(
            name=name, patient_number=patient_number, phone=phone,
            account_id=account_id, dob_from=dob_from, dob_to=dob_to,
        )
        # Sorting
        _sort_map = {
            "last_name": Patient.last_name,
            "first_name": Patient.first_name,
            "patient_number": Patient.patient_number,
            "date_of_birth": Patient.date_of_birth,
            "gender": Patient.gender,
            "city": Patient.city,
            "phone": Patient.phone,
            "account_name": Account.name,
        }
        sort_field = _sort_map.get(sort_column, Patient.last_name)
        query = query.order_by(
            sort_field.asc() if sort_ascending else sort_field.desc(),
            Patient.first_name,
        )
        return list(query.limit(limit).offset(offset))

    @classmethod
    def _build_query(
        cls,
        name: str | None = None,
        patient_number: str | None = None,
        phone: str | None = None,
        account_id: str | None = None,
        dob_from: str | None = None,
        dob_to: str | None = None,
    ):
        """Shared query builder (no ordering/limit) used by both search and count."""
        query = (
            Patient.select(Patient, Account)
            .join(Account, JOIN.LEFT_OUTER, on=(Patient.billing_account == Account.id))
        )
        if patient_number:
            query = query.where(Patient.patient_number == patient_number)
        if phone:
            query = query.where(Patient.phone.contains(phone))
        if name:
            query = query.where(
                Patient.last_name.contains(name)
                | Patient.first_name.contains(name)
            )
        if account_id:
            from gws_care.company.company_service import CompanyService
            company_id = CompanyService.get_company_id_for_account(account_id)
            if company_id:
                query = query.where(
                    (Patient.billing_account == account_id)
                    | (Patient.company_id == company_id)
                )
            else:
                query = query.where(Patient.billing_account == account_id)
        if dob_from:
            from datetime import date as date_type
            query = query.where(Patient.date_of_birth >= date_type.fromisoformat(dob_from))
        if dob_to:
            from datetime import date as date_type
            query = query.where(Patient.date_of_birth <= date_type.fromisoformat(dob_to))
        return query

    @classmethod
    def list_patients_for_account(cls, account_id: str) -> list[Patient]:
        """Return all patients belonging to the given account."""
        return list(
            Patient.select()
            .where(Patient.billing_account == account_id)
            .order_by(Patient.last_name, Patient.first_name)
        )

    @classmethod
    def list_patients_for_company(cls, company_id: str) -> list[Patient]:
        """Return all patients linked to the given company."""
        return list(
            Patient.select()
            .where(Patient.company_id == company_id)
            .order_by(Patient.last_name, Patient.first_name)
        )

    @classmethod
    def assign_account(cls, patient_id: str, account_id: str | None) -> Patient:
        """Assign (or remove) an account from a patient."""
        patient = cls.get_patient(patient_id)
        if account_id:
            account = Account.get_or_none(Account.id == account_id)
            if account is None:
                raise NotFoundException(f"Account '{account_id}' not found")
            patient.billing_account = account
        else:
            patient.billing_account = None
        patient.save()
        return patient

    @classmethod
    def assign_company(cls, patient_id: str, company_id: str | None) -> Patient:
        """Assign (or remove) a company from a patient."""
        patient = cls.get_patient(patient_id)
        patient.company_id = company_id
        patient.save()
        return patient

    @classmethod
    def create_patient(cls, dto: SavePatientDTO) -> Patient:
        cls._validate(dto)
        patient = Patient()
        patient.patient_number = cls._generate_patient_number()
        patient.qr_token = cls._generate_qr_token()
        cls._apply_dto(patient, dto)
        patient.save()
        return patient

    @classmethod
    def update_patient(cls, patient_id: str, dto: SavePatientDTO) -> Patient:
        cls._validate(dto)
        patient = cls.get_patient(patient_id)
        cls._apply_dto(patient, dto)
        patient.save()
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
        if dto.account_id:
            account = Account.get_or_none(Account.id == dto.account_id)
            patient.billing_account = account
        else:
            patient.billing_account = None

    @classmethod
    def _generate_patient_number(cls) -> str:
        """Generate a unique patient number in the format PAT-XXXXXXXX."""
        while True:
            number = f"PAT-{uuid.uuid4().hex[:8].upper()}"
            if not Patient.get_or_none(Patient.patient_number == number):
                return number

    @classmethod
    def _generate_qr_token(cls) -> str:
        """Generate a unique 12-character QR token (uppercase hex)."""
        while True:
            token = uuid.uuid4().hex[:12].upper()
            if not Patient.get_or_none(Patient.qr_token == token):
                return token

    @classmethod
    def delete_patient(cls, patient_id: str, reason: str, deleted_by: str | None = None) -> None:
        """Permanently delete a patient record and write an audit log entry.

        Args:
            patient_id: UUID of the patient to delete.
            reason: Mandatory reason for the deletion (stored in the audit log).
            deleted_by: Display name of the operator performing the deletion.

        Raises:
            BadRequestException: If *reason* is empty.
            NotFoundException: If the patient does not exist.
        """
        if not reason or not reason.strip():
            raise BadRequestException("A deletion reason is required.")
        patient = Patient.get_or_none(Patient.id == patient_id)
        if patient is None:
            raise NotFoundException(f"Patient '{patient_id}' not found")
        # Write audit log before deleting so the record is preserved.
        from gws_care.patient.patient_deletion_log import PatientDeletionLog
        log = PatientDeletionLog()
        log.patient_db_id = str(patient.id)
        log.patient_number = patient.patient_number
        log.patient_name = patient.get_full_name()
        log.reason = reason.strip()
        log.deleted_by = deleted_by or ""
        log.save()
        # CampaignPatient rows are CASCADE-deleted by the DB FK constraint.
        patient.delete_instance()
