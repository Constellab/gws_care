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
_DOCTOR_REQUIRED_COLS = {"last_name", "first_name"}
_ACCOUNT_INDIVIDUAL_REQUIRED_COLS = {"contact_last_name", "contact_first_name"}
_EXAM_TYPE_REQUIRED_COLS = {"exam_type", "category"}
_VALID_VALUE_TYPES = {"NUMERIC", "TEXT", "BOOLEAN"}
_CATEGORY_NORM = {
    "BIOLOGY": "BIOLOGY", "BIOLOGIE": "BIOLOGY", "BIOCHIMIE": "BIOLOGY",
    "HEMATOLOGIE": "BIOLOGY", "HÉMATOLOGIE": "BIOLOGY",
    "URINE": "URINE",
    "CLINICAL": "CLINICAL", "CLINIQUE": "CLINICAL",
    "IMAGING": "IMAGING", "IMAGERIE": "IMAGING",
    "ECG": "ECG",
    "ORL": "ORL",
    "OTHER": "OTHER", "AUTRE": "OTHER",
}


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
        from gws_care.patient.patient_account import PatientAccount
        from gws_care.patient.patient_dto import SavePatientDTO
        from gws_care.patient.patient_service import PatientService

        dto = SavePatientDTO(
            last_name=row_data.get("last_name", "").strip(),
            first_name=row_data.get("first_name", "").strip(),
            birth_name=row_data.get("birth_name", "").strip() or None,
            date_of_birth=date.fromisoformat(row_data["date_of_birth"].strip()),
            gender=row_data.get("gender", "").strip(),
            address=row_data.get("address", "").strip() or None,
            address_complement=row_data.get("address_complement", "").strip() or None,
            postal_code=row_data.get("postal_code", "").strip() or None,
            city=row_data.get("city", "").strip() or None,
            country=row_data.get("country", "").strip() or None,
            phone=row_data.get("phone", "").strip() or None,
            email=row_data.get("email", "").strip() or None,
            social_security_number=row_data.get("social_security_number", "").strip() or None,
            primary_physician_name=row_data.get("primary_physician_name", "").strip() or None,
            primary_physician_phone=row_data.get("primary_physician_phone", "").strip() or None,
        )
        patient = PatientService.create_patient(dto)

        account_name = (row_data.get("account_name") or "").strip()
        if account_name:
            account = Account.get_or_none(Account.name == account_name)
            if account is not None:
                link = PatientAccount()
                link.patient = patient.id
                link.account = account.id
                link.save()

    @classmethod
    def parse_doctors_csv(cls, content: str) -> CsvParseResult:
        """Parse and validate a medical doctor CSV string.

        :param content: Raw CSV text (UTF-8, may include BOM)
        :return: CsvParseResult with validated row list or a parse_error string
        :rtype: CsvParseResult
        """
        result = CsvParseResult()
        try:
            reader = csv.DictReader(io.StringIO(content.lstrip("﻿")))
            rows = list(reader)
        except Exception as exc:
            result.parse_error = f"CSV read error: {exc}"
            return result

        if not rows:
            result.parse_error = "The CSV file is empty or has no data rows."
            return result

        missing = _DOCTOR_REQUIRED_COLS - set(rows[0].keys())
        if missing:
            result.parse_error = f"Missing required columns: {', '.join(sorted(missing))}"
            return result

        for i, row in enumerate(rows, 1):
            result.rows.append(cls._validate_doctor_row(i, row))

        return result

    @classmethod
    def _validate_doctor_row(cls, row_num: int, row: dict) -> RowValidationResult:
        errors: list[str] = []

        if not row.get("last_name", "").strip():
            errors.append("last_name required")
        if not row.get("first_name", "").strip():
            errors.append("first_name required")

        return RowValidationResult(
            row_num=row_num,
            row_data=row,
            is_valid=not errors,
            errors=errors,
        )

    @classmethod
    def import_doctor_row(cls, row_data: dict) -> None:
        """Create one medical doctor record from a validated CSV row dict.

        Must be called inside a gws_core auth context. Skips if a doctor with
        the same last_name + first_name already exists.

        :param row_data: A single dict from the CSV DictReader
        :type row_data: dict
        """
        from gws_care.doctor.medical_doctor import MedicalDoctor
        from gws_care.doctor.medical_doctor_dto import SaveMedicalDoctorDTO
        from gws_care.doctor.medical_doctor_service import MedicalDoctorService

        last_name = row_data.get("last_name", "").strip()
        first_name = row_data.get("first_name", "").strip()

        existing = MedicalDoctor.get_or_none(
            (MedicalDoctor.last_name == last_name) & (MedicalDoctor.first_name == first_name)
        )
        if existing is not None:
            return

        dto = SaveMedicalDoctorDTO(
            first_name=first_name,
            last_name=last_name,
            specialization=row_data.get("specialization", "").strip() or None,
            phone=row_data.get("phone", "").strip() or None,
            email=row_data.get("email", "").strip() or None,
            rpps_number=row_data.get("rpps_number", "").strip() or None,
        )
        MedicalDoctorService.create_doctor(dto)

    @classmethod
    def parse_accounts_individual_csv(cls, content: str) -> CsvParseResult:
        """Parse and validate an individual account CSV string.

        :param content: Raw CSV text (UTF-8, may include BOM)
        :return: CsvParseResult with validated row list or a parse_error string
        :rtype: CsvParseResult
        """
        result = CsvParseResult()
        try:
            reader = csv.DictReader(io.StringIO(content.lstrip("﻿")))
            rows = list(reader)
        except Exception as exc:
            result.parse_error = f"CSV read error: {exc}"
            return result

        if not rows:
            result.parse_error = "The CSV file is empty or has no data rows."
            return result

        missing = _ACCOUNT_INDIVIDUAL_REQUIRED_COLS - set(rows[0].keys())
        if missing:
            result.parse_error = f"Missing required columns: {', '.join(sorted(missing))}"
            return result

        for i, row in enumerate(rows, 1):
            result.rows.append(cls._validate_account_individual_row(i, row))

        return result

    @classmethod
    def _validate_account_individual_row(cls, row_num: int, row: dict) -> RowValidationResult:
        errors: list[str] = []

        if not row.get("contact_last_name", "").strip():
            errors.append("contact_last_name required")
        if not row.get("contact_first_name", "").strip():
            errors.append("contact_first_name required")

        return RowValidationResult(
            row_num=row_num,
            row_data=row,
            is_valid=not errors,
            errors=errors,
        )

    @classmethod
    def import_individual_account_row(cls, row_data: dict) -> None:
        """Create one individual account record from a validated CSV row dict.

        Must be called inside a gws_core auth context.

        :param row_data: A single dict from the CSV DictReader
        :type row_data: dict
        """
        from gws_care.account.account import Account
        from gws_care.account.account_dto import SaveAccountDTO
        from gws_care.account.account_service import AccountService

        last_name = row_data.get("contact_last_name", "").strip()
        first_name = row_data.get("contact_first_name", "").strip()
        name = f"{last_name} {first_name}".strip()

        if (
            Account.get_or_none(
                (Account.contact_last_name == last_name)
                & (Account.contact_first_name == first_name)
            )
            is not None
        ):
            return

        dto = SaveAccountDTO(
            account_type="INDIVIDUAL",
            name=name,
            contact_last_name=last_name,
            contact_first_name=first_name,
            address=row_data.get("address", "").strip() or None,
            postal_code=row_data.get("postal_code", "").strip() or None,
            city=row_data.get("city", "").strip() or None,
            phone=row_data.get("phone", "").strip() or None,
            email=row_data.get("email", "").strip() or None,
        )
        AccountService.create_account(dto)

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
            contact_first_name=row_data.get("contact_first_name", "").strip() or None,
            contact_last_name=row_data.get("contact_last_name", "").strip() or None,
            contact_name=row_data.get("contact_name", "").strip() or None,
            phone=row_data.get("phone", "").strip() or None,
            email=row_data.get("email", "").strip() or None,
        )
        AccountService.create_account(dto)

    # ── Exam type referential ─────────────────────────────────────────────────

    @classmethod
    def parse_exam_types_csv(cls, content: str) -> "CsvParseResult":
        """Parse and validate an exam type referential CSV string."""
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

        missing = _EXAM_TYPE_REQUIRED_COLS - set(rows[0].keys())
        if missing:
            result.parse_error = f"Missing required columns: {', '.join(sorted(missing))}"
            return result

        for i, row in enumerate(rows, 1):
            result.rows.append(cls._validate_exam_type_row(i, row))

        return result

    @classmethod
    def _validate_exam_type_row(cls, row_num: int, row: dict) -> "RowValidationResult":
        errors: list[str] = []

        if not row.get("exam_type", "").strip():
            errors.append("exam_type required")
        if not row.get("category", "").strip():
            errors.append("category required")

        val_type = row.get("value_type", "").strip().upper() or "NUMERIC"
        if val_type and val_type not in _VALID_VALUE_TYPES:
            errors.append(f"value_type invalid '{val_type}' (NUMERIC/TEXT/BOOLEAN)")

        age_gender = row.get("age_gender", "").strip().upper()
        if age_gender and age_gender not in ("ALL", "M", "F"):
            errors.append("age_gender must be ALL, M or F")

        return RowValidationResult(
            row_num=row_num, row_data=row, is_valid=not errors, errors=errors
        )

    @classmethod
    def import_exam_type_row(cls, row_data: dict) -> None:
        """Create or update one exam type + optional parameter from a validated row.

        Gets or creates the exam type by name, then creates the parameter if it does
        not exist. If age_min, age_max, or age_gender are set the row is treated as an
        age-range row: the parameter is found-or-created and an ExamParameterAgeRange
        record is appended (idempotent on age_min+age_max+age_gender).
        Must be called inside a gws_core auth context.
        """
        from gws_care.exam_type_ref.exam_parameter import ExamParameter
        from gws_care.exam_type_ref.exam_type_ref import ExamTypeRef
        from gws_care.exam_type_ref.exam_type_ref_dto import (
            SaveExamParameterDTO,
            SaveExamTypeRefDTO,
        )
        from gws_care.exam_type_ref.exam_type_ref_service import ExamTypeRefService

        def _f(key: str) -> "float | None":
            v = row_data.get(key, "").strip()
            try:
                return float(v) if v else None
            except ValueError:
                return None

        def _s(key: str) -> "str | None":
            v = row_data.get(key, "").strip()
            return v or None

        def _i(key: str) -> "int | None":
            v = row_data.get(key, "").strip()
            try:
                return int(v) if v else None
            except ValueError:
                return None

        name = row_data["exam_type"].strip()
        raw_cat = row_data.get("category", "").strip().upper()
        category = _CATEGORY_NORM.get(raw_cat, "OTHER")

        existing_ref = ExamTypeRef.get_or_none(ExamTypeRef.name == name)
        if existing_ref is None:
            ref_dto = ExamTypeRefService.create(
                SaveExamTypeRefDTO(
                    name=name,
                    category=category,
                    department=_s("department"),
                    description=_s("description"),
                    is_active=True,
                    allows_attachment=True,
                    requires_attachment=False,
                )
            )
            ref_id = ref_dto.id
        else:
            ref_id = str(existing_ref.id)

        param_name = row_data.get("parameter", "").strip()
        if not param_name:
            return

        age_min = _i("age_min")
        age_max = _i("age_max")
        age_gender_raw = row_data.get("age_gender", "").strip().upper()
        is_age_range_row = age_min is not None or age_max is not None or bool(age_gender_raw)
        age_gender = age_gender_raw or "ALL"

        existing_param = ExamParameter.get_or_none(
            (ExamParameter.exam_type_ref == ref_id) & (ExamParameter.name == param_name)
        )

        if existing_param is None:
            val_type = row_data.get("value_type", "").strip().upper() or "NUMERIC"
            is_computed = row_data.get("is_computed", "").strip().lower() in ("true", "1", "yes")
            param_dto = ExamTypeRefService.add_parameter(
                ref_id,
                SaveExamParameterDTO(
                    name=param_name,
                    value_type=val_type,
                    unit=_s("unit"),
                    ref_low=_f("ref_low") if not is_age_range_row else None,
                    ref_high=_f("ref_high") if not is_age_range_row else None,
                    critical_low=_f("critical_low") if not is_age_range_row else None,
                    critical_high=_f("critical_high") if not is_age_range_row else None,
                    ref_low_m=_f("ref_low_m"),
                    ref_high_m=_f("ref_high_m"),
                    critical_low_m=_f("critical_low_m"),
                    critical_high_m=_f("critical_high_m"),
                    ref_low_f=_f("ref_low_f"),
                    ref_high_f=_f("ref_high_f"),
                    critical_low_f=_f("critical_low_f"),
                    critical_high_f=_f("critical_high_f"),
                    label_normal=_s("label_normal"),
                    label_low=_s("label_low"),
                    label_high=_s("label_high"),
                    label_critical_low=_s("label_critical_low"),
                    label_critical_high=_s("label_critical_high"),
                    code=_s("code"),
                    is_computed=is_computed,
                    formula=_s("formula"),
                    is_required=False,
                    display_order=0,
                ),
            )
            param_id = param_dto.id
        elif not is_age_range_row:
            return
        else:
            param_id = str(existing_param.id)

        if not is_age_range_row:
            return

        from gws_care.exam_type_ref.exam_param_age_range import ExamParameterAgeRange

        already = ExamParameterAgeRange.get_or_none(
            (ExamParameterAgeRange.exam_parameter == param_id)
            & (ExamParameterAgeRange.age_min == age_min)
            & (ExamParameterAgeRange.age_max == age_max)
            & (ExamParameterAgeRange.gender == age_gender)
        )
        if already is not None:
            return

        ExamParameterAgeRange.create(
            exam_parameter=param_id,
            age_min=age_min,
            age_max=age_max,
            gender=age_gender,
            ref_low=_f("ref_low"),
            ref_high=_f("ref_high"),
            critical_low=_f("critical_low"),
            critical_high=_f("critical_high"),
            label_normal=_s("label_normal"),
            label_low=_s("label_low"),
            label_high=_s("label_high"),
            label_critical_low=_s("label_critical_low"),
            label_critical_high=_s("label_critical_high"),
        )
