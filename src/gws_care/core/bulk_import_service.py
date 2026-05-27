"""Pure-logic helpers for bulk CSV import of patients and accounts.

This module is intentionally dependency-free (no Reflex, no DB imports at
module level) so it can be imported and unit-tested in the standard gws
test environment.
"""

import csv
import io
from dataclasses import dataclass, field
from datetime import date


@dataclass
class RowValidationResult:
    """Outcome of validating one CSV row before DB insertion."""

    row_num: int
    row_data: dict
    is_valid: bool
    errors: list[str] = field(default_factory=list)


@dataclass
class CsvParseResult:
    """Outcome of parsing and validating a full CSV file."""

    rows: list[RowValidationResult] = field(default_factory=list)
    parse_error: str = ""

    @property
    def valid_rows(self) -> list[RowValidationResult]:
        return [r for r in self.rows if r.is_valid]

    @property
    def invalid_rows(self) -> list[RowValidationResult]:
        return [r for r in self.rows if not r.is_valid]


_PATIENT_REQUIRED_COLS = {"last_name", "first_name", "date_of_birth", "gender"}
_VALID_GENDERS = {"M", "F", "Other"}


class BulkImportService:
    """Service for parsing, validating and writing bulk CSV imports."""

    # ── CSV parsing ───────────────────────────────────────────────────────────

    @classmethod
    def parse_patients_csv(cls, content: str) -> CsvParseResult:
        """Parse and validate a patient CSV string.

        :param content: Raw CSV text (UTF-8, may include BOM)
        :return: CsvParseResult with validated row list or a parse_error string
        :rtype: CsvParseResult
        """
        result = CsvParseResult()
        try:
            # Strip Excel BOM
            reader = csv.DictReader(io.StringIO(content.lstrip("\ufeff")))
            rows = list(reader)
        except Exception as exc:
            result.parse_error = f"CSV read error: {exc}"
            return result

        if not rows:
            result.parse_error = "The CSV file is empty or has no data rows."
            return result

        missing = _PATIENT_REQUIRED_COLS - set(rows[0].keys())
        if missing:
            result.parse_error = f"Missing required columns: {', '.join(sorted(missing))}"
            return result

        for i, row in enumerate(rows, 1):
            result.rows.append(cls._validate_patient_row(i, row))

        return result

    @classmethod
    def parse_accounts_csv(cls, content: str) -> CsvParseResult:
        """Parse and validate an account CSV string.

        :param content: Raw CSV text (UTF-8, may include BOM)
        :return: CsvParseResult with validated row list or a parse_error string
        :rtype: CsvParseResult
        """
        result = CsvParseResult()
        try:
            reader = csv.DictReader(io.StringIO(content.lstrip("\ufeff")))
            rows = list(reader)
        except Exception as exc:
            result.parse_error = f"CSV read error: {exc}"
            return result

        if not rows:
            result.parse_error = "The CSV file is empty or has no data rows."
            return result

        if "name" not in rows[0].keys():
            result.parse_error = "Missing required column: 'name'"
            return result

        for i, row in enumerate(rows, 1):
            result.rows.append(cls._validate_account_row(i, row))

        return result

    # ── Row validators ────────────────────────────────────────────────────────

    @classmethod
    def _validate_patient_row(cls, row_num: int, row: dict) -> RowValidationResult:
        errors: list[str] = []

        if not row.get("last_name", "").strip():
            errors.append("last_name required")
        if not row.get("first_name", "").strip():
            errors.append("first_name required")

        dob_str = row.get("date_of_birth", "").strip()
        if not dob_str:
            errors.append("date_of_birth required")
        else:
            try:
                date.fromisoformat(dob_str)
            except ValueError:
                errors.append("date_of_birth must be YYYY-MM-DD")

        gender = row.get("gender", "").strip()
        if gender not in _VALID_GENDERS:
            errors.append("gender must be M, F or Other")

        weight_str = row.get("weight", "").strip()
        if weight_str:
            try:
                float(weight_str)
            except ValueError:
                errors.append("weight must be a number (kg)")

        height_str = row.get("height", "").strip()
        if height_str:
            try:
                float(height_str)
            except ValueError:
                errors.append("height must be a number (cm)")

        return RowValidationResult(
            row_num=row_num,
            row_data=row,
            is_valid=not errors,
            errors=errors,
        )

    @classmethod
    def _validate_account_row(cls, row_num: int, row: dict) -> RowValidationResult:
        errors: list[str] = []

        if not row.get("name", "").strip():
            errors.append("name required")

        return RowValidationResult(
            row_num=row_num,
            row_data=row,
            is_valid=not errors,
            errors=errors,
        )

    # ── DB writers ────────────────────────────────────────────────────────────

    @classmethod
    def import_patient_row(cls, row_data: dict) -> None:
        """Create one patient record from a validated CSV row dict.

        Must be called inside a gws_core auth context.

        :param row_data: A single dict from the CSV DictReader
        :type row_data: dict
        """
        from gws_care.account.account import Account
        from gws_care.patient.patient_dto import SavePatientDTO
        from gws_care.patient.patient_service import PatientService

        account_id: str | None = None
        account_name = (row_data.get("account_name") or "").strip()
        if account_name:
            account = Account.get_or_none(Account.name == account_name)
            if account is not None:
                account_id = str(account.id)

        def _parse_float(key: str):
            v = row_data.get(key, "").strip()
            return float(v) if v else None

        dto = SavePatientDTO(
            last_name=row_data.get("last_name", "").strip(),
            first_name=row_data.get("first_name", "").strip(),
            birth_name=row_data.get("birth_name", "").strip() or None,
            date_of_birth=date.fromisoformat(row_data["date_of_birth"].strip()),
            gender=row_data.get("gender", "").strip(),
            address=row_data.get("address", "").strip() or None,
            postal_code=row_data.get("postal_code", "").strip() or None,
            city=row_data.get("city", "").strip() or None,
            phone=row_data.get("phone", "").strip() or None,
            email=row_data.get("email", "").strip() or None,
            primary_physician_name=row_data.get("primary_physician_name", "").strip() or None,
            primary_physician_phone=row_data.get("primary_physician_phone", "").strip() or None,
            account_id=account_id,
            social_security_number=row_data.get("social_security_number", "").strip() or None,
            weight=_parse_float("weight"),
            height=_parse_float("height"),
        )
        PatientService.create_patient(dto)

    @classmethod
    def import_account_row(cls, row_data: dict) -> None:
        """Create one account record from a validated CSV row dict.

        Must be called inside a gws_core auth context.

        :param row_data: A single dict from the CSV DictReader
        :type row_data: dict
        """
        from gws_care.account.account import Account
        from gws_care.account.account_dto import SaveAccountDTO
        from gws_care.account.account_service import AccountService

        name = row_data.get("name", "").strip()
        if Account.get_or_none(Account.name == name) is not None:
            return

        dto = SaveAccountDTO(
            name=name,
            registration_number=row_data.get("registration_number", "").strip() or None,
            address=row_data.get("address", "").strip() or None,
            postal_code=row_data.get("postal_code", "").strip() or None,
            city=row_data.get("city", "").strip() or None,
            phone=row_data.get("phone", "").strip() or None,
            email=row_data.get("email", "").strip() or None,
            contact_name=row_data.get("contact_name", "").strip() or None,
        )
        AccountService.create_account(dto)
