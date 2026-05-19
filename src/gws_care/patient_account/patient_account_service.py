"""Service layer for PatientAccount (patient-account affiliation)."""

from datetime import date

from gws_care.account.account import Account
from gws_care.patient.patient import Patient
from gws_care.patient_account.patient_account import PatientAccount, PatientAccountStatus
from gws_care.patient_account.patient_account_dto import PatientAccountDTO, SavePatientAccountDTO


class PatientAccountService:
    """CRUD operations for patient-account affiliations."""

    @classmethod
    def list_for_patient(cls, patient_id: str) -> list[PatientAccountDTO]:
        rows = (
            PatientAccount.select(PatientAccount, Patient, Account)
            .join(Patient)
            .switch(PatientAccount)
            .join(Account)
            .where(PatientAccount.patient == patient_id)
            .order_by(PatientAccount.start_date.desc())
        )
        return [cls._to_dto(r) for r in rows]

    @classmethod
    def list_for_account(cls, account_id: str) -> list[PatientAccountDTO]:
        rows = (
            PatientAccount.select(PatientAccount, Patient, Account)
            .join(Patient)
            .switch(PatientAccount)
            .join(Account)
            .where(PatientAccount.account == account_id)
            .order_by(PatientAccount.start_date.desc())
        )
        return [cls._to_dto(r) for r in rows]

    @classmethod
    def list_active_patients_for_account(cls, account_id: str) -> list["PatientAccount"]:
        return list(
            PatientAccount.select()
            .where(
                (PatientAccount.account == account_id)
                & (PatientAccount.status == PatientAccountStatus.ACTIVE.value)
            )
        )

    @classmethod
    def create_affiliation(cls, dto: SavePatientAccountDTO) -> PatientAccountDTO:
        patient = Patient.get_by_id_and_check(dto.patient_id)
        account = Account.get_by_id_and_check(dto.account_id)
        pa = PatientAccount()
        pa.patient = patient
        pa.account = account
        pa.status = dto.status
        pa.start_date = dto.start_date
        pa.end_date = dto.end_date
        pa.employee_number = dto.employee_number
        pa.position = dto.position
        pa.site = dto.site
        pa.department = dto.department
        pa.end_reason = dto.end_reason
        pa.save()
        return cls._to_dto(pa)

    @classmethod
    def update_affiliation(cls, affiliation_id: str, dto: SavePatientAccountDTO) -> PatientAccountDTO:
        pa = PatientAccount.get_by_id_and_check(affiliation_id)
        pa.status = dto.status
        pa.start_date = dto.start_date
        pa.end_date = dto.end_date
        pa.employee_number = dto.employee_number
        pa.position = dto.position
        pa.site = dto.site
        pa.department = dto.department
        pa.end_reason = dto.end_reason
        pa.save()
        return cls._to_dto(pa)

    @classmethod
    def close_affiliation(cls, affiliation_id: str, end_date: date, reason: str | None = None) -> PatientAccountDTO:
        pa = PatientAccount.get_by_id_and_check(affiliation_id)
        pa.status = PatientAccountStatus.FORMER.value
        pa.end_date = end_date
        if reason:
            pa.end_reason = reason
        pa.save()
        return cls._to_dto(pa)

    @classmethod
    def is_patient_affiliated_to_account(cls, patient_id: str, account_id: str) -> bool:
        return PatientAccount.select().where(
            (PatientAccount.patient == patient_id)
            & (PatientAccount.account == account_id)
            & (PatientAccount.status == PatientAccountStatus.ACTIVE.value)
        ).exists()

    @classmethod
    def _to_dto(cls, pa: "PatientAccount") -> PatientAccountDTO:
        try:
            status_enum = PatientAccountStatus(pa.status)
        except ValueError:
            status_enum = PatientAccountStatus.ACTIVE
        return PatientAccountDTO(
            id=str(pa.id),
            patient_id=str(pa.patient_id),
            patient_name=pa.patient.get_full_name() if pa.patient_id else "",
            patient_number=pa.patient.patient_number if pa.patient_id else "",
            account_id=str(pa.account_id),
            account_name=pa.account.name if pa.account_id else "",
            status=pa.status,
            status_label=status_enum.get_label(),
            status_color=status_enum.get_color(),
            start_date=pa.start_date.isoformat() if pa.start_date else None,
            end_date=pa.end_date.isoformat() if pa.end_date else None,
            employee_number=pa.employee_number,
            position=pa.position,
            site=pa.site,
            department=pa.department,
            end_reason=pa.end_reason,
        )
