import uuid
from datetime import date

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
    def search_patients(
        cls,
        name: str | None = None,
        patient_number: str | None = None,
        phone: str | None = None,
        account_id: str | None = None,
        dob_from: str | None = None,
        dob_to: str | None = None,
    ) -> list[Patient]:
        query = Patient.select()
        if patient_number:
            query = query.where(Patient.patient_number == patient_number)
        if phone:
            query = query.where(Patient.phone == phone)
        if name:
            query = query.where(
                Patient.last_name.contains(name)
                | Patient.first_name.contains(name)
            )
        if account_id:
            # Include patients directly linked to account OR linked via company
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
        return list(query.order_by(Patient.last_name, Patient.first_name))

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
    def delete_patient(cls, patient_id: str) -> None:
        """Delete a patient record. Also removes related CampaignPatient rows."""
        from gws_core import NotFoundException
        patient = Patient.get_or_none(Patient.id == patient_id)
        if patient is None:
            raise NotFoundException(f"Patient '{patient_id}' not found")
        # CampaignPatient rows are CASCADE-deleted by the DB FK constraint.
        patient.delete_instance()
